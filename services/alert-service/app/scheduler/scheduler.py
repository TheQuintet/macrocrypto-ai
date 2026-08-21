"""Scheduler setup for alert-service"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.scheduler.jobs import (
    expire_alerts_job,
    cleanup_alerts_job,
    process_email_queue_job
)
from app.scheduler.prediction_jobs import (
    check_prediction_changes_job,
    cleanup_prediction_history_job
)
from app.scheduler.macro_jobs import (
    check_macro_events_job,
    cleanup_old_events_job
)

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def setup_scheduler():
    """Configure and start the scheduler."""
    
    # Run every hour - expire old alerts
    scheduler.add_job(
        expire_alerts_job,
        trigger=IntervalTrigger(hours=1),
        id="expire_alerts",
        name="Expire alerts",
        replace_existing=True
    )
    
    # Run every 5 minutes - process email queue
    scheduler.add_job(
        process_email_queue_job,
        trigger=IntervalTrigger(minutes=5),
        id="process_emails",
        name="Process email queue",
        replace_existing=True
    )
    
    # Run every hour - check prediction changes (T8)
    scheduler.add_job(
        check_prediction_changes_job,
        trigger=IntervalTrigger(hours=1),
        id="check_prediction_changes",
        name="Check prediction changes",
        replace_existing=True
    )
    
    # Run every hour - check macro events (T9)
    scheduler.add_job(
        check_macro_events_job,
        trigger=IntervalTrigger(hours=1),
        id="check_macro_events",
        name="Check macro events",
        replace_existing=True
    )
    
    # Run daily at midnight - cleanup old alerts
    scheduler.add_job(
        cleanup_alerts_job,
        trigger=CronTrigger(hour=0, minute=0),
        id="cleanup_alerts",
        name="Cleanup old alerts",
        replace_existing=True
    )
    
    # Run daily at 2am - cleanup prediction history (T8)
    scheduler.add_job(
        cleanup_prediction_history_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="cleanup_prediction_history",
        name="Cleanup prediction history",
        replace_existing=True
    )
    
    # Run daily at 3am - cleanup old macro events (T9)
    scheduler.add_job(
        cleanup_old_events_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup_old_events",
        name="Cleanup old macro events",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler started with 7 jobs")
    
    # Log scheduled jobs
    for job in scheduler.get_jobs():
        logger.info(f"📋 Scheduled job: {job.name} (next run: {job.next_run_time})")


def shutdown_scheduler():
    """Shutdown the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("✅ Scheduler shutdown")