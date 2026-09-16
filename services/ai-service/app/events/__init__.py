"""AI Service — Events package.

This package owns the calculation of BTC price reactions to
historical economic events (FOMC meetings, CPI releases, NFP
prints, and so on) and the aggregation of those reactions into
per-event-type metrics.

A5.2 ships the reaction calculator. A5.3 ships the metrics
calculator. A5.4 will expose both via an API endpoint. A5.5 will
run the reaction calculation as a scheduled job.

Available modules:
    - reaction: pure calculation helpers plus the
      ``ReactionCalculator`` orchestrator.
    - metrics: pure aggregation helpers plus the
      ``EventMetricsCalculator`` orchestrator.
"""

from app.events.metrics import (
    CANONICAL_EVENT_TYPES,
    CONFIDENCE_LEVEL,
    EVENT_TYPE_ALIASES,
    MIN_EVENTS_FOR_METRICS,
    EventMetricsCalculator,
    EventTypeMetrics,
    MetricsCalculationResult,
    aggregate_by_type,
    aggregate_event_type,
    confidence_interval,
    direction_frequencies,
    mean_change,
    mean_volatility,
    min_max_change,
    normalize_event_type,
)
from app.events.reaction import (
    DIRECTION_THRESHOLD_PCT,
    MIN_PRICE_POINTS,
    PRICE_LOOKUP_TOLERANCE_HOURS,
    PRICE_WINDOW_HOURS_AFTER,
    PRICE_WINDOW_HOURS_BEFORE,
    ReactionCalculationResult,
    ReactionCalculator,
    ReactionSkip,
    classify_direction,
    price_change_percent,
    volatility_pct,
)

__all__ = [
    # reaction.py
    "DIRECTION_THRESHOLD_PCT",
    "MIN_PRICE_POINTS",
    "PRICE_LOOKUP_TOLERANCE_HOURS",
    "PRICE_WINDOW_HOURS_AFTER",
    "PRICE_WINDOW_HOURS_BEFORE",
    "ReactionCalculationResult",
    "ReactionCalculator",
    "ReactionSkip",
    "classify_direction",
    "price_change_percent",
    "volatility_pct",
    # metrics.py
    "CANONICAL_EVENT_TYPES",
    "CONFIDENCE_LEVEL",
    "EVENT_TYPE_ALIASES",
    "MIN_EVENTS_FOR_METRICS",
    "EventMetricsCalculator",
    "EventTypeMetrics",
    "MetricsCalculationResult",
    "aggregate_by_type",
    "aggregate_event_type",
    "confidence_interval",
    "direction_frequencies",
    "mean_change",
    "mean_volatility",
    "min_max_change",
    "normalize_event_type",
]