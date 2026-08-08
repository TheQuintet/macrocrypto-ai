"""
Pydantic response models for macroeconomic indicator endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IndicatorItem(BaseModel):
    """
    Represents a single macroeconomic indicator returned by the API.

    Attributes:
        indicator_name:
            Name of the macroeconomic indicator.

        time:
            Timestamp of the observation.

        current_value:
            Latest recorded value.

        previous_value:
            Previous recorded value.

        change_percent:
            Percentage change from the previous value.

        trend:
            Trend direction.

            ↑ = Increasing
            ↓ = Decreasing
            → = Unchanged

        source:
            Data provider.
    """

    model_config = ConfigDict(from_attributes=True)

    indicator_name: str
    time: datetime
    current_value: float
    previous_value: float | None = None
    change_percent: float | None = None
    trend: str
    source: str


class IndicatorsResponse(BaseModel):
    """
    Response model for the GET /api/v1/indicators endpoint.

    Attributes:
        period:
            Historical period requested by the client.
            Supported values:
            - 30d
            - 90d
            - 1y
            - 5y

        count:
            Number of indicators returned.

        indicators:
            Collection of macroeconomic indicators.
    """

    period: str | None = None
    count: int
    indicators: list[IndicatorItem]