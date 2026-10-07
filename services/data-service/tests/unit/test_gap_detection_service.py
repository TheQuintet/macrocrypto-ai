"""
Tests for gap_detection_service (Chat 4, C4-2).

Uses SQLite via tmp_path. The service opens its own sessions
through SessionLocal, and the repair path calls into Chat 3's
hourly writers, which also open sessions via SessionLocal. The
fixture patches SessionLocal in every module involved.

These tests do NOT exercise real Binance, Yahoo, or Postgres.
They build raw rows by hand and assert on scan/repair behavior.

Coverage:
  1. Empty hourly table -> 100% missing.
       BTC: all RAW_DATA_GAP (no ticks exist).
       Macro: all RAW_DATA_GAP (no prior observations exist).
  2. Full hourly table -> 0% missing.
  3. Mixed BTC: hours with ticks -> MATERIALIZATION_GAP,
     hours without -> RAW_DATA_GAP.
  4. BTC asymmetry: an hour with no tick is RAW_DATA_GAP even
     if a prior hour has a tick (unlike macro).
  5. Macro asymmetry: hour before earliest raw obs ->
     RAW_DATA_GAP; hour after -> MATERIALIZATION_GAP.
  6. scan() is read-only (no rows written).
  7. repair() only calls write_hour for MATERIALIZATION_GAP.
  8. repair() summary shape.
  9. suggested_commands() for BTC and macro produce the
     correct CLI pointers (BTC -> run_hourly_backfills --btc;
     macro -> run_backfills).
 10. Unsupported table name -> ValueError.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import app.services.gap_detection_service as gds
import app.services.hourly_btc_prices_service as hbps
import app.services.hourly_macro_indicators_service as hmis
import app.database.btc_prices_hourly_repository as btch_repo
import app.database.macro_indicators_hourly_repository as macroh_repo
import app.database.btc_price_repository as btc_repo
import app.database.macro_indicator_repository as macro_repo

from app.services.gap_detection_service import (
    GapClass,
    GapReport,
    MissingHour,
    TABLE_BTC,
    TABLE_MACRO,
    scan,
    repair,
)


# A stable reference hour, far from wall-clock so _last_completed_hour
# clamping doesn't interfere (we still pass an explicit end <= now).
HOUR0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# ======================================================================
# FIXTURE
# ======================================================================


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    """
    Build a SQLite DB with the raw + hourly tables the service
    touches, and patch every SessionLocal the code paths open.

    Also captures write_hour calls so tests can assert repair
    behavior without inspecting the DB.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with engine.begin() as conn:
        # Raw tables
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
        # Hourly tables
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
        # btc_dominance — HourlyBTCPricesService.build_hour_row
        # queries it during repair.
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

    # Patch SessionLocal in every module that opens one.
    for mod in (
        gds,
        hbps,
        hmis,
        btch_repo,
        macroh_repo,
        btc_repo,
        macro_repo,
    ):
        monkeypatch.setattr(mod, "SessionLocal", Session)

    class Env:
        def __init__(self):
            self.engine = engine
            self.Session = Session

        def session(self):
            return Session()

    yield Env()
    engine.dispose()


def _add_btc_tick(session, dt: datetime, price: float = 100.0):
    session.execute(
        text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, :p, 'binance')"
        ),
        {"t": dt, "p": price},
    )


def _add_btc_hourly(session, dt: datetime, close: float = 100.0):
    session.execute(
        text(
            "INSERT INTO btc_prices_hourly (time, close) "
            "VALUES (:t, :c)"
        ),
        {"t": dt, "c": close},
    )


def _add_macro_raw(session, dt: datetime, name: str = "cpi", value: float = 1.0):
    session.execute(
        text(
            "INSERT INTO macro_indicators "
            "(time, indicator_name, value, source) "
            "VALUES (:t, :n, :v, 'fred')"
        ),
        {"t": dt, "n": name, "v": value},
    )


def _add_macro_hourly(session, dt: datetime):
    session.execute(
        text(
            "INSERT INTO macro_indicators_hourly (time) VALUES (:t)"
        ),
        {"t": dt},
    )


# ======================================================================
# 1. Empty hourly table -> 100% missing
# ======================================================================


def test_scan_btc_empty_table_all_raw_gaps(db_env):
    # No btc_prices ticks at all, no btc_prices_hourly rows.
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)

    report = scan(TABLE_BTC, start, end)

    assert report.expected_hours == 3
    assert report.actual_hours == 0
    assert report.missing_count == 3
    assert report.materialization_count == 0
    assert report.raw_data_count == 3
    assert all(
        m.classification == GapClass.RAW_DATA_GAP
        for m in report.missing_hours
    )


def test_scan_macro_empty_table_all_raw_gaps(db_env):
    # No macro_indicators rows at all, no macro_indicators_hourly rows.
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)

    report = scan(TABLE_MACRO, start, end)

    assert report.expected_hours == 3
    assert report.actual_hours == 0
    assert report.missing_count == 3
    assert report.materialization_count == 0
    assert report.raw_data_count == 3


# ======================================================================
# 2. Full hourly table -> 0% missing
# ======================================================================


def test_scan_btc_full_table_no_gaps(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    with db_env.session() as s:
        for i in range(3):
            _add_btc_hourly(s, start + timedelta(hours=i))
        s.commit()

    report = scan(TABLE_BTC, start, end)

    assert report.missing_count == 0
    assert report.materialization_count == 0
    assert report.raw_data_count == 0
    assert report.has_gaps is False


def test_scan_macro_full_table_no_gaps(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    with db_env.session() as s:
        for i in range(3):
            _add_macro_hourly(s, start + timedelta(hours=i))
        s.commit()

    report = scan(TABLE_MACRO, start, end)

    assert report.missing_count == 0
    assert report.has_gaps is False


# ======================================================================
# 3. Mixed BTC: ticks present -> MATERIALIZATION_GAP,
#    ticks absent -> RAW_DATA_GAP
# ======================================================================


def test_scan_btc_mixed_classification(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=4)
    with db_env.session() as s:
        # Hour 0: has ticks, no hourly row -> MATERIALIZATION_GAP
        _add_btc_tick(s, start + timedelta(minutes=30))
        # Hour 1: no ticks, no hourly row -> RAW_DATA_GAP
        # Hour 2: has ticks, no hourly row -> MATERIALIZATION_GAP
        _add_btc_tick(s, start + timedelta(hours=2, minutes=30))
        # Hour 3: has hourly row already -> not missing
        _add_btc_hourly(s, start + timedelta(hours=3))
        s.commit()

    report = scan(TABLE_BTC, start, end)

    assert report.expected_hours == 4
    assert report.actual_hours == 1
    assert report.missing_count == 3
    assert report.materialization_count == 2
    assert report.raw_data_count == 1

    by_hour = {m.hour: m.classification for m in report.missing_hours}
    assert by_hour[start] == GapClass.MATERIALIZATION_GAP
    assert by_hour[start + timedelta(hours=1)] == GapClass.RAW_DATA_GAP
    assert by_hour[start + timedelta(hours=2)] == GapClass.MATERIALIZATION_GAP


# ======================================================================
# 4. BTC asymmetry: prior tick does NOT make a later hour
#    MATERIALIZATION_GAP
# ======================================================================


def test_scan_btc_prior_tick_does_not_carry_forward(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=2)
    with db_env.session() as s:
        # Tick only in hour 0.
        _add_btc_tick(s, start + timedelta(minutes=30))
        s.commit()

    report = scan(TABLE_BTC, start, end)

    # Hour 0: has tick -> MATERIALIZATION_GAP
    # Hour 1: no tick -> RAW_DATA_GAP (NOT carried from hour 0)
    by_hour = {m.hour: m.classification for m in report.missing_hours}
    assert by_hour[start] == GapClass.MATERIALIZATION_GAP
    assert by_hour[start + timedelta(hours=1)] == GapClass.RAW_DATA_GAP


# ======================================================================
# 5. Macro asymmetry: prior observation DOES carry forward
# ======================================================================


def test_scan_macro_prior_observation_carries_forward(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    with db_env.session() as s:
        # Single observation at hour 0.
        _add_macro_raw(s, start + timedelta(minutes=30))
        s.commit()

    report = scan(TABLE_MACRO, start, end)

    # Hour 0, 1, 2 all have "time <= H" satisfied -> MATERIALIZATION_GAP
    by_hour = {m.hour: m.classification for m in report.missing_hours}
    assert by_hour[start] == GapClass.MATERIALIZATION_GAP
    assert by_hour[start + timedelta(hours=1)] == GapClass.MATERIALIZATION_GAP
    assert by_hour[start + timedelta(hours=2)] == GapClass.MATERIALIZATION_GAP


def test_scan_macro_hours_before_first_observation_are_raw_gaps(db_env):
    # The macro table's raw history starts at HOUR0. Ask about
    # an earlier range: those hours have no observation with
    # time <= H, so they are RAW_DATA_GAP.
    earlier_start = HOUR0 - timedelta(hours=2)
    end = HOUR0
    with db_env.session() as s:
        _add_macro_raw(s, HOUR0)
        s.commit()

    report = scan(TABLE_MACRO, earlier_start, end)

    assert report.missing_count == 2
    assert report.raw_data_count == 2
    assert report.materialization_count == 0


# ======================================================================
# 6. scan() is read-only
# ======================================================================


def test_scan_does_not_write(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    with db_env.session() as s:
        _add_btc_tick(s, start + timedelta(minutes=30))
        s.commit()

    scan(TABLE_BTC, start, end)

    with db_env.session() as s:
        n = s.execute(
            text("SELECT COUNT(*) FROM btc_prices_hourly")
        ).scalar_one()
    assert n == 0  # scan() wrote nothing


# ======================================================================
# 7. repair() only touches MATERIALIZATION_GAP
# ======================================================================


def test_repair_only_writes_materialization_gaps(db_env, monkeypatch):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    with db_env.session() as s:
        # Hour 0 has a tick -> MATERIALIZATION_GAP
        _add_btc_tick(s, start + timedelta(minutes=30))
        # Hour 1 has no tick -> RAW_DATA_GAP
        # Hour 2 has a tick -> MATERIALIZATION_GAP
        _add_btc_tick(s, start + timedelta(hours=2, minutes=30))
        s.commit()

    report = scan(TABLE_BTC, start, end)
    assert report.materialization_count == 2
    assert report.raw_data_count == 1

    # Spy on HourlyBTCPricesService.write_hour.
    calls: list[datetime] = []
    real_write = hbps.HourlyBTCPricesService.write_hour

    def spy_write(self, hour, dry_run=False):
        calls.append(hour)
        return real_write(self, hour, dry_run=dry_run)

    monkeypatch.setattr(hbps.HourlyBTCPricesService, "write_hour", spy_write)

    summary = repair(report)

    # Only the two MATERIALIZATION_GAP hours were written.
    assert sorted(calls) == [
        start,
        start + timedelta(hours=2),
    ]
    assert summary["attempted"] == 2
    assert summary["succeeded"] == 2
    assert summary["raw_gaps"] == 1
    assert summary["errors"] == 0


# ======================================================================
# 8. repair() summary shape
# ======================================================================


def test_repair_summary_shape(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    with db_env.session() as s:
        _add_btc_tick(s, start + timedelta(minutes=30))
        s.commit()

    report = scan(TABLE_BTC, start, end)
    summary = repair(report)

    assert set(summary.keys()) == {
        "attempted",
        "succeeded",
        "skipped",
        "raw_gaps",
        "errors",
    }
    assert summary["attempted"] == 1
    assert summary["succeeded"] == 1
    assert summary["raw_gaps"] == 0
    assert summary["errors"] == 0


# ======================================================================
# 9. suggested_commands()
# ======================================================================


def test_suggested_commands_btc_mentions_run_hourly_backfills(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    # No ticks, no hourly rows -> all RAW_DATA_GAP.

    report = scan(TABLE_BTC, start, end)
    cmds = "\n".join(report.suggested_commands())

    assert "run_hourly_backfills --btc" in cmds
    assert "verify_hourly_tables --table btc" in cmds


def test_suggested_commands_macro_mentions_run_backfills(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    # No macro rows -> all RAW_DATA_GAP.

    report = scan(TABLE_MACRO, start, end)
    cmds = "\n".join(report.suggested_commands())

    assert "run_backfills" in cmds
    # Must NOT suggest the gold backfill — macro table is FRED-sourced.
    assert "--gold" not in cmds
    assert "verify_hourly_tables --table macro" in cmds


def test_suggested_commands_empty_when_no_gaps(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    with db_env.session() as s:
        _add_btc_hourly(s, start)
        s.commit()

    report = scan(TABLE_BTC, start, end)
    assert report.suggested_commands() == []


# ======================================================================
# 10. Unsupported table name
# ======================================================================


def test_scan_unsupported_table_raises(db_env):
    with pytest.raises(ValueError, match="unsupported table"):
        scan("not_a_table", HOUR0, HOUR0 + timedelta(hours=1))


def test_repair_unsupported_table_raises(db_env):
    bogus = GapReport(
        table="not_a_table",
        start=HOUR0,
        end=HOUR0 + timedelta(hours=1),
        expected_hours=1,
        actual_hours=0,
        missing_count=1,
        materialization_count=1,
        raw_data_count=0,
        missing_hours=[
            MissingHour(hour=HOUR0, classification=GapClass.MATERIALIZATION_GAP)
        ],
    )
    with pytest.raises(ValueError, match="unsupported table"):
        repair(bogus)