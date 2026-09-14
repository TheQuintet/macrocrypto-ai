"""Unit tests for the scheduler state module.

Test organization:
    - TestJobRunStatus: enum values
    - TestJobRunRecord: dataclass behavior + to_dict
    - TestSchedulerStateInit: constructor validation
    - TestSchedulerStateRecord: recording + counters
    - TestSchedulerStateRead: history, recent, last_run, stats
    - TestSchedulerStateClear: reset behavior
    - TestSchedulerStateBounded: ring buffer eviction
"""

from datetime import datetime, timezone

import pytest

from app.scheduler.state import (
    JobRunRecord,
    JobRunStatus,
    SchedulerState,
)


# ============================================================
# HELPERS
# ============================================================
def _make_record(
    job_name: str = "hourly_prediction",
    status: JobRunStatus = JobRunStatus.SUCCESS,
    attempt: int = 1,
    error: str = None,
    result: dict = None,
) -> JobRunRecord:
    """Build a JobRunRecord for tests."""
    started = datetime.now(timezone.utc)
    return JobRunRecord(
        job_name=job_name,
        started_at=started,
        finished_at=started,
        duration_seconds=0.1,
        status=status,
        attempt=attempt,
        result=result,
        error=error,
    )


# ============================================================
# ENUM TESTS
# ============================================================
class TestJobRunStatus:
    """Tests for the JobRunStatus enum."""

    def test_values(self) -> None:
        """Test that all three statuses exist."""
        assert JobRunStatus.SUCCESS.value == "success"
        assert JobRunStatus.FAILED.value == "failed"
        assert JobRunStatus.RETRIED.value == "retried"

    def test_is_str_enum(self) -> None:
        """Test that JobRunStatus subclasses str (JSON-friendly)."""
        assert isinstance(JobRunStatus.SUCCESS, str)
        assert JobRunStatus.SUCCESS == "success"


# ============================================================
# RECORD TESTS
# ============================================================
class TestJobRunRecord:
    """Tests for the JobRunRecord dataclass."""

    def test_default_construction(self) -> None:
        """Test defaults."""
        now = datetime.now(timezone.utc)
        record = JobRunRecord(job_name="x", started_at=now)
        assert record.job_name == "x"
        assert record.started_at == now
        assert record.finished_at is None
        assert record.duration_seconds == 0.0
        assert record.status == JobRunStatus.SUCCESS
        assert record.attempt == 1
        assert record.result is None
        assert record.error is None

    def test_to_dict_serializes_datetimes(self) -> None:
        """Test that datetimes are serialized to ISO strings."""
        record = _make_record()
        d = record.to_dict()
        assert isinstance(d["started_at"], str)
        assert isinstance(d["finished_at"], str)
        assert d["status"] == "success"

    def test_to_dict_none_finished_at(self) -> None:
        """Test that None finished_at serializes to None."""
        now = datetime.now(timezone.utc)
        record = JobRunRecord(job_name="x", started_at=now)
        d = record.to_dict()
        assert d["finished_at"] is None

    def test_repr(self) -> None:
        """Test __repr__ format."""
        record = _make_record()
        r = repr(record)
        assert "hourly_prediction" in r
        assert "status='success'" in r


# ============================================================
# INIT TESTS
# ============================================================
class TestSchedulerStateInit:
    """Tests for SchedulerState construction."""

    def test_default_construction(self) -> None:
        """Test that default max_entries=100."""
        state = SchedulerState()
        assert state.max_entries == 100
        assert len(state) == 0

    def test_custom_max_entries(self) -> None:
        """Test that max_entries is configurable."""
        state = SchedulerState(max_entries=5)
        assert state.max_entries == 5

    def test_zero_max_entries_raises(self) -> None:
        """Test that max_entries=0 raises ValueError."""
        with pytest.raises(ValueError, match="max_entries must be positive"):
            SchedulerState(max_entries=0)

    def test_negative_max_entries_raises(self) -> None:
        """Test that a negative max_entries raises ValueError."""
        with pytest.raises(ValueError, match="max_entries must be positive"):
            SchedulerState(max_entries=-1)

    def test_repr(self) -> None:
        """Test __repr__ format."""
        state = SchedulerState(max_entries=10)
        assert "history=0/10" in repr(state)


# ============================================================
# RECORD TESTS
# ============================================================
class TestSchedulerStateRecord:
    """Tests for SchedulerState.record()."""

    def test_record_appends_entry(self) -> None:
        """Test that recording adds an entry to history."""
        state = SchedulerState()
        state.record(_make_record())
        assert len(state) == 1

    def test_record_multiple_entries(self) -> None:
        """Test that multiple records accumulate."""
        state = SchedulerState()
        for _ in range(5):
            state.record(_make_record())
        assert len(state) == 5

    def test_record_updates_total_runs(self) -> None:
        """Test that total_runs counter increments."""
        state = SchedulerState()
        state.record(_make_record())
        state.record(_make_record())
        assert state.get_stats()["total_runs"] == 2

    def test_record_counts_successes(self) -> None:
        """Test that successes are counted."""
        state = SchedulerState()
        state.record(_make_record(status=JobRunStatus.SUCCESS))
        state.record(_make_record(status=JobRunStatus.SUCCESS))
        stats = state.get_stats()
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 0

    def test_record_counts_failures(self) -> None:
        """Test that failures are counted."""
        state = SchedulerState()
        state.record(_make_record(status=JobRunStatus.FAILED))
        stats = state.get_stats()
        assert stats["total_failures"] == 1
        assert stats["total_successes"] == 0

    def test_retried_status_not_counted_as_success_or_failure(self) -> None:
        """Test that RETRIED entries aren't counted as success/failure."""
        state = SchedulerState()
        state.record(_make_record(status=JobRunStatus.RETRIED))
        stats = state.get_stats()
        assert stats["total_successes"] == 0
        assert stats["total_failures"] == 0
        assert stats["total_runs"] == 1


# ============================================================
# READ TESTS
# ============================================================
class TestSchedulerStateRead:
    """Tests for read methods."""

    def test_get_history_empty(self) -> None:
        """Test that an empty state returns an empty list."""
        state = SchedulerState()
        assert state.get_history() == []

    def test_get_history_returns_list(self) -> None:
        """Test that get_history returns a list in insertion order."""
        state = SchedulerState()
        for i in range(3):
            state.record(_make_record(job_name=f"job_{i}"))
        history = state.get_history()
        assert [r.job_name for r in history] == ["job_0", "job_1", "job_2"]

    def test_get_recent_returns_last_n(self) -> None:
        """Test that get_recent returns the most recent N records."""
        state = SchedulerState()
        for i in range(5):
            state.record(_make_record(job_name=f"job_{i}"))
        recent = state.get_recent(limit=2)
        assert [r.job_name for r in recent] == ["job_3", "job_4"]

    def test_get_recent_filters_by_job_name(self) -> None:
        """Test that get_recent filters by job_name."""
        state = SchedulerState()
        state.record(_make_record(job_name="a"))
        state.record(_make_record(job_name="b"))
        state.record(_make_record(job_name="a"))
        recent = state.get_recent(job_name="a", limit=10)
        assert len(recent) == 2

    def test_get_last_run_returns_latest(self) -> None:
        """Test that get_last_run returns the most recent record."""
        state = SchedulerState()
        state.record(_make_record(job_name="a"))
        state.record(_make_record(job_name="b"))
        last = state.get_last_run()
        assert last.job_name == "b"

    def test_get_last_run_filtered(self) -> None:
        """Test that get_last_run respects job_name."""
        state = SchedulerState()
        state.record(_make_record(job_name="a"))
        state.record(_make_record(job_name="b"))
        state.record(_make_record(job_name="a"))
        last = state.get_last_run(job_name="a")
        assert last.job_name == "a"

    def test_get_last_run_empty(self) -> None:
        """Test that get_last_run returns None on empty state."""
        state = SchedulerState()
        assert state.get_last_run() is None

    def test_get_stats_shape(self) -> None:
        """Test that get_stats returns the expected keys."""
        state = SchedulerState()
        stats = state.get_stats()
        assert set(stats.keys()) == {
            "total_runs",
            "total_successes",
            "total_failures",
            "history_size",
        }


# ============================================================
# CLEAR TESTS
# ============================================================
class TestSchedulerStateClear:
    """Tests for SchedulerState.clear()."""

    def test_clear_removes_history(self) -> None:
        """Test that clear removes all history."""
        state = SchedulerState()
        state.record(_make_record())
        state.clear()
        assert len(state) == 0

    def test_clear_resets_counters(self) -> None:
        """Test that clear resets all counters."""
        state = SchedulerState()
        state.record(_make_record(status=JobRunStatus.SUCCESS))
        state.record(_make_record(status=JobRunStatus.FAILED))
        state.clear()
        stats = state.get_stats()
        assert stats["total_runs"] == 0
        assert stats["total_successes"] == 0
        assert stats["total_failures"] == 0


# ============================================================
# BOUNDED TESTS
# ============================================================
class TestSchedulerStateBounded:
    """Tests for the ring buffer max_entries behavior."""

    def test_exceeding_max_entries_evicts_oldest(self) -> None:
        """Test that old entries fall off when max_entries is exceeded."""
        state = SchedulerState(max_entries=3)
        for i in range(5):
            state.record(_make_record(job_name=f"job_{i}"))
        history = state.get_history()
        assert len(history) == 3
        assert [r.job_name for r in history] == ["job_2", "job_3", "job_4"]

    def test_totals_unaffected_by_eviction(self) -> None:
        """Test that eviction does not decrement total counters."""
        state = SchedulerState(max_entries=2)
        for _ in range(5):
            state.record(_make_record(status=JobRunStatus.SUCCESS))
        stats = state.get_stats()
        assert stats["total_runs"] == 5
        assert stats["total_successes"] == 5
        assert stats["history_size"] == 2