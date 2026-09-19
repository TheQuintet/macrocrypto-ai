"""Scheduler lifecycle manager.

Wraps APScheduler's AsyncIOScheduler with:
    - Job registration (daily retrain, hourly 24h prediction,
      daily 7d prediction, daily backtest, daily accuracy)
    - Lifecycle (start, shutdown) tied to FastAPI's lifespan
    - Failure handling (retries per settings.scheduler_max_retries)
    - Run history in SchedulerState

Design:
    - The manager owns the scheduler instance; no other module
      touches it directly
    - Every job is wrapped with a "run record" wrapper that captures
      timing, outcome, and errors, and applies retries
    - Job failures never propagate to APScheduler — a failed job
      logs and waits for the next tick
    - The manager is created once (module-level singleton) and used
      by app/main.py's lifespan
"""

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.scheduler.jobs import (
    JOB_DAILY_7D_PREDICTION,
    JOB_DAILY_ACCURACY,
    JOB_DAILY_BACKTEST,
    JOB_DAILY_RETRAIN,
    JOB_HOURLY_PREDICTION,
    daily_7d_prediction_job,
    daily_accuracy_job,
    daily_backtest_job,
    daily_retrain_job,
    hourly_prediction_job,
)
from app.scheduler.state import (
    JobRunRecord,
    JobRunStatus,
    SchedulerState,
)

logger = logging.getLogger(__name__)


# ============================================================
# JOB IDS
# ============================================================
JOB_ID_DAILY_RETRAIN = "daily_retrain"
JOB_ID_HOURLY_PREDICTION = "hourly_prediction"
JOB_ID_DAILY_7D_PREDICTION = "daily_7d_prediction"
JOB_ID_DAILY_BACKTEST = "daily_backtest"
JOB_ID_DAILY_ACCURACY = "daily_accuracy"


# ============================================================
# MANAGER
# ============================================================
class SchedulerManager:
    """Owns the APScheduler instance and manages job lifecycle.

    Usage:
        manager = SchedulerManager()
        manager.setup()              # register jobs
        manager.start()              # begin scheduling
        ...
        manager.shutdown()           # stop cleanly
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        state: Optional[SchedulerState] = None,
    ) -> None:
        """Initialize the manager.

        Args:
            enabled: Override settings.scheduler_enabled. If None,
                uses the setting.
            state: Optional SchedulerState instance. If None, creates
                one with max_entries from settings.
        """
        self.enabled = (
            settings.scheduler_enabled if enabled is None else enabled
        )
        self.state = (
            state
            if state is not None
            else SchedulerState(
                max_entries=settings.scheduler_history_max_entries
            )
        )
        self._scheduler: Optional[AsyncIOScheduler] = None
        self._started = False

        logger.info(
            f"SchedulerManager initialized (enabled={self.enabled})"
        )

    # ============================================================
    # LIFECYCLE
    # ============================================================
    def setup(self) -> None:
        """Register all jobs with the scheduler.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._scheduler is not None:
            logger.debug("Scheduler already set up — skipping")
            return

        self._scheduler = AsyncIOScheduler(
            timezone=settings.retrain_timezone
        )

        self._register_daily_retrain_job()
        self._register_hourly_prediction_job()
        self._register_daily_7d_prediction_job()
        self._register_daily_backtest_job()
        self._register_daily_accuracy_job()

        logger.info("Scheduler setup complete")

    def start(self) -> None:
        """Start the scheduler. Idempotent.

        If settings.scheduler_enabled is False, this is a no-op and
        logs a message.
        """
        if not self.enabled:
            logger.info(
                "Scheduler is disabled (SCHEDULER_ENABLED=false) — "
                "skipping start"
            )
            return

        if self._started:
            logger.debug("Scheduler already started — skipping")
            return

        if self._scheduler is None:
            self.setup()

        assert self._scheduler is not None

        self._scheduler.start()
        self._started = True

        logger.info("Scheduler started")

    def shutdown(self) -> None:
        """Shut down the scheduler cleanly. Idempotent."""
        if self._scheduler is not None and self._started:
            try:
                self._scheduler.shutdown(wait=False)
                logger.info("Scheduler shut down")
            except Exception as e:
                logger.warning(f"Scheduler shutdown error: {e}")
            finally:
                self._started = False

    # ============================================================
    # JOB REGISTRATION
    # ============================================================
    def _register_daily_retrain_job(self) -> None:
        """Register the daily retrain job (6:00 AM UTC)."""
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.retrain_hour,
            minute=settings.retrain_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(JOB_DAILY_RETRAIN, daily_retrain_job),
            trigger=trigger,
            id=JOB_ID_DAILY_RETRAIN,
            name="Daily model retraining",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_RETRAIN}' "
            f"(trigger: hour={settings.retrain_hour} "
            f"minute={settings.retrain_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_hourly_prediction_job(self) -> None:
        """Register the hourly prediction job (top of each hour)."""
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            minute=0,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_HOURLY_PREDICTION, hourly_prediction_job
            ),
            trigger=trigger,
            id=JOB_ID_HOURLY_PREDICTION,
            name="Hourly 24h prediction generation",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

        logger.info(
            f"Registered job '{JOB_ID_HOURLY_PREDICTION}' "
            f"(trigger: minute=0, tz={settings.retrain_timezone})"
        )

    def _register_daily_7d_prediction_job(self) -> None:
        """Register the daily 7d prediction job (6:30 AM UTC)."""
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.prediction_7d_hour,
            minute=settings.prediction_7d_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_7D_PREDICTION, daily_7d_prediction_job
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_7D_PREDICTION,
            name="Daily 7d prediction generation",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_7D_PREDICTION}' "
            f"(trigger: hour={settings.prediction_7d_hour} "
            f"minute={settings.prediction_7d_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_backtest_job(self) -> None:
        """Register the daily backtest job (6:45 AM UTC)."""
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.backtest_hour,
            minute=settings.backtest_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_BACKTEST, daily_backtest_job
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_BACKTEST,
            name="Daily walk-forward backtesting",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_BACKTEST}' "
            f"(trigger: hour={settings.backtest_hour} "
            f"minute={settings.backtest_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_accuracy_job(self) -> None:
        """Register the daily accuracy check job (7:00 AM UTC)."""
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.accuracy_hour,
            minute=settings.accuracy_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_ACCURACY, daily_accuracy_job
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_ACCURACY,
            name="Daily accuracy threshold check",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_ACCURACY}' "
            f"(trigger: hour={settings.accuracy_hour} "
            f"minute={settings.accuracy_minute} "
            f"tz={settings.retrain_timezone})"
        )

    # ============================================================
    # JOB WRAPPER
    # ============================================================
    def _wrap_job(
        self,
        job_name: str,
        job_func: Callable[[], Awaitable[Dict[str, Any]]],
    ) -> Callable[[], Awaitable[None]]:
        """Wrap a job function with run recording and retries.

        The wrapper:
            1. Times the run
            2. Calls the job function
            3. On success, records a SUCCESS record
            4. On failure, retries once (if configured), then records
               a FAILED record
            5. Never raises — APScheduler should not see exceptions

        Args:
            job_name: Job identifier for logging and history.
            job_func: The async job function to wrap.

        Returns:
            An async callable compatible with APScheduler.
        """

        async def _runner() -> None:
            attempt = 0
            max_attempts = 1 + settings.scheduler_max_retries

            while attempt < max_attempts:
                attempt += 1
                started = datetime.now(timezone.utc)

                try:
                    result = await job_func()
                    finished = datetime.now(timezone.utc)
                    duration = (finished - started).total_seconds()

                    self.state.record(
                        JobRunRecord(
                            job_name=job_name,
                            started_at=started,
                            finished_at=finished,
                            duration_seconds=duration,
                            status=JobRunStatus.SUCCESS,
                            attempt=attempt,
                            result=result,
                            error=None,
                        )
                    )

                    logger.info(
                        f"Job '{job_name}' succeeded on attempt {attempt} "
                        f"in {duration:.3f}s"
                    )
                    return

                except Exception as e:
                    finished = datetime.now(timezone.utc)
                    duration = (finished - started).total_seconds()

                    logger.error(
                        f"Job '{job_name}' failed on attempt {attempt} "
                        f"after {duration:.3f}s: {e}",
                        exc_info=True,
                    )

                    if attempt >= max_attempts:
                        self.state.record(
                            JobRunRecord(
                                job_name=job_name,
                                started_at=started,
                                finished_at=finished,
                                duration_seconds=duration,
                                status=JobRunStatus.FAILED,
                                attempt=attempt,
                                result=None,
                                error=str(e),
                            )
                        )
                        return

                    self.state.record(
                        JobRunRecord(
                            job_name=job_name,
                            started_at=started,
                            finished_at=finished,
                            duration_seconds=duration,
                            status=JobRunStatus.RETRIED,
                            attempt=attempt,
                            result=None,
                            error=str(e),
                        )
                    )

        return _runner

    # ============================================================
    # INTROSPECTION
    # ============================================================
    def get_job_ids(self) -> list:
        """Return the list of registered job IDs."""
        if self._scheduler is None:
            return []
        return [job.id for job in self._scheduler.get_jobs()]

    def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Return the next scheduled run time for a job, or None."""
        if self._scheduler is None:
            return None
        job = self._scheduler.get_job(job_id)
        return job.next_run_time if job else None

    def is_running(self) -> bool:
        """Return True if the scheduler is running."""
        return bool(
            self._started
            and self._scheduler is not None
            and self._scheduler.running
        )

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"SchedulerManager(enabled={self.enabled}, "
            f"started={self._started}, "
            f"jobs={self.get_job_ids()})"
        )


# ============================================================
# MODULE-LEVEL SINGLETON
# ============================================================
# A single SchedulerManager instance shared by the FastAPI lifespan.
# Tests can create their own instances to avoid global state.
scheduler_manager = SchedulerManager()