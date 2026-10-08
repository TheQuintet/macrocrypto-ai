"""
Tests for hourly_backfill_service (Chat 4, C4-1).

Uses an in-memory-ish SQLite database via tmp_path. The service
opens its own sessions through SessionLocal, and the repositories
(BTCPriceRepository, MacroIndicatorRepository) also open their
own sessions — so the fixture patches both module-level
SessionLocal references to point at the test engine.

These tests do NOT exercise real Binance or Yahoo. Both
collectors are monkeypatched with fakes that return canned data
or raise canned errors.

Coverage:
  1. backfill_btc_hourly is idempotent on re-run.
  2. Skip-if-ticks-exist: hourly candle is skipped when a
     non-hourly-tagged raw tick exists in the same hour.
  3. 2017-08-17 cap: start earlier than Binance's inception is
     floored.
  4. 1000-candle pagination: two pages are fetched when the
     range spans more than one page.
  5. Rate-limit backoff: a 429 is retried with sleep, then
     succeeds.
  6. Pagination non-advance guard: a fake that returns a
     non-advancing page logs a warning and stops.
  7. is_source_stale: empty table is stale; recent row is not;
     old row is.
  8. backfill_gold_hourly: client-side range filter works.
  9. backfill_gold_hourly: 730-day cap floors the start.
 10. backfill_gold_hourly: returns actual persisted count
     (not attempted), verified by running twice.
 11. run_hourly_backfill: resolves range and dispatches to the
     selected keys.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.services.hourly_backfill_service as svc
from app.services.hourly_backfill_service import (
    BINANCE_HOURLY_FLOOR,
    BINANCE_HOURLY_SOURCE,
    HOURLY_BACKFILL_SOURCES,
    YAHOO_HOURLY_INDICATOR,
    YAHOO_HOURLY_MAX_DAYS,
    YAHOO_HOURLY_SOURCE,
    _existing_raw_hours_without_tag,
    _floor_to_hour,
    _resolve_hourly_range,
    backfill_btc_hourly,
    backfill_gold_hourly,
    is_source_stale,
    run_hourly_backfill,
)


HOUR0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# ----------------------------------------------------------------------
# FIXTURE
# ----------------------------------------------------------------------


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    """
    Build a SQLite DB with the minimal raw tables, and patch every
    SessionLocal the service/repositories use to point at it.

    Returns a namespace with the engine, a session factory, and a
    `session()` helper for assertions.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE btc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TIMESTAMP NOT NULL,
                price REAL NOT NULL,
                volume REAL,
                market_cap REAL,
                source TEXT
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE macro_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TIMESTAMP NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL NOT NULL,
                previous_value REAL,
                change_percent REAL,
                source TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (time, indicator_name)
            )
            """
        ))

    # The service and repositories each import SessionLocal at
    # their own module top, so patch both.
    monkeypatch.setattr(svc, "SessionLocal", Session)

    import app.database.btc_price_repository as btc_repo
    import app.database.macro_indicator_repository as macro_repo
    monkeypatch.setattr(btc_repo, "SessionLocal", Session)
    monkeypatch.setattr(macro_repo, "SessionLocal", Session)

    class Env:
        def __init__(self):
            self.engine = engine
            self.Session = Session

        def session(self):
            return Session()

    yield Env()
    engine.dispose()


def _candle(open_dt: datetime, close: float, volume: float = 1.0) -> dict:
    """Build a Binance-shaped candle dict."""
    return {
        "open_time": int(open_dt.timestamp() * 1000),
        "close": close,
        "volume": volume,
    }


# ----------------------------------------------------------------------
# FAKE COLLECTORS
# ----------------------------------------------------------------------


class FakeBinanceCollector:
    """
    Returns a fixed page of candles per call. `pages` is an
    iterable of lists; each call consumes the next page. Records
    every call for assertions.
    """

    def __init__(self, pages: list[list[dict]]):
        self._pages = list(pages)
        self.calls: list[dict[str, Any]] = []
        self.closed = False

    async def get_klines(self, **kwargs):
        self.calls.append(kwargs)
        if not self._pages:
            return []
        return self._pages.pop(0)

    async def close(self):
        self.closed = True


class FailingThenSucceedingBinanceCollector:
    """Raises N times, then returns one page."""

    def __init__(self, failures: int, page: list[dict], error_msg: str = "429 Too Many Requests"):
        self._remaining_failures = failures
        self._page = page
        self._error_msg = error_msg
        self.calls: list[dict[str, Any]] = []
        self.sleeps: list[float] = []

    async def get_klines(self, **kwargs):
        self.calls.append(kwargs)
        if self._remaining_failures > 0:
            self._remaining_failures -= 1
            raise RuntimeError(self._error_msg)
        return self._page

    async def close(self):
        pass


class FakeYahooCollector:
    """Returns a canned list of {timestamp, price} dicts."""

    def __init__(self, rows: list[dict]):
        self._rows = list(rows)
        self.calls: list[dict[str, Any]] = []

    async def get_gold_spot_history(self, **kwargs):
        self.calls.append(kwargs)
        return self._rows

    async def close(self):
        pass


# ----------------------------------------------------------------------
# 1. Idempotency
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_btc_hourly_is_idempotent(db_env, monkeypatch):
    page = [
        _candle(HOUR0 + timedelta(hours=i), 100.0 + i)
        for i in range(3)
    ]
    fake = FakeBinanceCollector([page])

    # First call gets the page; second call gets empty.
    monkeypatch.setattr(svc, "BinanceCollector", lambda: fake)

    end = HOUR0 + timedelta(hours=3)
    first = await backfill_btc_hourly(HOUR0, end)
    assert first == 3

    # Re-prime the fake with the same page (simulates a re-run).
    fake._pages = [page]
    second = await backfill_btc_hourly(HOUR0, end)
    assert second == 0  # all rows already exist


# ----------------------------------------------------------------------
# 2. Skip-if-ticks-exist
# ----------------------------------------------------------------------


def test_existing_raw_hours_without_tag_excludes_matching_source(db_env):
    with db_env.session() as s:
        # Tick rows (source != binance_backfill_hourly)
        s.execute(text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, :p, :s)"
        ), [
            {"t": HOUR0 + timedelta(minutes=5), "p": 100.0, "s": "binance"},
            {"t": HOUR0 + timedelta(hours=1, minutes=5), "p": 101.0, "s": "binance"},
        ])
        # Hourly-tagged rows should NOT count as ticks
        s.execute(text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, :p, :s)"
        ), {
            "t": HOUR0 + timedelta(hours=2, minutes=5),
            "p": 102.0,
            "s": BINANCE_HOURLY_SOURCE,
        })
        s.commit()

    hours = _existing_raw_hours_without_tag(
        HOUR0, HOUR0 + timedelta(hours=4),
        exclude_source=BINANCE_HOURLY_SOURCE,
    )

    assert HOUR0 in hours
    assert HOUR0 + timedelta(hours=1) in hours
    assert HOUR0 + timedelta(hours=2) not in hours  # only hourly-tagged


@pytest.mark.asyncio
async def test_backfill_btc_hourly_skips_hours_with_ticks(db_env, monkeypatch):
    # Seed a raw tick at HOUR0.
    with db_env.session() as s:
        s.execute(text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, :p, :s)"
        ), {"t": HOUR0 + timedelta(minutes=5), "p": 100.0, "s": "binance"})
        s.commit()

    # Binance returns a candle for HOUR0 and HOUR0+1.
    page = [
        _candle(HOUR0, 105.0),
        _candle(HOUR0 + timedelta(hours=1), 106.0),
    ]
    monkeypatch.setattr(svc, "BinanceCollector", lambda: FakeBinanceCollector([page]))

    written = await backfill_btc_hourly(HOUR0, HOUR0 + timedelta(hours=2))

    # Only HOUR0+1 should be written; HOUR0 is skipped.
    assert written == 1

    with db_env.session() as s:
        rows = s.execute(text(
            "SELECT time, source FROM btc_prices ORDER BY time"
        )).all()
    sources = [r[1] for r in rows]
    assert "binance" in sources
    assert sources.count(BINANCE_HOURLY_SOURCE) == 1


# ----------------------------------------------------------------------
# 3. 2017-08-17 cap
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_btc_hourly_caps_start_at_2017(db_env, monkeypatch):
    fake = FakeBinanceCollector([[]])  # empty response; we only assert the call args
    monkeypatch.setattr(svc, "BinanceCollector", lambda: fake)

    ancient = datetime(2015, 1, 1, tzinfo=timezone.utc)
    await backfill_btc_hourly(ancient, ancient + timedelta(hours=1))

    assert len(fake.calls) == 1
    called_start_ms = fake.calls[0]["start_time"]
    expected_start_ms = int(BINANCE_HOURLY_FLOOR.timestamp() * 1000)
    assert called_start_ms == expected_start_ms


# ----------------------------------------------------------------------
# 4. 1000-candle pagination
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_btc_hourly_paginates(db_env, monkeypatch):
    # Page 1: exactly 1000 candles. Page 2: 1 candle.
    page1 = [
        _candle(HOUR0 + timedelta(hours=i), 100.0)
        for i in range(1000)
    ]
    page2 = [
        _candle(HOUR0 + timedelta(hours=1000), 200.0)
    ]
    fake = FakeBinanceCollector([page1, page2])
    monkeypatch.setattr(svc, "BinanceCollector", lambda: fake)

    await backfill_btc_hourly(HOUR0, HOUR0 + timedelta(hours=1001))

    assert len(fake.calls) == 2
    # Second call's start_time should be one ms after page 1's last open_time.
    expected_second_start_ms = page1[-1]["open_time"] + 1
    assert fake.calls[1]["start_time"] == expected_second_start_ms


# ----------------------------------------------------------------------
# 5. Rate-limit backoff
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_btc_hourly_retries_on_rate_limit(
    db_env, monkeypatch
):
    page = [_candle(HOUR0, 100.0)]
    fake = FailingThenSucceedingBinanceCollector(failures=2, page=page)

    async def fake_sleep(seconds):
        fake.sleeps.append(seconds)

    monkeypatch.setattr(svc, "BinanceCollector", lambda: fake)
    monkeypatch.setattr(svc.asyncio, "sleep", fake_sleep)

    written = await backfill_btc_hourly(HOUR0, HOUR0 + timedelta(hours=1))

    assert written == 1
    # Two retries -> two sleeps, exponential: 2s, 4s.
    assert fake.sleeps == [
        svc.BINANCE_BACKOFF_BASE_SECONDS,
        svc.BINANCE_BACKOFF_BASE_SECONDS * 2,
    ]


@pytest.mark.asyncio
async def test_backfill_btc_hourly_reraises_non_rate_limit(db_env, monkeypatch):
    class BoomCollector:
        async def get_klines(self, **kwargs):
            raise RuntimeError("500 Internal Server Error")

        async def close(self):
            pass

    monkeypatch.setattr(svc, "BinanceCollector", BoomCollector)

    with pytest.raises(RuntimeError, match="500"):
        await backfill_btc_hourly(HOUR0, HOUR0 + timedelta(hours=1))


# ----------------------------------------------------------------------
# 6. Pagination non-advance guard
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_btc_hourly_stops_on_non_advancing_page(
    db_env, monkeypatch, caplog
):
    # A single candle whose open_time is BEFORE the cursor.
    stuck = [_candle(HOUR0 - timedelta(hours=1), 100.0)]
    fake = FakeBinanceCollector([stuck, stuck, stuck])
    monkeypatch.setattr(svc, "BinanceCollector", lambda: fake)

    with caplog.at_level("WARNING"):
        written = await backfill_btc_hourly(HOUR0, HOUR0 + timedelta(hours=5))

    # The candle's hour is HOUR0-1h, which is < HOUR0, so
    # _existing_raw_hours_without_tag isn't consulted for it;
    # the row is written. Then pagination stops.
    assert written == 1
    assert any("did not advance" in r.message for r in caplog.records)
    # Only one call should have been made before the guard fired.
    assert len(fake.calls) == 1


# ----------------------------------------------------------------------
# 7. Staleness
# ----------------------------------------------------------------------


def test_is_source_stale_empty_table_is_stale(db_env):
    assert is_source_stale("btc_hourly") is True
    assert is_source_stale("gold_hourly") is True


def test_is_source_stale_recent_row_is_fresh(db_env):
    with db_env.session() as s:
        s.execute(text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, :p, :s)"
        ), {
            "t": datetime.now(timezone.utc) - timedelta(hours=1),
            "p": 100.0,
            "s": BINANCE_HOURLY_SOURCE,
        })
        s.commit()

    assert is_source_stale("btc_hourly") is False


def test_is_source_stale_old_row_is_stale(db_env):
    with db_env.session() as s:
        s.execute(text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, :p, :s)"
        ), {
            "t": datetime.now(timezone.utc) - timedelta(hours=7),
            "p": 100.0,
            "s": BINANCE_HOURLY_SOURCE,
        })
        s.commit()

    assert is_source_stale("btc_hourly") is True


def test_is_source_stale_unknown_key_is_false(db_env):
    assert is_source_stale("nonexistent") is False


# ----------------------------------------------------------------------
# 8. Gold: client-side range filter
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_gold_hourly_filters_by_range(db_env, monkeypatch):
    rows = [
        {"timestamp": int((HOUR0 - timedelta(hours=1)).timestamp()), "price": 1.0},
        {"timestamp": int(HOUR0.timestamp()), "price": 2.0},
        {"timestamp": int((HOUR0 + timedelta(hours=1)).timestamp()), "price": 3.0},
    ]
    fake = FakeYahooCollector(rows)
    monkeypatch.setattr(svc, "YahooFinanceCollector", lambda: fake)

    written = await backfill_gold_hourly(HOUR0, HOUR0 + timedelta(hours=1))

    assert written == 1

    with db_env.session() as s:
        stored = s.execute(text(
            "SELECT time, value FROM macro_indicators "
            "WHERE indicator_name = :n AND source = :s"
        ), {"n": YAHOO_HOURLY_INDICATOR, "s": YAHOO_HOURLY_SOURCE}).all()
    assert len(stored) == 1
    assert stored[0][1] == 2.0


# ----------------------------------------------------------------------
# 9. Gold: 730-day cap
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_gold_hourly_caps_start(db_env, monkeypatch):
    fake = FakeYahooCollector([])
    monkeypatch.setattr(svc, "YahooFinanceCollector", lambda: fake)

    ancient = datetime(2015, 1, 1, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    # Should not raise; start is floored internally.
    written = await backfill_gold_hourly(ancient, now)
    assert written == 0


# ----------------------------------------------------------------------
# 10. Gold: persisted count, not attempted
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backfill_gold_hourly_returns_persisted_not_attempted(
    db_env, monkeypatch
):
    rows = [
        {"timestamp": int(HOUR0.timestamp()), "price": 2.0},
        {"timestamp": int((HOUR0 + timedelta(hours=1)).timestamp()), "price": 3.0},
    ]
    fake = FakeYahooCollector(rows)
    monkeypatch.setattr(svc, "YahooFinanceCollector", lambda: fake)

    first = await backfill_gold_hourly(HOUR0, HOUR0 + timedelta(hours=2))
    assert first == 2

    # Re-run: same rows, but they already exist. Must return 0.
    second = await backfill_gold_hourly(HOUR0, HOUR0 + timedelta(hours=2))
    assert second == 0


# ----------------------------------------------------------------------
# 11. run_hourly_backfill dispatch
# ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_hourly_backfill_dispatches_selected_keys(
    db_env, monkeypatch
):
    btc_fake = FakeBinanceCollector([[_candle(HOUR0, 100.0)]])
    gold_fake = FakeYahooCollector(
        [{"timestamp": int(HOUR0.timestamp()), "price": 2.0}]
    )
    monkeypatch.setattr(svc, "BinanceCollector", lambda: btc_fake)
    monkeypatch.setattr(svc, "YahooFinanceCollector", lambda: gold_fake)

    # Use explicit start/end so we don't depend on wall clock.
    results = await run_hourly_backfill(
        ["btc_hourly", "gold_hourly"],
        start=HOUR0,
        end=HOUR0 + timedelta(hours=1),
    )

    assert results["btc_hourly"] == 1
    assert results["gold_hourly"] == 1


@pytest.mark.asyncio
async def test_run_hourly_backfill_ignores_unknown_keys(
    db_env, monkeypatch, caplog
):
    monkeypatch.setattr(svc, "BinanceCollector", lambda: FakeBinanceCollector([[]]))

    with caplog.at_level("WARNING"):
        results = await run_hourly_backfill(
            ["btc_hourly", "nonexistent"],
            start=HOUR0,
            end=HOUR0 + timedelta(hours=1),
        )

    assert "btc_hourly" in results
    assert "nonexistent" not in results
    assert any("unknown source" in r.message for r in caplog.records)


# ----------------------------------------------------------------------
# Bonus: range resolution warns when both days and start/end given
# ----------------------------------------------------------------------


def test_resolve_hourly_range_warns_on_days_and_start(caplog):
    with caplog.at_level("WARNING"):
        _resolve_hourly_range(
            start=HOUR0,
            end=HOUR0 + timedelta(hours=1),
            days=7,
        )
    assert any("days takes precedence" in r.message for r in caplog.records)