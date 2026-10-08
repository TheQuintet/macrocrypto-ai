"""
Raw hourly backfill service (Chat 4, C4-1).

Two sources, both written to raw tables:

  btc_hourly:
    Binance klines interval="1h" -> raw btc_prices
    source tag: "binance_backfill_hourly"
    historical floor: 2017-08-17 (Binance BTCUSDT inception)

  gold_hourly:
    Yahoo Finance interval="1h" -> raw macro_indicators
    indicator_name: "gold_spot"
    source tag: "yahoo_hourly"
    historical floor: ~730 days (Yahoo's hourly history limit)

Idempotency:
  BTC writes go through BTCPriceRepository.save_historical_prices,
  which pre-checks existing `time` values and skips duplicates.
  Gold writes go through MacroIndicatorRepository.create_many,
  which uses ON CONFLICT (time, indicator_name) DO NOTHING.

Skip-if-ticks-exist (Chat 3 §8.6, Chat 4 Decision 6):
  Before writing an hourly BTC candle for hour H, check whether
  btc_prices already has ANY row in [H, H+1h) whose source is
  NOT 'binance_backfill_hourly'. If so, skip the candle: ticks
  are strictly more informative than a 1h candle, and writing
  both would double-count volume in btc_prices_hourly.

Scheduling:
  CLI-only. See docs/data-service-hourly-runbook.md.

Return convention:
  Both backfill functions return the number of rows PERSISTED
  (post-dedupe, post-skip), not the number attempted. Running
  the same command twice shows 0 on the second run.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy import text

from app.collectors.binance import BinanceCollector
from app.collectors.yahoo_finance import YahooFinanceCollector
from app.config import settings
from app.database.btc_price_repository import BTCPriceRepository
from app.database.macro_indicator_repository import MacroIndicatorRepository
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

BINANCE_HOURLY_INTERVAL = "1h"
BINANCE_HOURLY_SOURCE = "binance_backfill_hourly"
BINANCE_HOURLY_LIMIT = 1000
BINANCE_HOURLY_FLOOR = datetime(2017, 8, 17, tzinfo=timezone.utc)

YAHOO_HOURLY_SOURCE = "yahoo_hourly"
YAHOO_HOURLY_INDICATOR = "gold_spot"
YAHOO_HOURLY_MAX_DAYS = 730  # Yahoo's hourly history limit
YAHOO_HOURLY_RANGE = "730d"
YAHOO_HOURLY_INTERVAL = "1h"

# Rate-limit backoff for Binance: max 4 retries, exponential.
BINANCE_MAX_RETRIES = 4
BINANCE_BACKOFF_BASE_SECONDS = 2.0

ONE_HOUR = timedelta(hours=1)


# ============================================================
# REGISTRY
# ============================================================
#
# Shape follows the Chat 4 addendum (dict), not the Phase A
# BackfillSource dataclass tuple. Rationale: C4-1's entries are
# hourly, target different tables, and are consumed by C4-2's
# gap detector, which needs the dict's keyed lookup.
#
# `function` is filled in at module bottom, after the functions
# are defined.

HOURLY_BACKFILL_SOURCES: dict[str, dict[str, Any]] = {
    "btc_hourly": {
        "function": None,  # wired at module bottom
        "table": "btc_prices",
        "source_tag": BINANCE_HOURLY_SOURCE,
        "native_cadence_hours": 1,
        "max_age_hours": 6,
    },
    "gold_hourly": {
        "function": None,  # wired at module bottom
        "table": "macro_indicators",
        "source_tag": YAHOO_HOURLY_SOURCE,
        "native_cadence_hours": 1,
        "max_age_hours": 6,
    },
}


# ============================================================
# HELPERS
# ============================================================


def _floor_to_hour(dt: datetime) -> datetime:
    """Return dt truncated to the start of its UTC hour."""
    return dt.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


def _last_completed_hour(now: Optional[datetime] = None) -> datetime:
    """
    Row timestamp of the last completed hour.

    At 14:35, the current hour [14:00, 15:00) is not complete.
    The last completed hour is [13:00, 14:00), whose row has
    time = 14:00.
    """
    now = now or datetime.now(timezone.utc)
    return _floor_to_hour(now)


def _resolve_hourly_range(
    start: Optional[datetime],
    end: Optional[datetime],
    days: Optional[int],
) -> tuple[datetime, datetime]:
    """
    Resolve a backfill range.

    Both bounds are floored to the hour and clamped to the last
    completed hour. `days` takes precedence over start/end.
    """
    if days is not None and (start is not None or end is not None):
        logger.warning(
            "[HOURLY-BACKFILL] both days and start/end provided; "
            "days takes precedence"
        )

    last = _last_completed_hour()

    if days is not None:
        if days <= 0:
            raise ValueError("days must be positive")
        end = last
        start = end - timedelta(days=days)
    else:
        if start is None:
            raise ValueError("either start or days is required")
        start = _floor_to_hour(start)
        end = _floor_to_hour(end) if end else last

    if end > last:
        logger.warning(
            "[HOURLY-BACKFILL] clamping end %s to last completed hour %s",
            end.isoformat(), last.isoformat(),
        )
        end = last

    if end <= start:
        raise ValueError(
            f"invalid range: start={start.isoformat()} end={end.isoformat()}"
        )

    return start, end


# ============================================================
# BTC HOURLY
# ============================================================


def _existing_raw_hours_without_tag(
    start: datetime,
    end: datetime,
    exclude_source: str,
) -> set[datetime]:
    """
    Return the set of hour boundaries in [start, end) where
    btc_prices already has at least one row whose source is NOT
    `exclude_source`.

    Batched: one query for the whole range. Used to implement
    the skip-if-ticks-exist rule (Chat 4 Decision 6).
    """
    sql = text(
        """
        SELECT DISTINCT date_trunc('hour', time) AS hour
        FROM btc_prices
        WHERE time >= :start AND time < :end
          AND source != :exclude
        """
    )
    session = SessionLocal()
    try:
        rows = session.execute(
            sql, {"start": start, "end": end, "exclude": exclude_source}
        ).all()
        return {_floor_to_hour(r[0]) for r in rows}
    finally:
        session.close()


async def _fetch_btc_klines_paginated(
    collector: BinanceCollector,
    start: datetime,
    end: datetime,
) -> list[dict]:
    """
    Walk Binance klines forward in 1000-candle pages.

    Assumes BinanceCollector.get_klines does not paginate
    internally (or that if it does, redundant pages are
    harmless). Retries with exponential backoff on 429/418.
    """
    all_candles: list[dict] = []
    cursor = start
    end_ms = int(end.timestamp() * 1000)

    while cursor < end:
        cursor_ms = int(cursor.timestamp() * 1000)

        last_error: Optional[Exception] = None
        for attempt in range(BINANCE_MAX_RETRIES):
            try:
                candles = await collector.get_klines(
                    symbol=settings.BINANCE_DEFAULT_SYMBOL,
                    interval=BINANCE_HOURLY_INTERVAL,
                    limit=BINANCE_HOURLY_LIMIT,
                    start_time=cursor_ms,
                    end_time=end_ms,
                )
                last_error = None
                break
            except Exception as error:
                msg = str(error)
                if "429" in msg or "418" in msg or "rate" in msg.lower():
                    wait = BINANCE_BACKOFF_BASE_SECONDS * (2 ** attempt)
                    logger.warning(
                        "[HOURLY-BACKFILL] Binance rate limited at %s "
                        "(attempt %d/%d); sleeping %.1fs",
                        cursor.isoformat(), attempt + 1,
                        BINANCE_MAX_RETRIES, wait,
                    )
                    await asyncio.sleep(wait)
                    last_error = error
                else:
                    raise
        if last_error is not None:
            raise last_error

        if not candles:
            break

        all_candles.extend(candles)

        # Advance cursor to one ms past the last candle's open_time.
        last_open_ms = int(candles[-1]["open_time"])
        next_cursor_ms = last_open_ms + 1
        if next_cursor_ms >= end_ms:
            break
        next_cursor = datetime.fromtimestamp(
            next_cursor_ms / 1000, tz=timezone.utc
        )
        if next_cursor <= cursor:
            # Binance returns ascending candles within a page, so
            # this should never fire. If it does, we stop rather
            # than loop forever.
            logger.warning(
                "[HOURLY-BACKFILL] pagination did not advance "
                "(cursor=%s, last_open_ms=%s); stopping to avoid loop",
                cursor.isoformat(), last_open_ms,
            )
            break
        cursor = next_cursor

    return all_candles


async def backfill_btc_hourly(
    start: datetime,
    end: datetime,
) -> int:
    """
    Backfill raw btc_prices with hourly Binance klines.

    Returns the number of rows actually persisted (post dedupe
    and post skip-if-ticks-exist).
    """
    # Floor the start to Binance's inception.
    if start < BINANCE_HOURLY_FLOOR:
        logger.info(
            "[HOURLY-BACKFILL] btc_hourly capping start %s to %s",
            start.isoformat(), BINANCE_HOURLY_FLOOR.isoformat(),
        )
        start = BINANCE_HOURLY_FLOOR

    logger.info(
        "[HOURLY-BACKFILL] btc_hourly range: %s -> %s",
        start.isoformat(), end.isoformat(),
    )

    collector = BinanceCollector()
    repository = BTCPriceRepository()

    try:
        candles = await _fetch_btc_klines_paginated(collector, start, end)
        logger.info(
            "[HOURLY-BACKFILL] btc_hourly received %d raw candles",
            len(candles),
        )
        if not candles:
            return 0

        # Skip hours that already have non-hourly-tagged ticks.
        hours_with_ticks = _existing_raw_hours_without_tag(
            start, end, exclude_source=BINANCE_HOURLY_SOURCE,
        )

        records = []
        skipped = 0
        for candle in candles:
            candle_time = _floor_to_hour(
                datetime.fromtimestamp(
                    candle["open_time"] / 1000, tz=timezone.utc
                )
            )
            if candle_time in hours_with_ticks:
                skipped += 1
                continue
            records.append({
                "time": candle_time,
                "price": float(candle["close"]),
                "volume": float(candle["volume"]),
                "market_cap": None,
            })

        logger.info(
            "[HOURLY-BACKFILL] btc_hourly: %d to write, %d skipped "
            "(existing ticks)",
            len(records), skipped,
        )

        inserted = repository.save_historical_prices(
            records, source=BINANCE_HOURLY_SOURCE,
        )
        logger.info(
            "[HOURLY-BACKFILL] btc_hourly persisted %d rows", inserted,
        )
        return inserted

    finally:
        await collector.close()


# ============================================================
# GOLD HOURLY
# ============================================================


def _count_gold_rows(
    indicator_name: str,
    start: datetime,
    end: datetime,
    source: str,
) -> int:
    """
    Count rows in macro_indicators matching (indicator_name,
    source) in [start, end).

    Used to measure the actual number of rows persisted by
    MacroIndicatorRepository.create_many, which returns the
    input list, not the inserted count.
    """
    sql = text(
        """
        SELECT count(*)
        FROM macro_indicators
        WHERE indicator_name = :ind
          AND source = :src
          AND time >= :start AND time < :end
        """
    )
    session = SessionLocal()
    try:
        return int(
            session.execute(
                sql,
                {
                    "ind": indicator_name,
                    "src": source,
                    "start": start,
                    "end": end,
                },
            ).scalar_one()
        )
    finally:
        session.close()


async def backfill_gold_hourly(
    start: datetime,
    end: datetime,
) -> int:
    """
    Backfill raw macro_indicators with hourly gold spot from
    Yahoo Finance.

    Yahoo only serves ~730 days of hourly history (and may serve
    less for some symbols). We cap the start accordingly and log
    the cap, then filter Yahoo's response client-side to
    [start, end).

    Returns the number of rows actually persisted (post-dedupe).
    """
    yahoo_floor = _last_completed_hour() - timedelta(
        days=YAHOO_HOURLY_MAX_DAYS
    )
    if start < yahoo_floor:
        logger.info(
            "[HOURLY-BACKFILL] gold_hourly capping start %s to %s "
            "(Yahoo %d-day limit)",
            start.isoformat(), yahoo_floor.isoformat(),
            YAHOO_HOURLY_MAX_DAYS,
        )
        start = yahoo_floor

    logger.info(
        "[HOURLY-BACKFILL] gold_hourly range: %s -> %s",
        start.isoformat(), end.isoformat(),
    )

    collector = YahooFinanceCollector()

    try:
        # Yahoo's range_ param only supports fixed strings.
        # Use interval="1h" + range_="730d" then filter client-side.
        raw = await collector.get_gold_spot_history(
            symbol=YahooFinanceCollector.GOLD_SPOT_SYMBOL,
            range_=YAHOO_HOURLY_RANGE,
            interval=YAHOO_HOURLY_INTERVAL,
        )

        start_ms = int(start.timestamp())
        end_ms = int(end.timestamp())

        records = []
        for r in raw:
            ts = int(r["timestamp"])
            if ts < start_ms or ts >= end_ms:
                continue
            dt = _floor_to_hour(
                datetime.fromtimestamp(ts, tz=timezone.utc)
            )
            records.append({
                "indicator_name": YAHOO_HOURLY_INDICATOR,
                "time": dt,
                "value": float(r["price"]),
                "previous_value": None,
                "change_percent": None,
                "source": YAHOO_HOURLY_SOURCE,
            })

        logger.info(
            "[HOURLY-BACKFILL] gold_hourly prepared %d records in range",
            len(records),
        )
        if not records:
            return 0

        records.sort(key=lambda x: x["time"])

        # Measure actual persistence by counting before/after:
        # create_many returns the input list, not the inserted
        # count (ON CONFLICT DO NOTHING silently skips dupes).
        before = _count_gold_rows(
            YAHOO_HOURLY_INDICATOR, start, end, YAHOO_HOURLY_SOURCE,
        )

        session = SessionLocal()
        try:
            repo = MacroIndicatorRepository(session)
            repo.create_many(records)
        finally:
            session.close()

        after = _count_gold_rows(
            YAHOO_HOURLY_INDICATOR, start, end, YAHOO_HOURLY_SOURCE,
        )
        inserted = after - before

        logger.info(
            "[HOURLY-BACKFILL] gold_hourly persisted %d rows "
            "(before=%d after=%d)",
            inserted, before, after,
        )
        return inserted

    finally:
        await collector.close()


# ============================================================
# REGISTRY WIRING
# ============================================================
#
# Wired at module bottom so the functions above are defined
# before they are referenced.

HOURLY_BACKFILL_SOURCES["btc_hourly"]["function"] = backfill_btc_hourly
HOURLY_BACKFILL_SOURCES["gold_hourly"]["function"] = backfill_gold_hourly


# ============================================================
# STALENESS
# ============================================================


def is_source_stale(source_key: str) -> bool:
    """
    Return True if the source's newest row is behind by more than
    its max_age_hours.

    Returns False for unknown keys (fail-open: unknown is not
    stale). Returns True for a source with no rows at all.
    """
    source = HOURLY_BACKFILL_SOURCES.get(source_key)
    if source is None:
        return False

    max_age = source["max_age_hours"]
    table = source["table"]
    tag = source["source_tag"]

    # `table` is interpolated (not parameterized); it must come
    # from the hardcoded HOURLY_BACKFILL_SOURCES registry, never
    # user input.
    sql = text(
        f"""
        SELECT max(time) AS max_time
        FROM {table}
        WHERE source = :tag
        """
    )
    session = SessionLocal()
    try:
        row = session.execute(sql, {"tag": tag}).first()
        if row is None or row.max_time is None:
            return True  # empty => stale
        age = datetime.now(timezone.utc) - row.max_time
        return age > timedelta(hours=max_age)
    finally:
        session.close()


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================


async def run_hourly_backfill(
    keys: list[str],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    days: Optional[int] = None,
) -> dict[str, int]:
    """
    Run one or more hourly backfill sources over a resolved range.

    Returns {source_key: rows_written}, where rows_written is the
    number of rows actually persisted (post-dedupe, post-skip).
    """
    resolved_start, resolved_end = _resolve_hourly_range(start, end, days)
    results: dict[str, int] = {}
    for key in keys:
        source = HOURLY_BACKFILL_SOURCES.get(key)
        if source is None:
            logger.warning("[HOURLY-BACKFILL] unknown source: %s", key)
            continue
        written = await source["function"](resolved_start, resolved_end)
        results[key] = written
    return results