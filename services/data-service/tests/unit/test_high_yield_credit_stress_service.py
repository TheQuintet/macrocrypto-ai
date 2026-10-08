"""
Tests for HighYieldCreditStressService.

Fixture style mirrors tests/unit/test_hourly_btc_prices_service.py:
a local SQLite database created with hand-rolled CREATE TABLE
statements, so the tests run without Postgres. The repository's
ON CONFLICT (time, indicator_name) clause compiles to
INSERT ... ON CONFLICT DO NOTHING, which SQLite has supported
since 3.24, so create_many works on both dialects.

No network access: the YahooFinanceCollector is replaced with a
FakeCollector that returns canned records per symbol.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.high_yield_credit_stress_service import (
    HY_PROXY_INDICATOR,
    HY_PROXY_SOURCE,
    HYG_SYMBOL,
    SHY_SYMBOL,
    HighYieldCreditStressService,
    _records_to_series,
)


# ==============================================================
# Fixtures
# ==============================================================


class FakeCollector:
    """
    Stand-in for YahooFinanceCollector.

    Returns whatever records were configured per symbol. If a
    symbol is not configured, get_daily_history raises KeyError
    so a test that forgot to seed it fails loudly rather than
    silently seeing an empty list.

    Records are in the shape the real collector returns:

        {"timestamp": <int Unix seconds>, "price": <float>,
         "symbol": <str>}
    """

    def __init__(self, by_symbol: dict[str, list[dict]]):
        self._by_symbol = by_symbol
        self.close_called = False

    async def get_daily_history(
        self,
        symbol: str,
        range_: str = "5y",
        interval: str = "1d",
    ) -> list[dict]:
        return self._by_symbol[symbol]

    async def close(self) -> None:
        self.close_called = True


def _yahoo_records(
    prices: dict[str, float],
    base_ts: int = 1_700_000_000,
) -> list[dict]:
    """
    Build Yahoo-shaped records from a {date_str: price} mapping.

    Timestamps are generated as consecutive days starting at
    base_ts (a fixed epoch). The service normalizes to midnight
    UTC, so the exact time of day in the timestamp does not
    matter for the test — only that the calendar days are
    distinct and increasing.
    """
    from datetime import timedelta

    base_dt = datetime.fromtimestamp(base_ts, tz=timezone.utc)

    records = []
    for i, (date_str, price) in enumerate(prices.items()):
        dt = base_dt + timedelta(days=i)
        # Noon UTC, so normalize() can only go one way.
        dt = dt.replace(hour=12, minute=0, second=0, microsecond=0)
        records.append(
            {
                "timestamp": int(dt.timestamp()),
                "price": float(price),
                "symbol": "",  # filled by the caller via the dict key
            }
        )
    return records


@pytest.fixture
def db(tmp_path):
    """
    Local SQLite database with a minimal macro_indicators table
    matching the columns the service and repository touch.

    The unique constraint on (time, indicator_name) is required
    for create_many's ON CONFLICT clause to deduplicate.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    with engine.begin() as conn:
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
                created_at TIMESTAMP NOT NULL,
                UNIQUE (time, indicator_name)
            )
            """
        ))

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================
# _records_to_series
# ==============================================================


def test_records_to_series_builds_sorted_float_series():
    records = _yahoo_records({"2024-01-01": 100.0, "2024-01-02": 101.0})
    series = _records_to_series(records)

    assert len(series) == 2
    assert series.dtype == "float64"
    # Sorted ascending.
    assert list(series.index) == sorted(series.index)


def test_records_to_series_collapses_duplicate_days_keeping_last():
    """
    Yahoo occasionally emits two candles for the same calendar
    day. The Series must keep the last one.
    """
    from datetime import datetime, timezone

    day = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    ts = int(day.timestamp())

    records = [
        {"timestamp": ts, "price": 100.0, "symbol": "X"},
        {"timestamp": ts, "price": 200.0, "symbol": "X"},
    ]

    series = _records_to_series(records)

    assert len(series) == 1
    assert series.iloc[0] == 200.0


# ==============================================================
# collect() — input validation
# ==============================================================


@pytest.mark.asyncio
async def test_collect_returns_empty_when_hyg_empty(db):
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: [],
            SHY_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 101.0}
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    assert result == []


@pytest.mark.asyncio
async def test_collect_returns_empty_when_shy_empty(db):
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 101.0}
            ),
            SHY_SYMBOL: [],
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    assert result == []


@pytest.mark.asyncio
async def test_collect_returns_empty_when_fewer_than_two_aligned_days(db):
    """
    One aligned day is not enough to compute pct_change.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records({"2024-01-01": 100.0}),
            SHY_SYMBOL: _yahoo_records({"2024-01-01": 100.0}),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    assert result == []


@pytest.mark.asyncio
async def test_collect_aligns_on_inner_join(db):
    """
    Days where only one ETF has data are dropped.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {
                    "2024-01-01": 100.0,
                    "2024-01-02": 101.0,
                    "2024-01-03": 102.0,
                }
            ),
            SHY_SYMBOL: _yahoo_records(
                {
                    "2024-01-01": 50.0,
                    # 01-02 missing on SHY side
                    "2024-01-03": 51.0,
                }
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    # Only 01-01 and 01-03 survive the inner join; pct_change
    # then drops the first row, leaving just 01-03.
    assert len(result) == 1


# ==============================================================
# collect() — computation
# ==============================================================


@pytest.mark.asyncio
async def test_collect_computes_pct_change_correctly(db):
    """
    Hand-computed expectation:

        HYG: 100, 105, 105
        SHY: 50,  50,  52.5

        ratio: 2.0, 2.1, 2.0
        pct_change: NaN, +0.05, -0.047619...

    First row is NaN and must be dropped.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 105.0, "2024-01-03": 105.0}
            ),
            SHY_SYMBOL: _yahoo_records(
                {"2024-01-01": 50.0, "2024-01-02": 50.0, "2024-01-03": 52.5}
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    assert len(result) == 2
    # Result is ordered by observation date ascending.
    assert result[0]["value"] == pytest.approx(0.05)
    assert result[1]["value"] == pytest.approx(-0.04761904761904767)


@pytest.mark.asyncio
async def test_collect_skips_first_nan_row(db):
    """
    pct_change always yields NaN for the first row; the service
    must not emit a record for it.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 101.0}
            ),
            SHY_SYMBOL: _yahoo_records(
                {"2024-01-01": 50.0, "2024-01-02": 50.0}
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    # 2 input days -> 1 pct_change value (the second day).
    assert len(result) == 1
    # The surviving record is 2024-01-02.
    assert result[0]["time"] == datetime(
        2024, 1, 2, 0, 0, 0, tzinfo=timezone.utc
    )


# ==============================================================
# collect() — record shape
# ==============================================================


@pytest.mark.asyncio
async def test_collect_sets_source_and_indicator_name(db):
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 101.0}
            ),
            SHY_SYMBOL: _yahoo_records(
                {"2024-01-01": 50.0, "2024-01-02": 50.0}
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    assert result
    for record in result:
        assert record["indicator_name"] == HY_PROXY_INDICATOR
        assert record["source"] == HY_PROXY_SOURCE
        assert record["previous_value"] is None
        assert record["change_percent"] is None


@pytest.mark.asyncio
async def test_collect_uses_midnight_utc_for_time(db):
    """
    Every record's `time` must be exactly midnight UTC of the
    observation day. This is the Q-B5-6 decision: it makes the
    writer idempotent under the (time, indicator_name) unique
    constraint and keeps the daily series PIT-correct for the
    features writer.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 101.0}
            ),
            SHY_SYMBOL: _yahoo_records(
                {"2024-01-01": 50.0, "2024-01-02": 50.0}
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    result = await service.collect()

    assert result
    for record in result:
        t = record["time"]
        assert t.tzinfo is timezone.utc
        assert t.hour == 0
        assert t.minute == 0
        assert t.second == 0
        assert t.microsecond == 0


# ==============================================================
# Persistence — repository round-trip
# ==============================================================


@pytest.mark.asyncio
async def test_create_many_is_idempotent(db):
    """
    Persisting the same records twice must not create duplicates.
    Relies on the (time, indicator_name) unique constraint and
    the repository's ON CONFLICT clause.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {"2024-01-01": 100.0, "2024-01-02": 101.0}
            ),
            SHY_SYMBOL: _yahoo_records(
                {"2024-01-01": 50.0, "2024-01-02": 50.0}
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    records = await service.collect()
    assert records

    service.repository.create_many(records)
    count_after_first = db.execute(
        text("SELECT COUNT(*) FROM macro_indicators")
    ).scalar()
    assert count_after_first == len(records)

    service.repository.create_many(records)
    count_after_second = db.execute(
        text("SELECT COUNT(*) FROM macro_indicators")
    ).scalar()
    assert count_after_second == count_after_first


@pytest.mark.asyncio
async def test_collect_and_persist_end_to_end(db):
    """
    Full pipeline: fake collector -> collect() -> create_many ->
    read back through the repository.
    """
    collector = FakeCollector(
        by_symbol={
            HYG_SYMBOL: _yahoo_records(
                {
                    "2024-01-01": 100.0,
                    "2024-01-02": 105.0,
                    "2024-01-03": 105.0,
                }
            ),
            SHY_SYMBOL: _yahoo_records(
                {
                    "2024-01-01": 50.0,
                    "2024-01-02": 50.0,
                    "2024-01-03": 52.5,
                }
            ),
        }
    )
    service = HighYieldCreditStressService(db, collector=collector)

    records = await service.collect()
    assert len(records) == 2

    service.repository.create_many(records)

    stored = service.repository.get_historical_data(
        indicator_name=HY_PROXY_INDICATOR,
        days=36500,  # wide enough that the fixture dates are in range
    )

    assert len(stored) == 2

    # Order is ascending by time; values match what collect()
    # produced.
    stored_values = [row.value for row in stored]
    assert stored_values[0] == pytest.approx(records[0]["value"])
    assert stored_values[1] == pytest.approx(records[1]["value"])

    # Every stored row has the correct source.
    for row in stored:
        assert row.source == HY_PROXY_SOURCE


# ==============================================================
# close()
# ==============================================================


@pytest.mark.asyncio
async def test_close_does_not_close_injected_collector(db):
    """
    If the caller passed a collector, we must not close it —
    the caller owns its lifecycle.
    """
    collector = FakeCollector(by_symbol={HYG_SYMBOL: [], SHY_SYMBOL: []})
    service = HighYieldCreditStressService(db, collector=collector)

    await service.close()

    assert collector.close_called is False