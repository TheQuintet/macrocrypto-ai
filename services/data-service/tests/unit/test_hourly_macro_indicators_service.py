"""
Tests for HourlyMacroIndicatorsService.

Uses an in-memory SQLite database. The service uses raw SQL
against macro_indicators plus the repository's upsert. We create
minimal versions of those tables in SQLite so the queries run.

These tests do NOT test TimescaleDB-specific features. Those
belong to integration tests.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.hourly_macro_indicators_service import (
    HourlyMacroIndicatorsService,
    RENAME_MAP,
)


HOUR0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def db(tmp_path):
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
                created_at TIMESTAMP NOT NULL
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE macro_indicators_hourly (
                time TIMESTAMP PRIMARY KEY,
                cpi REAL,
                interest_rate REAL,
                m2_growth REAL,
                dxy REAL,
                treasury_yield REAL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _add_raw(db, dt, indicator_name, value):
    db.execute(
        text(
            "INSERT INTO macro_indicators "
            "(time, indicator_name, value, created_at) "
            "VALUES (:t, :n, :v, :t)"
        ),
        {"t": dt, "n": indicator_name, "v": value},
    )


# ----------------------------------------------------------------------
# RENAME_MAP sanity
# ----------------------------------------------------------------------


def test_rename_map_matches_locked_mappings():
    assert RENAME_MAP == {
        "cpi": "cpi",
        "federal_funds_rate": "interest_rate",
        "m2_money_supply": "m2_growth",
        "dxy": "dxy",
        "ten_year_treasury": "treasury_yield",
    }


# ----------------------------------------------------------------------
# build_hour_row / ffill
# ----------------------------------------------------------------------


def test_build_hour_row_all_null_when_no_raw_data(db):
    service = HourlyMacroIndicatorsService(db)
    row = service.build_hour_row(HOUR0)

    assert row["time"] == HOUR0
    assert row["cpi"] is None
    assert row["interest_rate"] is None
    assert row["m2_growth"] is None
    assert row["dxy"] is None
    assert row["treasury_yield"] is None


def test_build_hour_row_uses_latest_observation_per_indicator(db):
    # cpi: two observations; the second is the one <= HOUR0.
    _add_raw(db, HOUR0 - timedelta(days=60), "cpi", 300.0)
    _add_raw(db, HOUR0 - timedelta(days=30), "cpi", 310.0)
    # dxy: one observation before HOUR0.
    _add_raw(db, HOUR0 - timedelta(hours=6), "dxy", 104.0)
    # treasury_yield: one observation after HOUR0 — must NOT be used.
    _add_raw(db, HOUR0 + timedelta(hours=1), "ten_year_treasury", 9.99)
    db.commit()

    service = HourlyMacroIndicatorsService(db)
    row = service.build_hour_row(HOUR0)

    assert row["cpi"] == 310.0
    assert row["dxy"] == 104.0
    assert row["treasury_yield"] is None  # nothing <= HOUR0
    assert row["interest_rate"] is None
    assert row["m2_growth"] is None


def test_build_hour_row_renames_columns_correctly(db):
    _add_raw(db, HOUR0 - timedelta(days=1), "cpi", 1.0)
    _add_raw(db, HOUR0 - timedelta(days=1), "federal_funds_rate", 2.0)
    _add_raw(db, HOUR0 - timedelta(days=1), "m2_money_supply", 3.0)
    _add_raw(db, HOUR0 - timedelta(days=1), "dxy", 4.0)
    _add_raw(db, HOUR0 - timedelta(days=1), "ten_year_treasury", 5.0)
    db.commit()

    service = HourlyMacroIndicatorsService(db)
    row = service.build_hour_row(HOUR0)

    assert row["cpi"] == 1.0
    assert row["interest_rate"] == 2.0
    assert row["m2_growth"] == 3.0
    assert row["dxy"] == 4.0
    assert row["treasury_yield"] == 5.0


def test_build_hour_row_ffills_across_many_hours(db):
    """
    An observation 100 days before HOUR0 is still used. There
    is no age limit.
    """
    _add_raw(db, HOUR0 - timedelta(days=100), "cpi", 250.0)
    db.commit()

    service = HourlyMacroIndicatorsService(db)
    row = service.build_hour_row(HOUR0)

    assert row["cpi"] == 250.0


# ----------------------------------------------------------------------
# write_hour
# ----------------------------------------------------------------------


def test_write_hour_writes_all_null_row_when_no_data(db):
    service = HourlyMacroIndicatorsService(db)
    wrote = service.write_hour(HOUR0)

    assert wrote is True
    stored = service.repository.get_by_time(HOUR0)
    assert stored is not None
    assert stored.cpi is None
    assert stored.interest_rate is None


def test_write_hour_does_not_double_write(db, monkeypatch):
    """
    Second write for the same hour is a no-op under
    ON CONFLICT DO NOTHING. Asserted by checking the repository
    is called and the row count stays at 1.
    """
    service = HourlyMacroIndicatorsService(db)

    # Use a monkeypatch on upsert_many to observe call count.
    calls = {"n": 0}
    original = service.repository.upsert_many

    def spy(rows):
        calls["n"] += 1
        return original(rows)

    monkeypatch.setattr(service.repository, "upsert_many", spy)

    service.write_hour(HOUR0)
    service.write_hour(HOUR0)

    assert calls["n"] == 2

    count = db.execute(
        text("SELECT COUNT(*) FROM macro_indicators_hourly")
    ).scalar()
    assert count == 1


# ----------------------------------------------------------------------
# backfill
# ----------------------------------------------------------------------


def test_backfill_writes_every_hour_in_range(db):
    """
    Unlike btc_prices_hourly, no hour is skipped. Every hour in
    the range gets a row.
    """
    service = HourlyMacroIndicatorsService(db)

    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    summary = service.backfill(start=start, end=end)

    assert summary["expected_hours"] == 3
    assert summary["written"] == 3

    count = db.execute(
        text("SELECT COUNT(*) FROM macro_indicators_hourly")
    ).scalar()
    assert count == 3


def test_backfill_is_idempotent(db):
    service = HourlyMacroIndicatorsService(db)

    start = HOUR0
    end = HOUR0 + timedelta(hours=2)

    first = service.backfill(start=start, end=end)
    second = service.backfill(start=start, end=end)

    assert first["written"] == 2
    assert second["written"] == 0
    assert second["already_present"] == 2


def test_backfill_verify_only_writes_nothing(db):
    service = HourlyMacroIndicatorsService(db)

    start = HOUR0
    end = HOUR0 + timedelta(hours=2)
    summary = service.backfill(
        start=start, end=end, verify_only=True,
    )

    assert summary["missing"] == [
        HOUR0,
        HOUR0 + timedelta(hours=1),
    ]

    count = db.execute(
        text("SELECT COUNT(*) FROM macro_indicators_hourly")
    ).scalar()
    assert count == 0