"""Pydantic schemas for the correlation API.

These schemas define the JSON contract for the correlation
endpoints (A1.6). The envelope for GET /api/v1/correlation/btc is
added in A1.6; this module currently provides the entry-level
schema and the standard error response.

Design:
    - `CorrelationEntry` — one row of correlation data, as the API
      will return it. Includes the raw coefficient plus the derived
      strength, direction, and their display hints (color and
      arrow). The color and arrow are populated by
      `app.correlation.calculator.strength_color` and
      `direction_arrow`, so the display logic lives in one place.
      Also includes the statistical significance flag and confidence
      level derived from the p-value (A1.4).
    - `CorrelationErrorResponse` — mirrors the pattern used by
      `PerformanceErrorResponse` and `PredictionErrorResponse`.

Units:
    - `correlation_coefficient` is dimensionless, in [-1, 1]
    - `p_value` is dimensionless, in [0, 1] (or None when not yet
      computed)
    - `confidence_level` is a percentage, in [0, 100] (or None when
      p_value is None)
    - `window_days` is a duration in days: 30, 90, or 365
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# ENTRY
# ============================================================
class CorrelationEntry(BaseModel):
    """One correlation row for a given (indicator, window).

    Attributes:
        indicator_name: Product-facing indicator label. One of
            'inflation', 'rates', 'gdp', 'unemployment'.
        window_days: Rolling window length in days. One of 30, 90,
            365.
        correlation_coefficient: Pearson correlation in [-1, 1].
        strength: Derived strength label. One of 'strong', 'medium',
            'weak'.
        strength_color: Display color for the strength. One of
            'green', 'yellow', 'red'.
        direction: Derived direction label. One of 'positive',
            'negative'.
        direction_arrow: Display arrow for the direction. One of
            '↑', '↓'.
        p_value: Two-tailed p-value in [0, 1], or None when the
            correlation was undefined.
        is_significant: True when p_value is below the significance
            threshold (0.05). False when p_value is None.
        confidence_level: Confidence level as a percentage
            ((1 - p_value) * 100), or None when p_value is None.
        calculated_at: When the correlation was computed (UTC).
    """

    indicator_name: str = Field(
        ..., description="Product-facing indicator label."
    )
    window_days: int = Field(
        ..., description="Rolling window length in days (30/90/365)."
    )
    correlation_coefficient: float = Field(
        ..., description="Pearson correlation coefficient in [-1, 1]."
    )
    strength: str = Field(
        ..., description="Derived strength: strong, medium, or weak."
    )
    strength_color: str = Field(
        ..., description="Display color: green, yellow, or red."
    )
    direction: str = Field(
        ..., description="Derived direction: positive or negative."
    )
    direction_arrow: str = Field(
        ..., description="Display arrow: ↑ or ↓."
    )
    p_value: Optional[float] = Field(
        None,
        description=(
            "Two-tailed p-value in [0, 1]. None when the correlation "
            "was undefined (insufficient data or zero variance)."
        ),
    )
    is_significant: bool = Field(
        False,
        description=(
            "True when p_value is strictly below the significance "
            "threshold (0.05). False when p_value is None."
        ),
    )
    confidence_level: Optional[float] = Field(
        None,
        description=(
            "Confidence level as a percentage, computed as "
            "(1 - p_value) * 100. None when p_value is None."
        ),
    )
    calculated_at: datetime = Field(
        ..., description="When the correlation was computed (UTC)."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "indicator_name": "inflation",
                    "window_days": 90,
                    "correlation_coefficient": -0.42,
                    "strength": "medium",
                    "strength_color": "yellow",
                    "direction": "negative",
                    "direction_arrow": "↓",
                    "p_value": 0.03,
                    "is_significant": True,
                    "confidence_level": 97.0,
                    "calculated_at": "2026-09-14T07:15:00Z",
                }
            ]
        }
    }


# ============================================================
# ERROR
# ============================================================
class CorrelationErrorResponse(BaseModel):
    """Response body for correlation endpoint errors.

    Attributes:
        error: Short error code.
        message: Human-readable error message.
        detail: Optional additional context.
    """

    error: str = Field(..., description="Short error code.")
    message: str = Field(
        ..., description="Human-readable message."
    )
    detail: Optional[str] = Field(
        None, description="Optional additional context."
    )