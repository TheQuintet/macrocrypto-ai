"""
CLI-level tests for hourly gap verification (Chat 4, C4-2).

Two entry points:

  1. app/scripts/verify_hourly_tables.py  (new top-level CLI)
  2. app/scripts/run_live_path.py --verify-hourly --table ...

Both are thin wrappers over gap_detection_service. These tests
build synthetic DB state and assert on exit codes + stdout.

These tests do NOT exercise real Binance, Yahoo, or Postgres.

Coverage:
  1. verify_hourly_tables: exit 0 when no gaps.
  2. verify_hourly_tables: exit 1 when gaps exist (no --repair).
  3. verify_hourly_tables: exit 1 with --repair that succeeds.
  4. verify_hourly_tables: exit 3 when --repair raises.
  5. verify_hourly_tables: exit 2 on invalid range.
  6. verify_hourly_tables: exit 2 on non-positive --days.
  7. verify_hourly_tables: --table all dispatches both tables.
  8. verify_hourly_tables: exit 2 on empty range (start == end).
  9. run_live_path --verify-hourly: exit 2 when --table missing.
 10. run_live_path --verify-hourly: exit 1 when gaps exist.
 11. run_live_path --verify-hourly: exit 0 when no gaps.
 12. run_live_path --verify-hourly: exit 1 with --repair that
     succeeds (gaps were found, repair doesn't change exit).
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

from app.scripts import verify_hourly_tables as vht_cli
from app.scripts import run_live_path as live_cli


# Fixed reference time. All ranges are anchored here so tests do
# not depend on wall clock. Each CLI computes `now()` internally
# only when --days is used; all tests below pass --start/--end.
HOUR0 = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


# ======================================================================
# FIXTURE
# ======================================================================


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    """
    Same shape as test_gap_detection_service's fixture. Patches
    SessionLocal in every module the service+repositories touch.
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


def _add_btc_hourly(session, dt: datetime):
    session.execute(
        text(
            "INSERT INTO btc_prices_hourly (time, close) "
            "VALUES (:t, 100.0)"
        ),
        {"t": dt},
    )


def _add_btc_tick(session, dt: datetime):
    session.execute(
        text(
            "INSERT INTO btc_prices (time, price, source) "
            "VALUES (:t, 100.0, 'binance')"
        ),
        {"t": dt},
    )


def _run_vht(argv: list[str]) -> int:
    """Call verify_hourly_tables.main with an explicit argv."""
    return vht_cli.main(argv)


def _run_live(argv: list[str]) -> int:
    """Call run_live_path.main with an explicit argv."""
    return live_cli.main(argv)


# ======================================================================
# verify_hourly_tables — exit codes
# ======================================================================


def test_vht_exit_0_when_no_gaps(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    with db_env.session() as s:
        for i in range(3):
            _add_btc_hourly(s, start + timedelta(hours=i))
        s.commit()

    rc = _run_vht([
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
    ])
    assert rc == 0


def test_vht_exit_1_when_gaps_exist_without_repair(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=3)
    # No hourly rows at all -> 3 missing.
    with db_env.session() as s:
        # Provide raw ticks so they classify as MATERIALIZATION_GAP
        # (avoids external fetches from --repair in later tests).
        for i in range(3):
            _add_btc_tick(s, start + timedelta(hours=i, minutes=30))
        s.commit()

    rc = _run_vht([
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
    ])
    assert rc == 1


def test_vht_exit_1_when_gaps_exist_with_successful_repair(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=2)
    with db_env.session() as s:
        for i in range(2):
            _add_btc_tick(s, start + timedelta(hours=i, minutes=30))
        s.commit()

    rc = _run_vht([
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
        "--repair",
    ])
    # Gaps were found, even though repair fixed them. Exit 1.
    assert rc == 1

    # Confirm repair actually wrote rows.
    with db_env.session() as s:
        n = s.execute(
            text("SELECT COUNT(*) FROM btc_prices_hourly")
        ).scalar_one()
    assert n == 2


def test_vht_exit_3_when_repair_raises(db_env, monkeypatch):
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    with db_env.session() as s:
        _add_btc_tick(s, start + timedelta(minutes=30))
        s.commit()

    def boom(report):
        raise RuntimeError("simulated repair failure")

    # Patch in the CLI module (it imports repair as repair_gaps).
    monkeypatch.setattr(vht_cli, "repair_gaps", boom)

    rc = _run_vht([
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
        "--repair",
    ])
    assert rc == 3


def test_vht_exit_2_on_invalid_range(db_env):
    # --end before --start.
    rc = _run_vht([
        "--table", "btc",
        "--start", "2026-01-15T12:00:00",
        "--end", "2026-01-15T11:00:00",
    ])
    assert rc == 2


def test_vht_exit_2_on_nonpositive_days(db_env):
    rc = _run_vht(["--table", "btc", "--days", "0"])
    assert rc == 2


def test_vht_table_all_scans_both(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    # BTC: one hourly row -> no gaps.
    # Macro: no hourly row -> one gap.
    with db_env.session() as s:
        _add_btc_hourly(s, start)
        s.commit()

    rc = _run_vht([
        "--table", "all",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
    ])
    # Macro has a gap -> exit 1.
    assert rc == 1


def test_vht_empty_range_returns_2(db_env):
    # start == end -> invalid range -> CLI returns 2.
    start = HOUR0
    rc = _run_vht([
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", start.isoformat(),
    ])
    assert rc == 2


# ======================================================================
# run_live_path --verify-hourly
# ======================================================================


def test_live_verify_hourly_exit_2_when_table_missing(db_env):
    # --verify-hourly without --table -> handler early return.
    rc = _run_live([
        "--verify-hourly",
        "--days", "1",
    ])
    assert rc == 2


def test_live_verify_hourly_exit_1_when_gaps_exist(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=2)
    # No hourly rows, no raw rows -> 2 gaps (RAW_DATA_GAP).

    rc = _run_live([
        "--verify-hourly",
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
    ])
    assert rc == 1


def test_live_verify_hourly_exit_0_when_no_gaps(db_env):
    start = HOUR0
    end = HOUR0 + timedelta(hours=2)
    with db_env.session() as s:
        for i in range(2):
            _add_btc_hourly(s, start + timedelta(hours=i))
        s.commit()

    rc = _run_live([
        "--verify-hourly",
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
    ])
    assert rc == 0


def test_live_verify_hourly_exit_1_with_repair(db_env):
    # Gaps exist and repair succeeds -> still exit 1.
    start = HOUR0
    end = HOUR0 + timedelta(hours=1)
    with db_env.session() as s:
        _add_btc_tick(s, start + timedelta(minutes=30))
        s.commit()

    rc = _run_live([
        "--verify-hourly",
        "--table", "btc",
        "--start", start.isoformat(),
        "--end", end.isoformat(),
        "--repair",
    ])
    assert rc == 1

    with db_env.session() as s:
        n = s.execute(
            text("SELECT COUNT(*) FROM btc_prices_hourly")
        ).scalar_one()
    assert n == 1