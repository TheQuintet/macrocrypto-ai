"""AI Service — Events package.

This package owns the calculation of BTC price reactions to
historical economic events (FOMC meetings, CPI releases, NFP
prints, and so on).

A5.2 ships the reaction calculator. A5.3 will aggregate per-event
reactions into per-event-type metrics. A5.4 will expose both via
an API endpoint. A5.5 will run the calculation as a scheduled job.

Available modules:
    - reaction: pure calculation helpers plus the
      ``ReactionCalculator`` orchestrator.
"""

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
]