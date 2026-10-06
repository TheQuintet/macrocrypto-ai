"""
Tests for HourlyBTCPricesService.

Uses an in-memory SQLite database. The service uses raw SQL against
btc_prices, btc_dominance, and macro_indicators, plus the
repository's upsert. We create minimal versions of those tables in
SQLite so the queries run.

These tests do NOT test TimescaleDB-specific features
(create_hypertable). Those belong to integration tests.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database.btc_prices_hourly_repository import (
    BTCPriceHourlyRepository,
)
from app.services.hourly_btc_prices_service import (
    HourlyBTCPricesService,
    _floor_to_hour,
)


HOUR0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE btc_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TIMESTAMP NOT NULL,
                price REAL NOT NULL,
                volume REAL,
                source TEXT
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE btc_dominance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TIMESTAMP NOT NULL,
                dominance REAL NOT NULL,
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
                created_at TIMESTAMP NOT NULL
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE btc_prices_hourly (
                time TIMESTAMP PRIMARY KEY,
                close REAL,
                volume REAL,
                volatility REAL,
                dominance REAL,
                active_addresses REAL,
                price_lag_7d REAL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _add_tick(db, dt, price, volume=None):
    db.execute(
        text(
            "INSERT INTO btc_prices (time, price, volume) "
            "VALUES (:t, :p, :v)"
        ),
        {"t": dt, "p": price, "v": volume},
    )


def _add_dominance(db, dt, value):
    db.execute(
        text(
            "INSERT INTO btc_dominance (time, dominance) "
            "VALUES (:t, :v)"
        ),
        {"t": dt, "v": value},
    )


def _add_active_addresses(db, dt, value):
    db.execute(
        text(
            "INSERT INTO macro_indicators "
            "(time, indicator_name, value, created_at) "
            "VALUES (:t, :n, :v, :t)"
        ),
        {"t": dt, "n": "active_addresses", "v": value},
    )


# ----------------------------------------------------------------------
# fetch_hour_bucket
# ----------------------------------------------------------------------


def test_fetch_hour_bucket_returns_none_when_no_ticks(db):
    service = HourlyBTCPricesService(db)
    assert service.fetch_hour_bucket(HOUR0) is None


def test_fetch_hour_bucket_aggregates_close_and_volume(db):
    _add_tick(db, HOUR0 + timedelta(minutes=1), 100.0, 1.0)
    _add_tick(db, HOUR0 + timedelta(minutes=30), 105.0, 2.0)
    _add_tick(db, HOUR0 + timedelta(minutes=59), 103.0, 3.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    bucket = service.fetch_hour_bucket(HOUR0)

    assert bucket is not None
    assert bucket["close"] == 103.0
    assert bucket["volume"] == 6.0


def test_fetch_hour_bucket_ignores_ticks_outside_hour(db):
    _add_tick(db, HOUR0 - timedelta(seconds=1), 999.0, 999.0)
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0, 1.0)
    _add_tick(db, HOUR0 + timedelta(hours=1), 999.0, 999.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    bucket = service.fetch_hour_bucket(HOUR0)

    assert bucket["close"] == 100.0
    assert bucket["volume"] == 1.0


# ----------------------------------------------------------------------
# volatility
# ----------------------------------------------------------------------


def test_volatility_null_when_single_tick(db):
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0, 1.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    bucket = service.fetch_hour_bucket(HOUR0)

    assert bucket["volatility"] is None


def test_volatility_matches_ddof_1_log_returns(db):
    prices = [100.0, 101.0, 99.0, 102.0, 100.5]
    for i, p in enumerate(prices):
        _add_tick(db, HOUR0 + timedelta(minutes=i), p, 1.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    bucket = service.fetch_hour_bucket(HOUR0)

    log_returns = [
        math.log(prices[i] / prices[i - 1])
        for i in range(1, len(prices))
    ]
    n = len(log_returns)
    mean = sum(log_returns) / n
    expected = math.sqrt(
        sum((r - mean) ** 2 for r in log_returns) / (n - 1)
    )

    assert bucket["volatility"] == pytest.approx(expected)


# ----------------------------------------------------------------------
# dominance / active_addresses
# ----------------------------------------------------------------------


def test_dominance_uses_latest_row_at_or_before_hour(db):
    _add_dominance(db, HOUR0 - timedelta(hours=2), 50.0)
    _add_dominance(db, HOUR0, 51.0)
    _add_dominance(db, HOUR0 + timedelta(hours=3), 99.0)
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    row = service.build_hour_row(HOUR0)

    assert row["dominance"] == 51.0


def test_dominance_null_when_no_row_before_hour(db):
    _add_dominance(db, HOUR0 + timedelta(hours=1), 51.0)
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    row = service.build_hour_row(HOUR0)

    assert row["dominance"] is None


def test_active_addresses_uses_latest_row_at_or_before_hour(db):
    _add_active_addresses(db, HOUR0 - timedelta(days=1), 1000.0)
    _add_active_addresses(db, HOUR0 - timedelta(hours=1), 1100.0)
    _add_active_addresses(db, HOUR0 + timedelta(days=1), 9999.0)
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    row = service.build_hour_row(HOUR0)

    assert row["active_addresses"] == 1100.0


# ----------------------------------------------------------------------
# price_lag_7d
# ----------------------------------------------------------------------def test_price_lag_7d_uses_exact_row(db):
    lag_hour = HOUR0 - timedelta(days=7)
    db.execute(
        text(
            "INSERT INTO btc_prices_hourly (time, close) "
            "VALUES (:t, :c)"
        ),
        {"t": lag_hour, "c": 88.0},
    )
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    row = service.build_hour_row(HOUR0)

    assert row["price_lag_7d"] == 88.0


def test_price_lag_7d_null_when_lag_row_missing(db):
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    row = service.build_hour_row(HOUR0)

    assert row["price_lag_7d"] is None


# ----------------------------------------------------------------------
# build_hour_row / write_hour
# ----------------------------------------------------------------------


def test_build_hour_row_returns_none_when_no_ticks(db):
    service = HourlyBTCPricesService(db)
    assert service.build_hour_row(HOUR0) is None


def test_write_hour_skips_empty_hour(db):
    service = HourlyBTCPricesService(db)
    wrote = service.write_hour(HOUR0)

    assert wrote is False
    assert service.repository.get_by_time(HOUR0) is None


def test_write_hour_writes_when_ticks_present(db):
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0, 1.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    wrote = service.write_hour(HOUR0)

    assert wrote is True

    stored = service.repository.get_by_time(HOUR0)
    assert stored is not None
    assert stored.close == 100.0


# ----------------------------------------------------------------------
# backfill
# ----------------------------------------------------------------------


def test_backfill_is_idempotent(db, monkeypatch):
    """
    Running backfill twice does not create duplicate rows and does
    not error on the second run.
    """
    # Seed ticks for two hours.
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    _add_tick(db, HOUR0 + timedelta(hours=1, minutes=30), 101.0)
    db.commit()

    service = HourlyBTCPricesService(db)

    # Bypass _last_completed_hour so the range isn't clamped
    # (SQLite test env has no real "now" constraint we care about).
    start = HOUR0
    end = HOUR0 + timedelta(hours=2)

    first = service.backfill(start=start, end=end)
    second = service.backfill(start=start, end=end)

    assert first["written"] == 2
    assert second["written"] == 0
    assert second["already_present"] == 2

    # Still exactly two rows.
    rows = db.execute(
        text("SELECT COUNT(*) FROM btc_prices_hourly")
    ).scalar()
    assert rows == 2


def test_backfill_skips_hours_with_no_ticks(db):
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    # No tick for HOUR0 + 1h.
    _add_tick(db, HOUR0 + timedelta(hours=2, minutes=30), 102.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    summary = service.backfill(
        start=HOUR0,
        end=HOUR0 + timedelta(hours=3),
    )

    assert summary["written"] == 2
    assert summary["skipped_no_data"] == 1


def test_backfill_verify_only_writes_nothing(db):
    _add_tick(db, HOUR0 + timedelta(minutes=30), 100.0)
    db.commit()

    service = HourlyBTCPricesService(db)
    summary = service.backfill(
        start=HOUR0,
        end=HOUR0 + timedelta(hours=1),
        verify_only=True,
    )

    assert summary["missing"] == [HOUR0]
    assert summary["written"] == 0

    rows = db.execute(
        text("SELECT COUNT(*) FROM btc_prices_hourly")
    ).scalar()
    assert rows == 0