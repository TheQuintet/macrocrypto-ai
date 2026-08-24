"""
Pydantic schemas for economic calendar validation.
"""

from datetime import datetime, timezone
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator


EventType = Literal[
    "fed",
    "cpi",
    "employment",
    "gdp",
]

ImpactLevel = Literal[
    "high",
    "medium",
    "low",
]


class EconomicEventCreate(BaseModel):
    """
    Validated economic event input.
    """

    event_name: str = Field(
        min_length=1,
        max_length=150,
    )

    event_type: EventType

    event_date: datetime

    impact_level: ImpactLevel

    description: str = Field(
        min_length=1,
    )

    @field_validator("event_date")
    @classmethod
    def validate_event_date(
        cls,
        value: datetime,
    ) -> datetime:
        """
        Require a timezone-aware datetime and normalize it to UTC.
        """

        if value.tzinfo is None:
            raise ValueError(
                "event_date must be timezone-aware"
            )

        return value.astimezone(timezone.utc)


class UserCalendarPreferenceCreate(BaseModel):
    """
    Validated user calendar preference.
    """

    user_id: int = Field(
        gt=0,
    )

    timezone: str = "UTC"

    @field_validator("timezone")
    @classmethod
    def validate_timezone(
        cls,
        value: str,
    ) -> str:
        """
        Validate an IANA timezone identifier.
        """

        try:
            ZoneInfo(value)
        except Exception as exc:
            raise ValueError(
                f"Invalid timezone: {value}"
            ) from exc

        return value