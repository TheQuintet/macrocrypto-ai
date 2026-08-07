"""
Scheduled background jobs.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

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
        next_run += timedelta(
            days=1
        )


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