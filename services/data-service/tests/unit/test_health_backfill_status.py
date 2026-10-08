"""
Tests for the backfill_status field added to /health.

Uses FastAPI's TestClient. The actual health_check endpoint calls
into the module-level backfill_service singleton, so we mutate
that directly to simulate the states.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import backfill_service as bs


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_status():
    bs._status.state = "idle"
    bs._status.current_source = None
    bs._status.error = None
    bs._status.started_at = None
    bs._status.completed_at = None
    bs._status.sources_run = 0
    bs._status.sources_skipped = 0
    yield


def test_health_includes_idle_backfill_status(client):
    r = client.get("/health")
    assert r.status_code == 200

    body = r.json()
    assert "backfill_status" in body
    assert body["backfill_status"]["state"] == "idle"
    assert body["backfill_status"]["current_source"] is None
    assert body["backfill_status"]["error"] is None
    assert body["backfill_status"]["sources_run"] == 0
    assert body["backfill_status"]["sources_skipped"] == 0


def test_health_reflects_running_backfill(client):
    bs._status.state = "running"
    bs._status.current_source = "btc_prices"
    bs._status.started_at = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)

    r = client.get("/health")
    body = r.json()

    assert body["backfill_status"]["state"] == "running"
    assert body["backfill_status"]["current_source"] == "btc_prices"
    assert body["backfill_status"]["started_at"] == "2026-10-06T12:00:00+00:00"


def test_health_reflects_failed_backfill(client):
    bs._status.state = "failed"
    bs._status.current_source = "fred_indicators"
    bs._status.error = "HTTP 503 from FRED"
    bs._status.completed_at = datetime(2026, 10, 6, 12, 5, 0, tzinfo=timezone.utc)

    r = client.get("/health")
    body = r.json()

    assert body["backfill_status"]["state"] == "failed"
    assert body["backfill_status"]["error"] == "HTTP 503 from FRED"
    assert body["backfill_status"]["current_source"] == "fred_indicators"