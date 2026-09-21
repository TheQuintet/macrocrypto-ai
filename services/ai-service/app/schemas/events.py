"""Pydantic schemas for the events endpoint (A5.4).

The events endpoint returns two things in one payload:

    - ``events``: the per-event rows stored by A5.2, one per
      historical event, each carrying its BTC reaction
      (btc_price_before, btc_price_after, price_change_percent,
      volatility, direction).
    - ``metrics``: the per-event-type aggregates computed by A5.3
      (mean change, mean volatility, direction frequencies,
      min/max, confidence interval).

Both are wrapped in one ``EventsResponse`` so the frontend can
render the table and the summary from a single round-trip. The
schema is a dumb container: all derivation (normalization,
aggregation, confidence intervals) happens in
``app.events.metrics`` before the response is built.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# EVENT ROW
# ============================================================
class EventResponse(BaseModel):
    """One historical event and its BTC reaction.

    Mirrors a row of ``historical_event_impacts``. All fields are
    the raw stored values; nothing here is derived.
    """

    event_name: str = Field(
        ...,
        description="Free-form event name (e.g. 'FOMC', 'CPI Release').",
    )
    event_date: date = Field(
        ...,
        description="Calendar date the event occurred (UTC day).",
    )
    impact_level: str = Field(
        ...,
        description="Classified significance: 'high', 'medium', or 'low'.",
    )
    btc_price_before: float = Field(
        ...,
        description="BTC price 24 hours before the event date.",
    )
    btc_price_after: float = Field(
        ...,
        description="BTC price 24 hours after the event date.",
    )
    price_change_percent: float = Field(
        ...,
        description=(
            "Percentage change from btc_price_before to "
            "btc_price_after (signed)."
        ),
    )
    volatility: float = Field(
        ...,
        description=(
            "Standard deviation of percentage returns over the "
            "48-hour window, in percent."
        ),
    )
    direction: str = Field(
        ...,
        description="Derived direction: 'up', 'down', or 'neutral'.",
    )


# ============================================================
# METRICS
# ============================================================
class EventTypeMetricsResponse(BaseModel):
    """Aggregate metrics for one event type (A5.3).

    Mirrors ``app.events.metrics.EventTypeMetrics``.
    """

    event_type: str = Field(
        ...,
        description=(
            "Canonical type key ('fed', 'cpi', 'gdp', 'employment') "
            "or a normalized free-form name."
        ),
    )
    n_events: int = Field(
        ...,
        description="Number of events aggregated.",
    )
    mean_change: float = Field(
        ...,
        description="Mean price_change_percent, in percent.",
    )
    mean_volatility: float = Field(
        ...,
        description="Mean volatility, in percent.",
    )
    direction_frequencies: Dict[str, float] = Field(
        ...,
        description=(
            "Fraction of events in each direction. Keys are always "
            "'up', 'down', 'neutral'; values sum to 1.0."
        ),
    )
    min_change: float = Field(
        ...,
        description="Minimum price_change_percent, in percent.",
    )
    max_change: float = Field(
        ...,
        description="Maximum price_change_percent, in percent.",
    )
    mean_change_ci: List[float] = Field(
        ...,
        description=(
            "Two-sided confidence interval on mean_change, "
            "as [lower, upper]."
        ),
    )
    confidence_level: float = Field(
        ...,
        description="Confidence level used for the interval (0.95).",
    )


# ============================================================
# FILTERS ECHO
# ============================================================
class EventsFilters(BaseModel):
    """The filters that were applied to this response.

    Echoed back so the caller can confirm what was applied,
    especially when the request used defaults.
    """

    event_type: Optional[List[str]] = Field(
        None,
        description="Canonical event types requested, or null.",
    )
    start_date: Optional[date] = Field(
        None,
        description="Inclusive start of the date range, or null.",
    )
    end_date: Optional[date] = Field(
        None,
        description="Inclusive end of the date range, or null.",
    )


# ============================================================
# TOP-LEVEL RESPONSE
# ============================================================
class EventsResponse(BaseModel):
    """Response for GET /api/v1/events/historical.

    Combines the per-event rows and the per-type aggregates in
    one payload.
    """

    generated_at: datetime = Field(
        ...,
        description="When this response was generated (UTC).",
    )
    count: int = Field(
        ...,
        description="Number of events in the `events` list.",
    )
    filters: EventsFilters = Field(
        ...,
        description="The filters that were applied.",
    )
    events: List[EventResponse] = Field(
        default_factory=list,
        description="The per-event rows, newest first.",
    )
    by_type: Dict[str, EventTypeMetricsResponse] = Field(
        default_factory=dict,
        description=(
            "Aggregate metrics keyed by canonical event type. "
            "Types with fewer than 3 events are omitted."
        ),
    )
    unmapped_names: List[str] = Field(
        default_factory=list,
        description=(
            "Free-form event names that did not match a canonical "
            "type. Those rows are still present in `events` and "
            "aggregated under their normalized key."
        ),
    )
    insufficient: List[str] = Field(
        default_factory=list,
        description=(
            "Event types with fewer than the minimum number of "
            "events required for aggregation."
        ),
    )


# ============================================================
# ERROR RESPONSE
# ============================================================
class EventsErrorResponse(BaseModel):
    """Error payload for 422 responses.

    Matches the shape the correlation and predict endpoints use
    for manually-validated query parameters.
    """

    error: str = Field(
        ...,
        description="Machine-readable error code.",
    )
    message: str = Field(
        ...,
        description="Human-readable error message.",
    )


__all__ = [
    "EventResponse",
    "EventTypeMetricsResponse",
    "EventsErrorResponse",
    "EventsFilters",
    "EventsResponse",
]