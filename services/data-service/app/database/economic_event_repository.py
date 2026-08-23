"""
Repository for economic calendar events.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.economic_event import EconomicEvent


logger = logging.getLogger(__name__)


class EconomicEventRepository:
    """
    Handles database operations for economic calendar events.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        event_name: str,
        event_type: str,
        event_date: datetime,
        impact_level: str,
        description: str,
    ) -> EconomicEvent:
        """
        Create and persist a single economic event.

        Event dates are normalized to UTC before storage.
        """

        if event_date.tzinfo is None:
            raise ValueError(
                "event_date must be timezone-aware"
            )

        event_date = event_date.astimezone(timezone.utc)

        event = EconomicEvent(
            event_name=event_name,
            event_type=event_type,
            event_date=event_date,
            impact_level=impact_level,
            description=description,
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        logger.info(
            "Stored economic event: %s",
            event_name,
        )

        return event