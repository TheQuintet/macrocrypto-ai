"""
SQLAlchemy model for user economic-calendar preferences.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
)

from app.models.btc_price import Base


class UserCalendarPreference(Base):
    """
    User-specific calendar display preferences.

    Timezone is stored as an IANA timezone identifier, for example:

        UTC
        Africa/Addis_Ababa
        America/New_York
        Europe/London
    """

    __tablename__ = "user_calendar_preferences"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id = Column(
        Integer,
        nullable=False,
    )

    timezone = Column(
        String(64),
        nullable=False,
        default="UTC",
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
        Index(
            "ix_user_calendar_preferences_user_id",
            "user_id",
        ),
    )