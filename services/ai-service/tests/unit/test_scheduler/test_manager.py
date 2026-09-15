"""Unit tests for the SchedulerManager.

These tests exercise:
    - Setup: job registration
    - Start / shutdown lifecycle
    - The job wrapper: success, retry, final failure, history recording
    - Introspection methods

Lifecycle tests are async because APScheduler's AsyncIOScheduler
requires a running event loop to start.

Test organization:
    - TestManagerInit: constructor
    - TestManagerSetup: job registration
    - TestManagerStartStop: lifecycle + idempotency
    - TestJobWrapperSuccess: wrapper success path
    - TestJobWrapperRetry: retry behavior
    - TestJobWrapperFinalFailure: exhaustion behavior
    - TestManagerIntrospection: get_job_ids, get_next_run_time, is_running
"""

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from app.scheduler.manager import (
    JOB_ID_DAILY_7D_PREDICTION,
    JOB_ID_DAILY_ACCURACY,
    JOB_ID_DAILY_BACKTEST,
    JOB_ID_DAILY_CORRELATION,
    JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION,
    JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS,
    JOB_ID_DAILY_RETRAIN,
    JOB_ID_HOURLY_PREDICTION,
    SchedulerManager,
)
from app.scheduler.state import JobRunStatus, SchedulerState


# ============================================================
# INIT TESTS
# ============================================================
class TestManagerInit:
    """Tests for SchedulerManager construction."""

    def test_default_construction(self) -> None:
        """Test that the manager constructs with defaults."""
        manager = SchedulerManager(enabled=False)
        assert manager.enabled is False
        assert manager.state is not None
        assert manager.is_running() is False

    def test_state_override(self) -> None:
        """Test that a custom state instance is used."""
        state = SchedulerState(max_entries=5)
        manager = SchedulerManager(enabled=False, state=state)
        assert manager.state is state

    def test_repr(self) -> None:
        """Test __repr__ format."""
        manager = SchedulerManager(enabled=False)
        r = repr(manager)
        assert "SchedulerManager" in r
        assert "enabled=False" in r


# ============================================================
# SETUP TESTS
# ============================================================
class TestManagerSetup:
    """Tests for SchedulerManager.setup()."""

    def test_setup_registers_daily_retrain_job(self) -> None:
        """Test that setup registers the daily retrain job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert JOB_ID_DAILY_RETRAIN in manager.get_job_ids()
        finally:
            manager.shutdown()

    def test_setup_registers_hourly_job(self) -> None:
        """Test that setup registers the hourly 24h job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert JOB_ID_HOURLY_PREDICTION in manager.get_job_ids()
        finally:
            manager.shutdown()

    def test_setup_registers_daily_7d_job(self) -> None:
        """Test that setup registers the daily 7d job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert JOB_ID_DAILY_7D_PREDICTION in manager.get_job_ids()
        finally:
            manager.shutdown()

    def test_setup_registers_daily_backtest_job(self) -> None:
        """Test that setup registers the daily backtest job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert JOB_ID_DAILY_BACKTEST in manager.get_job_ids()
        finally:
            manager.shutdown()

    def test_setup_registers_daily_accuracy_job(self) -> None:
        """Test that setup registers the daily accuracy check job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert JOB_ID_DAILY_ACCURACY in manager.get_job_ids()
        finally:
            manager.shutdown()

    def test_setup_registers_daily_multi_model_predictions_job(self) -> None:
        """Test that setup registers the multi-model predictions job (M6b)."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert (
                JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS
                in manager.get_job_ids()
            )
        finally:
            manager.shutdown()

    def test_setup_registers_daily_model_performance_aggregation_job(
        self,
    ) -> None:
        """Test that setup registers the M7b aggregation job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert (
                JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION
                in manager.get_job_ids()
            )
        finally:
            manager.shutdown()

    def test_setup_registers_daily_correlation_job(self) -> None:
        """Test that setup registers the A1.5 correlation job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert (
                JOB_ID_DAILY_CORRELATION
                in manager.get_job_ids()
            )
        finally:
            manager.shutdown()

    def test_setup_registers_all_eight_jobs(self) -> None:
        """Test that setup registers exactly all eight jobs."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            ids = sorted(manager.get_job_ids())
            assert ids == sorted(
                [
                    JOB_ID_DAILY_RETRAIN,
                    JOB_ID_HOURLY_PREDICTION,
                    JOB_ID_DAILY_7D_PREDICTION,
                    JOB_ID_DAILY_BACKTEST,
                    JOB_ID_DAILY_ACCURACY,
                    JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS,
                    JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION,
                    JOB_ID_DAILY_CORRELATION,
                ]
            )
        finally:
            manager.shutdown()

    def test_setup_is_idempotent(self) -> None:
        """Test that calling setup twice doesn't duplicate jobs."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            first_ids = sorted(manager.get_job_ids())
            manager.setup()
            second_ids = sorted(manager.get_job_ids())
            assert first_ids == second_ids
        finally:
            manager.shutdown()


# ============================================================
# START / STOP TESTS
# ============================================================
class TestManagerStartStop:
    """Tests for start() and shutdown().

    All async because AsyncIOScheduler.start() requires a running loop.
    """

    @pytest.mark.asyncio
    async def test_start_when_disabled_is_noop(self) -> None:
        """Test that start() is a no-op when disabled."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        manager.start()
        assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_start_when_enabled_marks_running(self) -> None:
        """Test that start() marks the manager as running."""
        manager = SchedulerManager(enabled=True)
        try:
            manager.setup()
            manager.start()
            assert manager.is_running() is True
        finally:
            manager.shutdown()

    @pytest.mark.asyncio
    async def test_start_is_idempotent(self) -> None:
        """Test that calling start() twice doesn't error."""
        manager = SchedulerManager(enabled=True)
        try:
            manager.setup()
            manager.start()
            manager.start()  # second call is a no-op
            assert manager.is_running() is True
        finally:
            manager.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_stops_scheduler(self) -> None:
        """Test that shutdown() stops the scheduler."""
        manager = SchedulerManager(enabled=True)
        manager.setup()
        manager.start()
        manager.shutdown()
        assert manager.is_running() is False

    @pytest.mark.asyncio
    async def test_shutdown_is_idempotent(self) -> None:
        """Test that shutdown() can be called twice."""
        manager = SchedulerManager(enabled=True)
        manager.setup()
        manager.start()
        manager.shutdown()
        manager.shutdown()  # second call no-op
        assert manager.is_running() is False


# ============================================================
# JOB WRAPPER — SUCCESS
# ============================================================
class TestJobWrapperSuccess:
    """Tests for the job wrapper on the success path."""

    @pytest.mark.asyncio
    async def test_success_records_history(self) -> None:
        """Test that a successful run records a history entry."""
        manager = SchedulerManager(enabled=False)

        async def ok_job() -> Dict[str, Any]:
            return {"rows": 24}

        wrapped = manager._wrap_job("test_job", ok_job)
        await wrapped()

        assert len(manager.state) == 1
        record = manager.state.get_last_run()
        assert record.job_name == "test_job"
        assert record.status == JobRunStatus.SUCCESS
        assert record.result == {"rows": 24}
        assert record.error is None

    @pytest.mark.asyncio
    async def test_success_attempt_is_1(self) -> None:
        """Test that a successful first attempt has attempt=1."""
        manager = SchedulerManager(enabled=False)

        async def ok_job() -> Dict[str, Any]:
            return {}

        wrapped = manager._wrap_job("test_job", ok_job)
        await wrapped()

        record = manager.state.get_last_run()
        assert record.attempt == 1


# ============================================================
# JOB WRAPPER — RETRY
# ============================================================
class TestJobWrapperRetry:
    """Tests for the job wrapper's retry behavior."""

    @pytest.mark.asyncio
    async def test_success_on_retry(self, monkeypatch) -> None:
        """Test that a job succeeding on retry records RETRIED then SUCCESS."""
        from app.config import settings

        # Allow 1 retry (2 attempts total)
        monkeypatch.setattr(settings, "scheduler_max_retries", 1)

        manager = SchedulerManager(enabled=False)

        call_count = {"n": 0}

        async def flaky_job() -> Dict[str, Any]:
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise RuntimeError("transient failure")
            return {"rows": 24}

        wrapped = manager._wrap_job("flaky_job", flaky_job)
        await wrapped()

        # Two records: RETRIED (attempt 1) then SUCCESS (attempt 2)
        history = manager.state.get_history()
        assert len(history) == 2
        assert history[0].status == JobRunStatus.RETRIED
        assert history[0].attempt == 1
        assert history[1].status == JobRunStatus.SUCCESS
        assert history[1].attempt == 2

    @pytest.mark.asyncio
    async def test_no_retry_when_disabled(self, monkeypatch) -> None:
        """Test that scheduler_max_retries=0 disables retry."""
        from app.config import settings

        monkeypatch.setattr(settings, "scheduler_max_retries", 0)

        manager = SchedulerManager(enabled=False)

        async def always_fails() -> Dict[str, Any]:
            raise RuntimeError("permanent failure")

        wrapped = manager._wrap_job("fail_job", always_fails)
        await wrapped()

        # Single record: FAILED on attempt 1
        history = manager.state.get_history()
        assert len(history) == 1
        assert history[0].status == JobRunStatus.FAILED
        assert history[0].attempt == 1


# ============================================================
# JOB WRAPPER — FINAL FAILURE
# ============================================================
class TestJobWrapperFinalFailure:
    """Tests for the job wrapper when all attempts fail."""

    @pytest.mark.asyncio
    async def test_all_attempts_fail_records_failed(self, monkeypatch) -> None:
        """Test that exhausted retries record a FAILED entry."""
        from app.config import settings

        monkeypatch.setattr(settings, "scheduler_max_retries", 1)

        manager = SchedulerManager(enabled=False)

        async def always_fails() -> Dict[str, Any]:
            raise RuntimeError("always fails")

        wrapped = manager._wrap_job("fail_job", always_fails)
        await wrapped()

        history = manager.state.get_history()
        # RETRIED (attempt 1) then FAILED (attempt 2)
        assert len(history) == 2
        assert history[0].status == JobRunStatus.RETRIED
        assert history[1].status == JobRunStatus.FAILED
        assert history[1].error == "always fails"

    @pytest.mark.asyncio
    async def test_wrapper_does_not_raise(self, monkeypatch) -> None:
        """Test that the wrapper never re-raises — APScheduler stays healthy."""
        from app.config import settings

        monkeypatch.setattr(settings, "scheduler_max_retries", 0)

        manager = SchedulerManager(enabled=False)

        async def always_fails() -> Dict[str, Any]:
            raise RuntimeError("boom")

        wrapped = manager._wrap_job("fail_job", always_fails)
        # Should not raise even though the job does
        await wrapped()

        assert manager.state.get_stats()["total_failures"] == 1


# ============================================================
# INTROSPECTION TESTS
# ============================================================
class TestManagerIntrospection:
    """Tests for introspection methods."""

    def test_get_job_ids_before_setup(self) -> None:
        """Test that get_job_ids returns [] before setup."""
        manager = SchedulerManager(enabled=False)
        assert manager.get_job_ids() == []

    def test_get_job_ids_after_setup(self) -> None:
        """Test that get_job_ids returns all registered jobs after setup."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            ids = manager.get_job_ids()
            assert JOB_ID_DAILY_RETRAIN in ids
            assert JOB_ID_HOURLY_PREDICTION in ids
            assert JOB_ID_DAILY_7D_PREDICTION in ids
            assert JOB_ID_DAILY_BACKTEST in ids
            assert JOB_ID_DAILY_ACCURACY in ids
            assert JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS in ids
            assert (
                JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION in ids
            )
            assert JOB_ID_DAILY_CORRELATION in ids
        finally:
            manager.shutdown()

    def test_get_next_run_time_before_setup(self) -> None:
        """Test that get_next_run_time returns None before setup."""
        manager = SchedulerManager(enabled=False)
        assert manager.get_next_run_time("anything") is None

    def test_get_next_run_time_unknown_job(self) -> None:
        """Test that get_next_run_time returns None for an unknown job."""
        manager = SchedulerManager(enabled=False)
        manager.setup()
        try:
            assert manager.get_next_run_time("does_not_exist") is None
        finally:
            manager.shutdown()

    def test_is_running_false_before_start(self) -> None:
        """Test that is_running is False before start()."""
        manager = SchedulerManager(enabled=False)
        assert manager.is_running() is False