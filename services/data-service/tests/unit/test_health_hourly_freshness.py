"""
Tests for /health's hourly_freshness field (Chat 4, C4-3).

Covers the local helper _freshness_for(table) and the
hourly_freshness block it produces on the /health response.

These tests do NOT exercise real Postgres. app.main.engine is
patched to a SQLite test engine.

Coverage:
  1. fresh when newest row is recent.
  2. stale when newest row is > 3h behind.
  3. unknown when the table is empty.
  4. unknown when the DB query raises.
  5. Boundary: exactly 3h behind -> fresh.
  6. Boundary: 3h59m59s behind -> fresh (floor to hours).
  7. Boundary: 4h00m01s behind -> stale.
  8. Both tables reported independently.
  9. /health response includes hourly_freshness with expected shape.
 10. /health response reports fresh on both tables when both fresh.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

import app.main as main_module
from app.main import _freshness_for


# ======================================================================
# FIXTURE
# ======================================================================


@pytest.fixture
def db_env(tmp_path, monkeypatch):
    """
    Build a SQLite DB with the two hourly tables and patch
    app.main.engine to point at it.

    Also stubs the module-level globals /health reads so the
    route can render without a running service.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")

    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE btc_prices_hourly (
                time TIMESTAMP PRIMARY KEY,
                close REAL
            )
            """
        ))
        conn.execute(text(
            """
            CREATE TABLE macro_indicators_hourly (
                time TIMESTAMP PRIMARY KEY,
                cpi REAL
            )
            """
        ))

    monkeypatch.setattr(main_module, "engine", engine)

    # Neutralize /health's other dependencies so the route can
    # render. The tests only assert on hourly_freshness.
    monkeypatch.setattr(main_module, "btc_task", None)
    monkeypatch.setattr(main_module, "cache_client", None)
    monkeypatch.setattr(main_module, "rabbitmq_producer", None)
    monkeypatch.setattr(main_module, "price_service", None)
    monkeypatch.setattr(main_module, "data_processor", None)

    class Env:
        def __init__(self):
            self.engine = engine

        def session(self):
            return engine.connect()

        def insert_btc(self, dt: datetime):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO btc_prices_hourly (time, close) "
                        "VALUES (:t, 100.0)"
                    ),
                    {"t": dt},
                )

        def insert_macro(self, dt: datetime):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO macro_indicators_hourly (time) "
                        "VALUES (:t)"
                    ),
                    {"t": dt},
                )

    yield Env()
    engine.dispose()


def _hours_ago(hours: float) -> datetime:
    """A tz-aware UTC datetime that is `hours` before now."""
    return datetime.now(timezone.utc) - timedelta(hours=hours)


# ======================================================================
# 1-2. Basic fresh / stale
# ======================================================================


def test_freshness_fresh_when_recent(db_env):
    db_env.insert_btc(_hours_ago(1))

    report = _freshness_for("btc_prices_hourly")

    assert report["status"] == "fresh"
    assert report["hours_behind"] == 1
    assert report["latest_hour"] is not None


def test_freshness_stale_when_old(db_env):
    db_env.insert_btc(_hours_ago(5))

    report = _freshness_for("btc_prices_hourly")

    assert report["status"] == "stale"
    assert report["hours_behind"] == 5


# ======================================================================
# 3. Empty table
# ======================================================================


def test_freshness_unknown_when_empty(db_env):
    report = _freshness_for("btc_prices_hourly")

    assert report["status"] == "unknown"
    assert report["latest_hour"] is None
    assert report["hours_behind"] is None


# ======================================================================
# 4. DB error -> unknown
# ======================================================================


def test_freshness_unknown_when_query_raises(db_env, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("simulated DB failure")

    # Replace the engine with a stand-in whose connect() raises.
    class FailingEngine:
        def connect(self):
            raise RuntimeError("simulated DB failure")

    monkeypatch.setattr(main_module, "engine", FailingEngine())

    with caplog.at_level(logging.ERROR):
        report = _freshness_for("btc_prices_hourly")

    assert report["status"] == "unknown"
    assert report["latest_hour"] is None
    assert report["hours_behind"] is None
    # The failure was logged, not swallowed silently.
    assert any(
        "Hourly freshness query failed" in r.message
        for r in caplog.records
    )


# ======================================================================
# 5-7. Boundary behavior (documents the //3600 floor)
# ======================================================================


def test_freshness_exactly_3h_fresh(db_env):
    # 3h00m00s behind -> hours_behind=3 -> 3 > 3 is False -> fresh
    db_env.insert_btc(_hours_ago(3))

    report = _freshness_for("btc_prices_hourly")

    assert report["hours_behind"] == 3
    assert report["status"] == "fresh"


def test_freshness_just_under_4h_fresh(db_env):
    # 3h59m59s behind -> floored to 3 -> fresh
    db_env.insert_btc(_hours_ago(3 + 59 / 60 + 59 / 3600))

    report = _freshness_for("btc_prices_hourly")

    assert report["hours_behind"] == 3
    assert report["status"] == "fresh"


def test_freshness_just_over_4h_stale(db_env):
    # 4h00m01s behind -> floored to 4 -> 4 > 3 -> stale
    db_env.insert_btc(_hours_ago(4 + 1 / 3600))

    report = _freshness_for("btc_prices_hourly")

    assert report["hours_behind"] == 4
    assert report["status"] == "stale"


# ======================================================================
# 8. Independence of the two tables
# ======================================================================


def test_both_tables_reported_independently(db_env):
    db_env.insert_btc(_hours_ago(1))    # fresh
    db_env.insert_macro(_hours_ago(10))  # stale

    btc = _freshness_for("btc_prices_hourly")
    macro = _freshness_for("macro_indicators_hourly")

    assert btc["status"] == "fresh"
    assert macro["status"] == "stale"
    assert macro["hours_behind"] == 10


# ======================================================================
# 9-10. /health integration
# ======================================================================


def test_health_includes_hourly_freshness(db_env):
    client = TestClient(main_module.app)

    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert "hourly_freshness" in body
    hf = body["hourly_freshness"]
    assert set(hf.keys()) == {
        "btc_prices_hourly",
        "macro_indicators_hourly",
    }
    for table_report in hf.values():
        assert set(table_report.keys()) == {
            "latest_hour",
            "hours_behind",
            "status",
        }
        assert table_report["status"] in {"fresh", "stale", "unknown"}


def test_health_reports_fresh_when_both_recent(db_env):
    db_env.insert_btc(_hours_ago(1))
    db_env.insert_macro(_hours_ago(2))

    client = TestClient(main_module.app)
    body = client.get("/health").json()

    hf = body["hourly_freshness"]
    assert hf["btc_prices_hourly"]["status"] == "fresh"
    assert hf["btc_prices_hourly"]["hours_behind"] == 1
    assert hf["macro_indicators_hourly"]["status"] == "fresh"
    assert hf["macro_indicators_hourly"]["hours_behind"] == 2