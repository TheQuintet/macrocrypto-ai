"""Trend direction calculation for forecasts.

This module provides a pure function that determines the trend
direction (up / down / neutral) of a forecast, based on the
percentage change between the current price and the predicted
end price.

The thresholds are horizon-dependent:
    - 24h horizon: ±0.5% (per T1.7)
    - 7d horizon:  ±1.0% (per T2.6)

Design:
    - Pure function, no I/O, no state
    - Returns both the trend and the percentage change so callers
      can use them independently
    - Defensive against None / zero / negative current prices
"""

import logging
from typing import Optional, Tuple

from app.schemas.prediction import TrendDirection

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Percentage thresholds for trend classification.
# A change strictly greater than +threshold is UP;
# strictly less than -threshold is DOWN; otherwise NEUTRAL.
TREND_THRESHOLD_24H = 0.5  # ±0.5%
TREND_THRESHOLD_7D = 1.0   # ±1.0%

# Default threshold used when horizon is unknown
TREND_THRESHOLD_DEFAULT = TREND_THRESHOLD_24H

# Map horizon labels to thresholds
TREND_THRESHOLDS = {
    "24h": TREND_THRESHOLD_24H,
    "7d": TREND_THRESHOLD_7D,
}


# ============================================================
# PERCENTAGE CHANGE
# ============================================================
def calculate_price_change_pct(
    current_price: Optional[float],
    predicted_end_price: float,
) -> Optional[float]:
    """Calculate the percentage change from current to predicted price.

    Returns None if the current price is missing or not strictly
    positive, since a percentage change cannot be computed in
    those cases.

    Args:
        current_price: The current (latest) price. May be None.
        predicted_end_price: The predicted price at the end of the
            forecast horizon.

    Returns:
        The percentage change as a float (e.g., 1.10 for +1.10%),
        or None if it cannot be computed.

    Example:
        >>> calculate_price_change_pct(100.0, 101.0)
        1.0
        >>> calculate_price_change_pct(None, 101.0) is None
        True
        >>> calculate_price_change_pct(0.0, 101.0) is None
        True
    """
    if current_price is None:
        return None

    if current_price <= 0:
        logger.debug(
            f"Cannot compute percentage change: "
            f"current_price={current_price} is not positive"
        )
        return None

    change = (predicted_end_price - current_price) / current_price * 100.0
    return float(change)


# ============================================================
# TREND DIRECTION
# ============================================================
def calculate_trend(
    current_price: Optional[float],
    predicted_end_price: float,
    horizon: str = "24h",
) -> TrendDirection:
    """Determine the trend direction of a forecast.

    Classification:
        - change > +threshold  → UP
        - change < -threshold  → DOWN
        - otherwise            → NEUTRAL

    If the current price is missing or non-positive, the trend is
    NEUTRAL (we cannot reason about direction without a baseline).

    Args:
        current_price: The current (latest) price. May be None.
        predicted_end_price: The predicted price at the end of the
            forecast horizon.
        horizon: The forecast horizon ("24h" or "7d"). Determines
            the threshold. Unknown horizons fall back to the 24h
            threshold.

    Returns:
        A TrendDirection enum value.

    Example:
        >>> calculate_trend(100.0, 101.0, "24h")
        <TrendDirection.UP: 'up'>
        >>> calculate_trend(100.0, 100.2, "24h")
        <TrendDirection.NEUTRAL: 'neutral'>
        >>> calculate_trend(100.0, 99.0, "24h")
        <TrendDirection.DOWN: 'down'>
        >>> calculate_trend(None, 101.0, "24h")
        <TrendDirection.NEUTRAL: 'neutral'>
    """
    # Resolve the threshold for the given horizon
    threshold = TREND_THRESHOLDS.get(horizon, TREND_THRESHOLD_DEFAULT)

    change_pct = calculate_price_change_pct(current_price, predicted_end_price)

    if change_pct is None:
        return TrendDirection.NEUTRAL

    if change_pct > threshold:
        return TrendDirection.UP

    if change_pct < -threshold:
        return TrendDirection.DOWN

    return TrendDirection.NEUTRAL


# ============================================================
# COMBINED HELPER
# ============================================================
def calculate_trend_and_change(
    current_price: Optional[float],
    predicted_end_price: float,
    horizon: str = "24h",
) -> Tuple[TrendDirection, Optional[float]]:
    """Compute both trend direction and percentage change.

    Convenience function for callers that need both values — avoids
    computing the percentage change twice.

    Args:
        current_price: The current (latest) price. May be None.
        predicted_end_price: The predicted price at the end of the
            forecast horizon.
        horizon: The forecast horizon ("24h" or "7d").

    Returns:
        A tuple (trend, price_change_pct).
        `price_change_pct` is None when `current_price` is None or
        non-positive.
    """
    change_pct = calculate_price_change_pct(current_price, predicted_end_price)
    threshold = TREND_THRESHOLDS.get(horizon, TREND_THRESHOLD_DEFAULT)

    if change_pct is None:
        trend = TrendDirection.NEUTRAL
    elif change_pct > threshold:
        trend = TrendDirection.UP
    elif change_pct < -threshold:
        trend = TrendDirection.DOWN
    else:
        trend = TrendDirection.NEUTRAL

    return trend, change_pct