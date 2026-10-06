"""
Backfill service — manual, staleness-aware wrapper around
app/scripts/run_backfills.py.

Responsibilities
----------------
- Register each backfill source with its target table and
  identity filter (source tag and/or indicator name).
- Decide per source whether a backfill is needed, based on:
    * table empty for that source  -> bootstrap
    * max(time) behind by > cadence * 2  -> gap fill
    * force=True  -> full re-pull (idempotent)
- Invoke the underlying backfill function via run_backfill_module
  (which handles the sync/async split).
- Emit structured progress logs:
    [BACKFILL] <source> starting (range, ~N rows)
    [BACKFILL] <source> progress: N/M rows (P%)   every 1000 rows
    [BACKFILL] <source> completed: N rows in T s
    [BACKFILL] <source> failed at row N (time): <error>
- Track a process-wide status (idle|running|completed|failed)
  for /health visibility.

Scope (Phase A, Chat 2)
-----------------------
- Manual trigger only. No scheduler, no startup hook.
- Daily-resolution sources from run_backfills.py.
- run_backfills.py is not modified; its functions are called
  through run_backfill_module.

Not in scope (Phase B)
----------------------
- Hourly backfill (hourly_backfill_service.py).
- Hourly materializers (btc_prices_hourly, macro_indicators_hourly).
- features_db writer and hourly parquet.

Cadence semantics
-----------------
cadence is the expected interval between new rows *from this
specific writer*. It is used only by check_and_backfill to skip
pointless re-runs when a human invokes the CLI. Nothing fires on
a timer.

cadence=None means "never consider this source stale". Used for
frozen historical archives. On an empty DB the bootstrap path
still runs them once. On a populated DB they are skipped unless
force=True.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import text

from app.database.session import SessionLocal, engine
from app.scripts.run_backfills import (
    backfill_active_addresses,
    backfill_btc_dominance,
    backfill_btc_prices,
    backfill_equity_correlation,
    backfill_fred_indicators,
    backfill_gold_spot_perth,
    backfill_gold_spot_yahoo,
    backfill_high_yield_spread,
    run_backfill_module,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

# Indicators written by backfill_fred_indicators via IndicatorService.
# IndicatorService.parse_observations always writes source='fred'.
#
# high_yield_spread is included here even though it also has a
# dedicated CSV seed (see HIGH_YIELD_ARCHIVE below). The FRED-list
# staleness query filters by source='fred', so the CSV seed's rows
# (source='fred_archive_backfill') never interfere with this check.
FRED_INDICATOR_NAMES: tuple[str, ...] = (
    "cpi",
    "federal_funds_rate",
    "m2_money_supply",
    "dxy",
    "vix",
    "ten_year_treasury",
    "gdp",
    "unemployment",
    "high_yield_spread",
    "nasdaq_composite",
)


# ============================================================
# SOURCE REGISTRY
# ============================================================


@dataclass(frozen=True)
class BackfillSource:
    """
    One backfill source: a function plus the identity of the rows
    it writes, so its freshness can be queried in isolation.

    Attributes
    ----------
    key:
        Stable identifier used in logs and status.
    function:
        Callable from run_backfills.py. May be sync or async.
    table:
        Target raw table.
    filter_sql:
        SQL fragment appended to WHERE, identifying this source's
        rows. Must use only literals (no user input).
    indicator_names:
        Optional tuple of indicator_name values, when the filter
        spans several indicators (FRED group).
    cadence:
        Expected interval between new rows. None = frozen archive.
    estimate_per_day:
        Approximate rows per day from this source, for the "~N rows"
        progress estimate. 1 for daily sources.
    """

    key: str
    function: Callable[[], Any]
    table: str
    filter_sql: str
    cadence: Optional[timedelta]
    estimate_per_day: float = 1.0
    indicator_names: tuple[str, ...] = field(default_factory=tuple)


BACKFILL_SOURCES: tuple[BackfillSource, ...] = (
    # ------------------------------------------------------------
    # BTC prices (daily klines, source='binance_backfill')
    # ------------------------------------------------------------
    BackfillSource(
        key="btc_prices",
        function=backfill_btc_prices,
        table="btc_prices",
        filter_sql="source = 'binance_backfill'",
        cadence=timedelta(hours=24),
        estimate_per_day=1.0,
    ),
    # ------------------------------------------------------------
    # BTC dominance (BGeometrics CSV, source='bgeometrics_backfill')
    # ------------------------------------------------------------
    BackfillSource(
        key="btc_dominance",
        function=backfill_btc_dominance,
        table="btc_dominance",
        filter_sql="source = 'bgeometrics_backfill'",
        cadence=timedelta(hours=24),
        estimate_per_day=1.0,
    ),
    # ------------------------------------------------------------
    # Gold spot — Perth Mint
    #
    # Static CSV archive, 2017-08-17 -> 2021-09-13. Never updated.
    # cadence=None: never stale. Bootstraps on empty DB, otherwise
    # skipped unless force=True.
    # ------------------------------------------------------------
    BackfillSource(
        key="gold_spot_perth",
        function=backfill_gold_spot_perth,
        table="macro_indicators",
        filter_sql=(
            "indicator_name = 'gold_spot' "
            "AND source = 'perth_mint_backfill'"
        ),
        cadence=None,
        estimate_per_day=1.0,
    ),
    # ------------------------------------------------------------
    # Gold spot — Yahoo (daily)
    # ------------------------------------------------------------
    BackfillSource(
        key="gold_spot_yahoo",
        function=backfill_gold_spot_yahoo,
        table="macro_indicators",
        filter_sql=(
            "indicator_name = 'gold_spot' "
            "AND source = 'yahoo_finance'"
        ),
        cadence=timedelta(hours=24),
        estimate_per_day=1.0,
    ),
    # ------------------------------------------------------------
    # FRED indicators (10 series, source='fred')
    #
    # Excludes the CSV archive path; that is a separate source below.
    # ------------------------------------------------------------
    BackfillSource(
        key="fred_indicators",
        function=backfill_fred_indicators,
        table="macro_indicators",
        filter_sql=(
            "source = 'fred' AND indicator_name IN ("
            + ", ".join(f"'{name}'" for name in FRED_INDICATOR_NAMES)
            + ")"
        ),
        cadence=timedelta(hours=24),
        estimate_per_day=1.0,
        indicator_names=FRED_INDICATOR_NAMES,
    ),
    # ------------------------------------------------------------
    # High-yield spread — CSV archive
    #
    # Frozen historical FRED snapshot: BAMLH0A0HYM2.csv covers
    # 1996-12-31 -> 2021-03-19. Never receives new rows. The live
    # series is kept current by fred_indicators (source='fred').
    #
    # cadence=None: bootstrap-only. On a fresh DB it seeds the
    # pre-2021 history. On a populated DB it is skipped unless
    # force=True.
    # ------------------------------------------------------------
    BackfillSource(
        key="high_yield_spread_archive",
        function=backfill_high_yield_spread,
        table="macro_indicators",
        filter_sql=(
            "indicator_name = 'high_yield_spread' "
            "AND source = 'fred_archive_backfill'"
        ),
        cadence=None,
        estimate_per_day=1.0,
    ),
    # ------------------------------------------------------------
    # Active addresses (source='blockchain.com')
    # ------------------------------------------------------------
    BackfillSource(
        key="active_addresses",
        function=backfill_active_addresses,
        table="macro_indicators",
        filter_sql=(
            "indicator_name = 'active_addresses' "
            "AND source = 'blockchain.com'"
        ),
        cadence=timedelta(hours=24),
        estimate_per_day=1.0,
    ),
    # ------------------------------------------------------------
    # Equity correlation (derived, source='derived')
    # ------------------------------------------------------------
    BackfillSource(
        key="equity_corr",
        function=backfill_equity_correlation,
        table="macro_indicators",
        filter_sql=(
            "indicator_name = 'equity_corr' "
            "AND source = 'derived'"
        ),
        cadence=timedelta(hours=24),
        estimate_per_day=1.0,
    ),
)


# ============================================================
# STATUS SINGLETON
# ============================================================


@dataclass
class BackfillStatus:
    state: str = "idle"           # idle | running | completed | failed
    current_source: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    sources_run: int = 0
    sources_skipped: int = 0


_status = BackfillStatus()
_status_lock = asyncio.Lock()
_run_lock = asyncio.Lock()


def get_backfill_status() -> BackfillStatus:
    """
    Return a snapshot of the current backfill status.

    Read by /health. Never blocks; returns the current field values
    without copying, since the dataclass is small and read-mostly.
    """
    return _status


def _reset_status_for_run() -> None:
    _status.state = "running"
    _status.current_source = None
    _status.error = None
    _status.started_at = datetime.now(timezone.utc)
    _status.completed_at = None
    _status.sources_run = 0
    _status.sources_skipped = 0


def _set_status_failed(source_key: str, error: str) -> None:
    _status.state = "failed"
    _status.current_source = source_key
    _status.error = error
    _status.completed_at = datetime.now(timezone.utc)


def _set_status_completed() -> None:
    _status.state = "completed"
    _status.current_source = None
    _status.error = None
    _status.completed_at = datetime.now(timezone.utc)


# ============================================================
# STALENESS QUERY
# ============================================================


def _query_max_time(source: BackfillSource) -> Optional[datetime]:
    """
    Return max(time) for this source's rows, or None if empty.

    Uses a 30-day bounded window to avoid a full hypertable scan
    on btc_prices, which also contains live tick rows. The window
    is far wider than any cadence we check, so it cannot produce a
    false "current" answer.
    """
    sql = text(
        f"""
        SELECT max(time) AS max_time
        FROM {source.table}
        WHERE time >= now() - interval '30 days'
          AND {source.filter_sql}
        """
    )

    session = SessionLocal()
    try:
        row = session.execute(sql).first()
        return row.max_time if row and row.max_time else None
    finally:
        session.close()


def _is_stale(source: BackfillSource, max_time: Optional[datetime]) -> bool:
    """
    Decide whether a source needs a backfill.

    Returns True if:
      - the table has no rows for this source (bootstrap), OR
      - the source has a cadence and max_time is behind by
        more than cadence * 2.

    Returns False if the source is a frozen archive (cadence=None)
    and rows already exist.
    """
    if max_time is None:
        return True

    if source.cadence is None:
        return False

    now = datetime.now(timezone.utc)
    age = now - max_time
    return age > source.cadence * 2


# ============================================================
# PROGRESS POLLER
# ============================================================


async def _count_rows_since(
    source: BackfillSource,
    since: datetime,
) -> int:
    """Return the number of rows written since `since` for this source."""
    sql = text(
        f"""
        SELECT count(*) AS n
        FROM {source.table}
        WHERE time >= :since
          AND {source.filter_sql}
        """
    )
    session = SessionLocal()
    try:
        row = session.execute(sql, {"since": since}).first()
        return int(row.n) if row and row.n else 0
    finally:
        session.close()


async def _progress_poller(
    source: BackfillSource,
    since: datetime,
    stop_event: asyncio.Event,
    start_time: float,
) -> None:
    """
    Poll the target table every few seconds and log progress each
    time the row count crosses a new 1000-row boundary.

    M is an estimate based on cadence and elapsed wall time. It is
    labelled as such in the log line.
    """
    last_bucket = 0
    try:
        while not stop_event.is_set():
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=5.0)
                # stop_event was set; loop exits on next check.
                continue
            except asyncio.TimeoutError:
                pass

            try:
                n = await _count_rows_since(source, since)
            except Exception:
                logger.exception(
                    "[BACKFILL] %s progress poll failed", source.key
                )
                continue

            bucket = n // 1000
            if bucket <= last_bucket:
                continue
            last_bucket = bucket

            elapsed = max(time.monotonic() - start_time, 1e-6)
            per_sec = n / elapsed
            # Rough estimate of total rows for this source.
            # Daily sources: ~1 row per day over the covered range.
            # This is intentionally loose; the log marks it as an estimate.
            estimated_total = max(n, int(source.estimate_per_day * max(elapsed, 1)))
            pct = int(100 * n / estimated_total) if estimated_total else 0

            logger.info(
                "[BACKFILL] %s progress: %d/%d rows (%d%%, estimate)",
                source.key,
                n,
                estimated_total,
                pct,
            )
    except asyncio.CancelledError:
        raise


# ============================================================
# SOURCE EXECUTION
# ============================================================


async def _run_source(source: BackfillSource) -> int:
    """
    Run one source, with progress polling and structured logging.

    Returns the number of rows written (best effort; may be 0 if
    the writer's return value is not row-countable).
    """
    logger.info("[BACKFILL] %s starting", source.key)
    start_ts = datetime.now(timezone.utc)
    start_time = time.monotonic()

    stop_event = asyncio.Event()
    poller = asyncio.create_task(
        _progress_poller(source, start_ts, stop_event, start_time)
    )

    _status.current_source = source.key

    try:
        await run_backfill_module(source.function)
    except Exception as error:
        # Best-effort count of what landed before the failure.
        try:
            rows_before_failure = await _count_rows_since(source, start_ts)
        except Exception:
            rows_before_failure = 0

        logger.error(
            "[BACKFILL] %s failed at row %d (%s): %s",
            source.key,
            rows_before_failure,
            datetime.now(timezone.utc).isoformat(),
            error,
        )
        raise
    finally:
        stop_event.set()
        try:
            await asyncio.wait_for(poller, timeout=2.0)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            poller.cancel()

    elapsed = time.monotonic() - start_time
    rows = await _count_rows_since(source, start_ts)

    logger.info(
        "[BACKFILL] %s completed: %d rows in %.1fs",
        source.key,
        rows,
        elapsed,
    )
    return rows


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================


async def check_and_backfill(force: bool = False) -> None:
    """
    For each registered source, decide whether it needs a backfill
    and run it if so.

    force=True: run every source unconditionally (idempotent).
    force=False: bootstrap empty sources; gap-fill sources whose
                 max(time) is behind by more than cadence * 2;
                 skip frozen archives that already have rows.

    Concurrent calls are serialised: a second caller logs
    "already running" and returns immediately.
    """
    if _run_lock.locked():
        logger.info("[BACKFILL] already running, skipping")
        return

    async with _run_lock:
        _reset_status_for_run()

        logger.info(
            "[BACKFILL] starting (force=%s, sources=%d)",
            force,
            len(BACKFILL_SOURCES),
        )

        for source in BACKFILL_SOURCES:
            try:
                max_time = _query_max_time(source)
            except Exception as error:
                logger.exception(
                    "[BACKFILL] %s staleness query failed", source.key
                )
                _set_status_failed(source.key, str(error))
                return

            if force:
                reason = "forced"
            elif max_time is None:
                reason = "bootstrap (empty)"
            elif _is_stale(source, max_time):
                reason = "stale"
            else:
                _status.sources_skipped += 1
                logger.info(
                    "[BACKFILL] %s skipped (current, last=%s)",
                    source.key,
                    max_time.isoformat(),
                )
                continue

            logger.info("[BACKFILL] %s -> %s", source.key, reason)

            try:
                await _run_source(source)
                _status.sources_run += 1
            except Exception as error:
                _set_status_failed(source.key, str(error))
                logger.exception("[BACKFILL] %s aborted run", source.key)
                return

        _set_status_completed()
        logger.info(
            "[BACKFILL] completed (ran=%d, skipped=%d)",
            _status.sources_run,
            _status.sources_skipped,
        )