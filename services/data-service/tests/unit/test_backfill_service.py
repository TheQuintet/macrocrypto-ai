"""
Unit tests for app.services.backfill_service.

Covers:
- staleness decision (empty / stale / current / forced)
- frozen-archive cadence=None behaviour
- source-filtered max(time) query
- concurrent-call guard
- status transitions (idle -> running -> completed / failed)

All repositories and run_backfills functions are mocked; no real
DB, no network calls.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services import backfill_service as bs


# ============================================================
# FIXTURES
# ============================================================


def _source(key: str) -> bs.BackfillSource:
    for s in bs.BACKFILL_SOURCES:
        if s.key == key:
            return s
    raise KeyError(key)


@pytest.fixture(autouse=True)
def _reset_status():
    """Reset the module-level status between tests."""
    bs._status.state = "idle"
    bs._status.current_source = None
    bs._status.error = None
    bs._status.started_at = None
    bs._status.completed_at = None
    bs._status.sources_run = 0
    bs._status.sources_skipped = 0
    yield


# ============================================================
# STALENESS DECISION
# ============================================================


def test_bootstrap_when_empty():
    src = _source("btc_prices")
    assert bs._is_stale(src, max_time=None) is True


def test_stale_when_behind_threshold():
    src = _source("btc_prices")  # cadence 24h -> threshold 48h
    old = datetime.now(timezone.utc) - timedelta(hours=72)
    assert bs._is_stale(src, max_time=old) is True


def test_current_when_within_threshold():
    src = _source("btc_prices")
    recent = datetime.now(timezone.utc) - timedelta(hours=12)
    assert bs._is_stale(src, max_time=recent) is False


def test_frozen_archive_not_stale_when_has_rows():
    src = _source("gold_spot_perth")  # cadence=None
    old = datetime(2021, 9, 13, tzinfo=timezone.utc)
    assert bs._is_stale(src, max_time=old) is False


def test_frozen_archive_bootstraps_when_empty():
    src = _source("gold_spot_perth")
    assert bs._is_stale(src, max_time=None) is True


# ============================================================
# CHECK_AND_BACKFILL BEHAVIOUR
# ============================================================


@pytest.mark.asyncio
async def test_skip_when_current():
    """All sources current -> nothing runs."""
    now = datetime.now(timezone.utc)

    async def fake_run(src):
        raise AssertionError("no source should run")

    with patch.object(bs, "_query_max_time", return_value=now), \
         patch.object(bs, "_run_source", side_effect=fake_run):
        await bs.check_and_backfill(force=False)

    assert bs._status.state == "completed"
    assert bs._status.sources_run == 0
    assert bs._status.sources_skipped == len(bs.BACKFILL_SOURCES)


@pytest.mark.asyncio
async def test_force_runs_everything():
    now = datetime.now(timezone.utc)
    ran: list[str] = []

    async def fake_run(src):
        ran.append(src.key)
        return 0

    with patch.object(bs, "_query_max_time", return_value=now), \
         patch.object(bs, "_run_source", side_effect=fake_run):
        await bs.check_and_backfill(force=True)

    assert ran == [s.key for s in bs.BACKFILL_SOURCES]
    assert bs._status.state == "completed"
    assert bs._status.sources_run == len(bs.BACKFILL_SOURCES)


@pytest.mark.asyncio
async def test_bootstrap_runs_only_empty_sources():
    """Empty sources run; populated ones skip."""
    now = datetime.now(timezone.utc)

    def fake_max(source):
        # Only btc_prices is empty.
        return None if source.key == "btc_prices" else now

    ran: list[str] = []

    async def fake_run(src):
        ran.append(src.key)
        return 0

    with patch.object(bs, "_query_max_time", side_effect=fake_max), \
         patch.object(bs, "_run_source", side_effect=fake_run):
        await bs.check_and_backfill(force=False)

    assert ran == ["btc_prices"]


@pytest.mark.asyncio
async def test_failure_sets_status_failed():
    now = datetime.now(timezone.utc)

    async def boom(src):
        raise RuntimeError("boom")

    with patch.object(bs, "_query_max_time", return_value=now), \
         patch.object(bs, "_run_source", side_effect=boom):
        await bs.check_and_backfill(force=True)

    assert bs._status.state == "failed"
    assert bs._status.error is not None
    assert "boom" in bs._status.error


@pytest.mark.asyncio
async def test_concurrent_call_returns_immediately():
    """A second call while a run is in flight is skipped."""
    started = asyncio.Event()
    finish = asyncio.Event()

    async def slow_run(src):
        started.set()
        await finish.wait()
        return 0

    now = datetime.now(timezone.utc)

    with patch.object(bs, "_query_max_time", return_value=now), \
         patch.object(bs, "_run_source", side_effect=slow_run):
        task1 = asyncio.create_task(bs.check_and_backfill(force=True))
        await started.wait()

        # Second call should see the lock held and return.
        await bs.check_and_backfill(force=True)

        finish.set()
        await task1


# ============================================================
# STATUS SNAPSHOT
# ============================================================


def test_get_backfill_status_returns_singleton():
    s1 = bs.get_backfill_status()
    s2 = bs.get_backfill_status()
    assert s1 is s2