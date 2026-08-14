"""
Scheduled background jobs.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def wait_until_next_run(
    hour: int,
    minute: int,
):
    """
    Sleep until the next scheduled UTC time.
    """

    now = datetime.now(timezone.utc)

    next_run = now.replace(
        hour=hour,
        minute=minute,
        second=0,
        microsecond=0,
    )

    if next_run <= now:
        next_run += timedelta(days=1)

    wait_seconds = (
        next_run - now
    ).total_seconds()

    logger.info(
        f"Next macro update scheduled "
        f"at {next_run.isoformat()}"
    )

    await asyncio.sleep(
        wait_seconds
    )


async def periodic_regime_collection():
    """
    Daily scheduler for current macroeconomic regime processing.

    Runs independently from the FRED indicator scheduler.
    """

    logger.info(
        "🔥 Current regime scheduler started"
    )

    from app.database.session import SessionLocal
    from app.services.current_regime_service import (
        CurrentRegimeService,
    )

    while True:
        try:
            await wait_until_next_run(
                settings.CURRENT_REGIME_UPDATE_HOUR_UTC,
                settings.CURRENT_REGIME_UPDATE_MINUTE_UTC,
            )

            logger.info(
                "🔥 Current regime scheduler woke up"
            )

            db = SessionLocal()
            service = None

            try:
                service = CurrentRegimeService(db)

                result = (
                    await service.process_current_regime()
                )

                logger.info(
                    "Current regime processing completed: %s",
                    result,
                )

            finally:
                if service:
                    await service.close()

                db.close()

                logger.info(
                    "Current regime database session closed"
                )

        except asyncio.CancelledError:
            logger.info(
                "Current regime scheduler cancelled"
            )
            raise

        except Exception:
            logger.exception(
                "🔥 Current regime scheduler failed"
            )