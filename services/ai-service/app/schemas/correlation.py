"""Pydantic schemas for the correlation API.

These schemas define the JSON contract for:
    - GET /api/v1/correlation/btc

Design:
    - `CorrelationEntry` — one row of correlation data, as the API
      returns it. Includes the raw coefficient plus the derived
      strength, direction, and their display hints (color and
      arrow). The color and arrow are populated by
      `app.correlation.calculator.strength_color` and
      `direction_arrow`, so the display logic lives in one place.
      Also includes the statistical significance flag and confidence
      level derived from the p-value (A1.4), and a short
      human-readable insight sentence (A1.7).
    - `CorrelationHistoryPoint` — one point in a correlation
      history series. Mirrors `CorrelationEntry` minus the
      indicator/window identifiers, which are constant within a
      series. Does not include an insight — history points are
      just data.
    - `CorrelationResponse` — the envelope returned by
      GET /api/v1/correlation/btc. One entry per (indicator,
      window).
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
from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# HISTORY POINT
# ============================================================
class CorrelationHistoryPoint(BaseModel):
    """One point in a correlation history series.

    Mirrors `CorrelationEntry` minus the (indicator_name,
    window_days) pair, which is constant within a series, and minus
    the insight sentence, which only applies to the current entry.
    The display fields (strength_color, direction_arrow,
    is_significant, confidence_level) are populated the same way as
    on the entry.

    Attributes:
        calculated_at: When the correlation was computed (UTC).
        correlation_coefficient: Pearson correlation in [-1, 1].
        strength: Derived strength label.
        strength_color: Display color for the strength.
        direction: Derived direction label.
        direction_arrow: Display arrow for the direction.
        p_value: Two-tailed p-value in [0, 1], or None.
        is_significant: True when p_value is below the threshold.
        confidence_level: Confidence level as a percentage, or None.
    """

    calculated_at: datetime = Field(
        ..., description="When the correlation was computed (UTC)."
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
        description="Two-tailed p-value in [0, 1], or None.",
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
            "Confidence level as a percentage ((1 - p_value) * 100). "
            "None when p_value is None."
        ),
    )


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
        insight: Short human-readable sentence describing the
            relationship (A1.7). Empty when the endpoint does not
            populate it.
        history: Ordered list of historical points for this
            (indicator, window), oldest first. Empty unless
            `?include_history=true` is set.
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
    insight: str = Field(
        "",
        description=(
            "Short human-readable sentence describing the "
            "relationship. Empty when not populated."
        ),
    )
    history: List[CorrelationHistoryPoint] = Field(
        default_factory=list,
        description=(
            "Historical points for this (indicator, window), oldest "
            "first. Empty unless ?include_history=true."
        ),
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
                    "insight": (
                        "When inflation rises, BTC typically falls "
                        "(medium negative correlation, 97% "
                        "confidence)."
                    ),
                    "history": [
                        {
                            "calculated_at": "2026-09-13T07:15:00Z",
                            "correlation_coefficient": -0.40,
                            "strength": "medium",
                            "strength_color": "yellow",
                            "direction": "negative",
                            "direction_arrow": "↓",
                            "p_value": 0.04,
                            "is_significant": True,
                            "confidence_level": 96.0,
                        }
                    ],
                }
            ]
        }
    }


# ============================================================
# RESPONSE ENVELOPE
# ============================================================
class CorrelationResponse(BaseModel):
    """Response body for GET /api/v1/correlation/btc.

    Attributes:
        window_days: The window the request asked for (30/90/365).
        generated_at: When this response was produced (UTC).
        entries: One entry per indicator with data in the requested
            window.
    """

    window_days: int = Field(
        ..., description="Rolling window length in days (30/90/365)."
    )
    generated_at: datetime = Field(
        ..., description="When this response was produced (UTC)."
    )
    entries: List[CorrelationEntry] = Field(
        default_factory=list,
        description="One entry per indicator with data.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "window_days": 90,
                    "generated_at": "2026-09-14T08:00:00Z",
                    "entries": [
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
                            "insight": (
                                "When inflation rises, BTC typically "
                                "falls (medium negative correlation, "
                                "97% confidence)."
                            ),
                            "history": [],
                        }
                    ],
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