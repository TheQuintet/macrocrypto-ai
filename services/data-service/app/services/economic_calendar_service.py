"""
Economic calendar service.

Coordinates economic calendar data collection from FRED
and persistence into the economic_events table.

Responsibilities:
- Fetch economic events from FRED.
- Persist normalized events into PostgreSQL.
- Avoid duplicate economic events.
- Store event timestamps in UTC.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.collectors.economic_calendar import (
    EconomicCalendarCollector,
)
from app.config import settings
from app.models.economic_event import EconomicEvent


logger = logging.getLogger(__name__)


class EconomicCalendarService:
    """
    Service responsible for collecting and storing
    economic calendar events.
    """

    def __init__(
        self,
        db: Session,
        collector: EconomicCalendarCollector | None = None,
    ):
        self.db = db

        self.collector = (
            collector
            if collector is not None
            else EconomicCalendarCollector()
        )

    async def collect_events(
        self,
        days: int | None = None,
    ) -> list[EconomicEvent]:
        """
        Fetch economic calendar events from FRED
        and persist them into the database.

        Args:
            days:
                Number of future days to collect.
                Defaults to FRED_CALENDAR_LOOKBACK_DAYS.

        Returns:
            Newly created EconomicEvent records.
        """

        if days is None:
            days = (
                settings.FRED_CALENDAR_LOOKBACK_DAYS
            )

        logger.info(
            "Starting economic calendar collection "
            "(days=%s)",
            days,
        )

        events = await self.collector.get_all_events(
            days=days
        )

        if not events:
            logger.info(
                "No economic calendar events returned by FRED"
            )

            return []

        created_events: list[EconomicEvent] = []

        for event in events:

            event_type = event.get("event_type")
            event_date = event.get("event_date")

            if not event_type:
                logger.warning(
                    "Skipping event without event type: %s",
                    event,
                )
                continue

            if not event_date:
                logger.warning(
                    "Skipping event without event date: %s",
                    event,
                )
                continue

            event_date = self._normalize_event_date(
                event_date
            )

            existing_event = (
                self.db.query(EconomicEvent)
                .filter(
                    EconomicEvent.event_type
                    == event_type,
                    EconomicEvent.event_date
                    == event_date,
                )
                .first()
            )

            if existing_event:
                logger.debug(
                    "Economic event already exists: "
                    "%s %s",
                    event_type,
                    event_date,
                )
                continue

            economic_event = EconomicEvent(
                event_name=event.get(
                    "event_name",
                    event_type.upper(),
                ),
                event_type=event_type,
                event_date=event_date,
                impact_level=event.get(
                    "impact_level",
                    "high",
                ),
                description=event.get(
                    "description",
                    "",
                ),
            )

            self.db.add(economic_event)

            created_events.append(
                economic_event
            )

        if not created_events:
            logger.info(
                "No new economic calendar events to store"
            )

            return []

        try:

            self.db.commit()

            for event in created_events:
                self.db.refresh(event)

            logger.info(
                "Stored %d new economic calendar events",
                len(created_events),
            )

            return created_events

        except Exception:

            self.db.rollback()

            logger.exception(
                "Failed to store economic calendar events"
            )

            raise

    @staticmethod
    def _normalize_event_date(
        event_date: datetime,
    ) -> datetime:
        """
        Normalize an event timestamp to UTC.
        """

        if event_date.tzinfo is None:
            return event_date.replace(
                tzinfo=timezone.utc
            )

        return event_date.astimezone(
            timezone.utc
        )

    async def close(self):
        """
        Close the underlying FRED collector.
        """

        await self.collector.close()

        logger.info(
            "Economic calendar service closed"
        )