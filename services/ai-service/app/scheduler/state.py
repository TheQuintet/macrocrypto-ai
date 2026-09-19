"""In-memory state for the scheduler.

Tracks recent job runs in a bounded ring buffer. Each run record
captures the job name, timestamps, duration, status, result summary,
and error (if any).

Design:
    - Bounded deque (maxlen configurable) — old entries fall off
    - Records are plain dataclasses, easily serialized for logging
      or a future /health/scheduler endpoint
    - Thread-safe-enough: APScheduler runs jobs on the event loop,
      and Python's GIL protects deque operations. If we ever add
      multi-threaded execution, we'd wrap this with a lock.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS
# ============================================================
class JobRunStatus(str, Enum):
    """Status of a single job run."""

    SUCCESS = "success"
    FAILED = "failed"
    RETRIED = "retried"


# ============================================================
# RUN RECORD
# ============================================================
@dataclass
class JobRunRecord:
    """A single job run record.

    Attributes:
        job_name: Identifier of the job (e.g. 'hourly_prediction').
        started_at: When the run started (UTC).
        finished_at: When the run finished (UTC).
        duration_seconds: Wall-clock duration.
        status: JobRunStatus value.
        attempt: Which attempt this was (1 = first, 2 = retry).
        result: Optional structured result (e.g. GenerationResult dict).
        error: Error message if the run failed.
    """

    job_name: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    status: JobRunStatus = JobRunStatus.SUCCESS
    attempt: int = 1
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "job_name": self.job_name,
            "started_at": self.started_at.isoformat(),
            "finished_at": (
                self.finished_at.isoformat() if self.finished_at else None
            ),
            "duration_seconds": self.duration_seconds,
            "status": self.status.value,
            "attempt": self.attempt,
            "result": self.result,
            "error": self.error,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"JobRunRecord(job_name='{self.job_name}', "
            f"status='{self.status.value}', "
            f"attempt={self.attempt}, "
            f"duration={self.duration_seconds:.3f}s)"
        )


# ============================================================
# SCHEDULER STATE
# ============================================================
class SchedulerState:
    """Bounded in-memory history of scheduler job runs.

    Attributes:
        max_entries: Maximum number of run records to retain.
    """

    def __init__(self, max_entries: int = 100) -> None:
        """Initialize the state.

        Args:
            max_entries: Maximum number of run records to retain.
                Older entries are discarded as new ones arrive.
        """
        if max_entries <= 0:
            raise ValueError(
                f"max_entries must be positive, got {max_entries}"
            )

        self.max_entries = max_entries
        self._history: Deque[JobRunRecord] = deque(maxlen=max_entries)
        self._total_runs: int = 0
        self._total_successes: int = 0
        self._total_failures: int = 0

    # ============================================================
    # WRITE
    # ============================================================
    def record(self, record: JobRunRecord) -> None:
        """Append a run record to the history.

        Args:
            record: The JobRunRecord to store.
        """
        self._history.append(record)
        self._total_runs += 1

        if record.status == JobRunStatus.SUCCESS:
            self._total_successes += 1
        elif record.status == JobRunStatus.FAILED:
            self._total_failures += 1

        logger.debug(f"Recorded job run: {record}")

    def clear(self) -> None:
        """Clear all history and counters. Used in tests."""
        self._history.clear()
        self._total_runs = 0
        self._total_successes = 0
        self._total_failures = 0

    # ============================================================
    # READ
    # ============================================================
    def get_history(self) -> List[JobRunRecord]:
        """Return the current history (newest last) as a list."""
        return list(self._history)

    def get_recent(
        self, job_name: Optional[str] = None, limit: int = 10
    ) -> List[JobRunRecord]:
        """Return the most recent N run records, optionally filtered.

        Args:
            job_name: If set, only include records for this job.
            limit: Maximum number of records to return.

        Returns:
            List of JobRunRecord, most recent last.
        """
        records = list(self._history)
        if job_name is not None:
            records = [r for r in records if r.job_name == job_name]
        return records[-limit:]

    def get_last_run(
        self, job_name: Optional[str] = None
    ) -> Optional[JobRunRecord]:
        """Return the most recent run record, optionally filtered by job.

        Args:
            job_name: If set, only consider records for this job.

        Returns:
            The most recent matching record, or None.
        """
        records = self.get_recent(job_name=job_name, limit=1)
        return records[0] if records else None

    def get_stats(self) -> Dict[str, Any]:
        """Return aggregate counters.

        Returns:
            Dictionary with total_runs, total_successes,
            total_failures, and history_size.
        """
        return {
            "total_runs": self._total_runs,
            "total_successes": self._total_successes,
            "total_failures": self._total_failures,
            "history_size": len(self._history),
        }

    def __len__(self) -> int:
        """Return the number of records currently in history."""
        return len(self._history)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SchedulerState(history={len(self._history)}/{self.max_entries}, "
            f"total_runs={self._total_runs})"
        )