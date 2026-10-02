"""Scheduler lifecycle manager.

Wraps APScheduler's AsyncIOScheduler with:
    - Conditional job registration gated by two category toggles:
        * scheduler_ml_jobs_enabled  — the 8 ML jobs
        * scheduler_analytics_jobs_enabled — the 3 analytics jobs
    - Lifecycle (start, shutdown) tied to FastAPI's lifespan
    - Failure handling (retries per settings.scheduler_max_retries)
    - Run history in SchedulerState

Job categories:
    ML jobs (8) — depend on trained models:
        - daily_retrain
        - hourly_prediction
        - daily_7d_prediction
        - daily_backtest
        - daily_accuracy
        - daily_multi_model_predictions
        - daily_model_performance_aggregation
        - daily_promote_champion

    Analytics + housekeeping jobs (3) — independent of models:
        - daily_correlation
        - daily_event_impact_update
        - daily_export_cleanup

Design:
    - The manager owns the scheduler instance; no other module
      touches it directly
    - Every job is wrapped with a "run record" wrapper that captures
      timing, outcome, and errors, and applies retries
    - Job failures never propagate to APScheduler — a failed job
      logs and waits for the next tick
    - The manager is created once (module-level singleton) and used
      by app/main.py's lifespan
    - Disabled categories are skipped at registration time — the
      scheduler never sees them, so they produce no logs, no missed
      runs, and no run history
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
    JOB_DAILY_CORRELATION,
    JOB_DAILY_EVENT_IMPACT_UPDATE,
    JOB_DAILY_EXPORT_CLEANUP,
    JOB_DAILY_MODEL_PERFORMANCE_AGGREGATION,
    JOB_DAILY_MULTI_MODEL_PREDICTIONS,
    JOB_DAILY_PROMOTE_CHAMPION,
    JOB_DAILY_RETRAIN,
    JOB_HOURLY_PREDICTION,
    daily_7d_prediction_job,
    daily_accuracy_job,
    daily_backtest_job,
    daily_correlation_job,
    daily_event_impact_update_job,
    daily_export_cleanup_job,
    daily_model_performance_aggregation_job,
    daily_multi_model_predictions_job,
    daily_promote_champion_job,
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
JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS = "daily_multi_model_predictions"
JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION = (
    "daily_model_performance_aggregation"
)
JOB_ID_DAILY_PROMOTE_CHAMPION = "daily_promote_champion"
JOB_ID_DAILY_CORRELATION = "daily_correlation"
JOB_ID_DAILY_EXPORT_CLEANUP = "daily_export_cleanup"
JOB_ID_DAILY_EVENT_IMPACT_UPDATE = "daily_event_impact_update"


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

    Job registration is conditional. The ML jobs are registered only
    when ``settings.scheduler_ml_jobs_enabled`` is True; the analytics
    jobs are registered only when
    ``settings.scheduler_analytics_jobs_enabled`` is True. Both
    default per ``app/config.py``.
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
            f"SchedulerManager initialized "
            f"(enabled={self.enabled}, "
            f"ml_jobs={settings.scheduler_ml_jobs_enabled}, "
            f"analytics_jobs={settings.scheduler_analytics_jobs_enabled})"
        )

    # ============================================================
    # LIFECYCLE
    # ============================================================
    def setup(self) -> None:
        """Register jobs with the scheduler, honoring category toggles.

        The registration is conditional:

            - ML jobs (8) are registered only when
              ``settings.scheduler_ml_jobs_enabled`` is True.
            - Analytics jobs (3) are registered only when
              ``settings.scheduler_analytics_jobs_enabled`` is True.

        Disabled categories are skipped entirely — their jobs are not
        added to the scheduler, so they produce no logs, no missed
        runs, and no history.

        Safe to call multiple times — subsequent calls are no-ops.
        """
        if self._scheduler is not None:
            logger.debug("Scheduler already set up — skipping")
            return

        self._scheduler = AsyncIOScheduler(
            timezone=settings.retrain_timezone
        )

        # ------------------------------------------------------------
        # ML jobs (8) — gated by scheduler_ml_jobs_enabled
        # ------------------------------------------------------------
        if settings.scheduler_ml_jobs_enabled:
            self._register_daily_retrain_job()
            self._register_hourly_prediction_job()
            self._register_daily_7d_prediction_job()
            self._register_daily_backtest_job()
            self._register_daily_accuracy_job()
            self._register_daily_multi_model_predictions_job()
            self._register_daily_model_performance_aggregation_job()
            self._register_daily_promote_champion_job()
            logger.info(
                "Registered 8 ML jobs "
                "(SCHEDULER_ML_JOBS_ENABLED=true)"
            )
        else:
            logger.info(
                "Skipping 8 ML jobs "
                "(SCHEDULER_ML_JOBS_ENABLED=false)"
            )

        # ------------------------------------------------------------
        # Analytics + housekeeping jobs (3)
        # — gated by scheduler_analytics_jobs_enabled
        # ------------------------------------------------------------
        if settings.scheduler_analytics_jobs_enabled:
            self._register_daily_correlation_job()
            self._register_daily_export_cleanup_job()
            self._register_daily_event_impact_update_job()
            logger.info(
                "Registered 3 analytics jobs "
                "(SCHEDULER_ANALYTICS_JOBS_ENABLED=true)"
            )
        else:
            logger.info(
                "Skipping 3 analytics jobs "
                "(SCHEDULER_ANALYTICS_JOBS_ENABLED=false)"
            )

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

    def _register_daily_multi_model_predictions_job(self) -> None:
        """Register the daily multi-model predictions job (6:15 AM UTC).

        Sits between the daily retrain (6:00) and the daily 7d
        Prophet prediction (6:30). Writes one stored batch per
        non-prophet_fresh variant for both horizons, so the M6a
        comparison endpoint has real multi-model data to compare.
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.multi_model_prediction_hour,
            minute=settings.multi_model_prediction_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_MULTI_MODEL_PREDICTIONS,
                daily_multi_model_predictions_job,
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS,
            name="Daily multi-model prediction generation",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_MULTI_MODEL_PREDICTIONS}' "
            f"(trigger: hour={settings.multi_model_prediction_hour} "
            f"minute={settings.multi_model_prediction_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_model_performance_aggregation_job(self) -> None:
        """Register the daily model-performance aggregation job (7:15 AM UTC).

        Sits after the 6:45 backtest (which writes prediction_performance)
        and after the 7:00 accuracy check (which reads the same source).
        Copies the latest aggregate metrics from prediction_performance
        into model_performance, so the M8 multi-model performance API
        has a compact, indexed history to read from.
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.model_performance_aggregation_hour,
            minute=settings.model_performance_aggregation_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_MODEL_PERFORMANCE_AGGREGATION,
                daily_model_performance_aggregation_job,
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION,
            name="Daily model performance aggregation",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job "
            f"'{JOB_ID_DAILY_MODEL_PERFORMANCE_AGGREGATION}' "
            f"(trigger: hour={settings.model_performance_aggregation_hour} "
            f"minute={settings.model_performance_aggregation_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_promote_champion_job(self) -> None:
        """Register the daily champion promotion job (7:30 AM UTC).

        Sits after the 7:15 model-performance aggregation job so both
        source tables — prediction_performance (written at 6:45) and
        model_performance (written at 7:15) — are fresh when the
        promotion job reads them.

        The job ranks candidate models by backtested metrics over
        two rolling windows, applies three safety gates (minimum
        sample size, meaningful lead, stability streak), and promotes
        a new champion per horizon (and optionally per regime).

        Runs at champion_promotion_hour:champion_promotion_minute
        (default 7:30 AM UTC). Configurable via Settings.

        misfire_grace_time=1800 (30 min): if the scheduler was down
        and misses the 7:30 tick, run anyway so the champion set is
        still refreshed that day.
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.champion_promotion_hour,
            minute=settings.champion_promotion_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_PROMOTE_CHAMPION,
                daily_promote_champion_job,
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_PROMOTE_CHAMPION,
            name="Daily champion promotion",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_PROMOTE_CHAMPION}' "
            f"(trigger: hour={settings.champion_promotion_hour} "
            f"minute={settings.champion_promotion_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_correlation_job(self) -> None:
        """Register the daily correlation job (2:00 AM UTC).

        Sits well before the 6:00 retrain so the correlations are
        computed on the previous day's freshest macro data. Reads
        BTC price and macro indicator data, resamples BTC to daily
        close, and writes one correlation row per (indicator,
        window) to btc_macro_correlation. Feeds A1.6's read API.
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.correlation_hour,
            minute=settings.correlation_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_CORRELATION,
                daily_correlation_job,
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_CORRELATION,
            name="Daily correlation calculation",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_CORRELATION}' "
            f"(trigger: hour={settings.correlation_hour} "
            f"minute={settings.correlation_minute} "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_export_cleanup_job(self) -> None:
        """Register the daily export cleanup job (3:00 AM UTC).

        Sits after the 2:00 correlation job and well before the
        6:00 retrain. Deletes export files older than
        ``settings.export_file_ttl_seconds``. Only
        ``LocalDiskStorage`` supports age-based cleanup on this
        branch; the job no-ops on any other backend.

        Schedule choices:
            - 3:00 AM UTC: the correlation job (2:00) typically
              finishes in a few seconds, and the retrain (6:00)
              does not touch storage. 3:00 is a quiet window.
            - misfire_grace_time=1800 (30 min): if the scheduler
              was down and misses the tick, run anyway.
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=3,
            minute=0,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_EXPORT_CLEANUP,
                daily_export_cleanup_job,
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_EXPORT_CLEANUP,
            name="Daily export cleanup",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_EXPORT_CLEANUP}' "
            f"(trigger: hour=3 minute=0 "
            f"tz={settings.retrain_timezone})"
        )

    def _register_daily_event_impact_update_job(self) -> None:
        """Register the daily event impact update job (4:00 AM UTC).

        Sits after the 3:00 export cleanup and well before the
        6:00 retrain. Reads every row in ``historical_event_impacts``,
        recomputes the BTC reaction with A5.2's ``ReactionCalculator``,
        and updates rows whose reaction changed. Idempotent: a second
        run the same day is a no-op.

        Schedule choices:
            - 4:00 AM UTC: the export cleanup (3:00) typically
              finishes in a few seconds, and the retrain (6:00)
              does not touch the events table. 4:00 is a quiet
              window.
            - misfire_grace_time=1800 (30 min): if the scheduler
              was down and misses the tick, run anyway.
        """
        if self._scheduler is None:
            raise RuntimeError("Scheduler not set up")

        trigger = CronTrigger(
            hour=settings.event_impact_hour,
            minute=settings.event_impact_minute,
            timezone=settings.retrain_timezone,
        )

        self._scheduler.add_job(
            func=self._wrap_job(
                JOB_DAILY_EVENT_IMPACT_UPDATE,
                daily_event_impact_update_job,
            ),
            trigger=trigger,
            id=JOB_ID_DAILY_EVENT_IMPACT_UPDATE,
            name="Daily event impact update",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=1800,
        )

        logger.info(
            f"Registered job '{JOB_ID_DAILY_EVENT_IMPACT_UPDATE}' "
            f"(trigger: hour={settings.event_impact_hour} "
            f"minute={settings.event_impact_minute} "
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
        """Return the next scheduled run time for a job, or None.

        APScheduler only populates ``Job.next_run_time`` once the
        scheduler has started. Before ``start()`` — i.e. after
        ``setup()`` but before the event loop is running — the
        attribute does not exist on the Job object, so we read it
        with ``getattr`` and fall back to None. The method is
        therefore safe to call in any lifecycle state.
        """
        if self._scheduler is None:
            return None
        job = self._scheduler.get_job(job_id)
        if job is None:
            return None
        return getattr(job, "next_run_time", None)

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