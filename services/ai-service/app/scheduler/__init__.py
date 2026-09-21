"""AI Service — Scheduler package.

Provides the APScheduler-based job scheduling for the AI Service:
    - SchedulerManager: lifecycle (setup, start, shutdown)
    - Job definitions: hourly prediction generation
    - Job state: in-memory ring buffer of recent runs

Usage:
    The scheduler is started/stopped by the FastAPI lifespan in
    app/main.py. Individual jobs are registered by the manager.

    To disable scheduling (e.g., during tests), set the
    SCHEDULER_ENABLED env var to false.
"""

from app.scheduler.manager import SchedulerManager
from app.scheduler.state import (
    JobRunRecord,
    JobRunStatus,
    SchedulerState,
)

__all__ = [
    "SchedulerManager",
    "SchedulerState",
    "JobRunRecord",
    "JobRunStatus",
]