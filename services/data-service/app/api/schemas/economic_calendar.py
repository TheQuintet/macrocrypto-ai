"""
Pydantic response models for economic calendar endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EconomicEventResponse(BaseModel):
    """
    Represents a single economic calendar event returned by the API.
    """

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    event_name: str
    event_type: str
    event_date: datetime
    impact_level: str
    description: str


class EconomicCalendarResponse(BaseModel):
    """
    Response model for the economic calendar API.

    Attributes:
        count:
            Number of economic events returned.

        events:
            Collection of economic calendar events.
    """

    count: int
    events: list[EconomicEventResponse]