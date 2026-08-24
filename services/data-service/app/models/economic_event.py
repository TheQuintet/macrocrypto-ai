"""
SQLAlchemy model for economic calendar events.

Economic events are stored in UTC and exposed through
the API using the user's preferred timezone.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)

from app.models.btc_price import Base


class EconomicEvent(Base):
    """
    Economic calendar event.

    Supported event types:
    - fed
    - cpi
    - employment
    - gdp

    Supported impact levels:
    - high
    - medium
    - low
    """

    __tablename__ = "economic_events"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    event_name = Column(
        String(150),
        nullable=False,
    )

    event_type = Column(
        String(30),
        nullable=False,
    )

    # Canonical storage format is UTC.
    event_date = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    impact_level = Column(
        String(20),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN "
            "('fed', 'cpi', 'employment', 'gdp')",
            name="ck_economic_events_event_type",
        ),
        CheckConstraint(
            "impact_level IN "
            "('high', 'medium', 'low')",
            name="ck_economic_events_impact_level",
        ),
        Index(
            "ix_economic_events_event_date",
            "event_date",
        ),
        Index(
            "ix_economic_events_event_type",
            "event_type",
        ),
        Index(
            "ix_economic_events_event_date_type",
            "event_date",
            "event_type",
        ),
    )