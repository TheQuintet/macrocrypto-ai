"""Market condition classification for forecast evaluation.

This module provides a pure classifier that labels a forecast window
as one of four market conditions based on how BTC actually moved
during that window:

    - "volatile": standard deviation of returns > threshold
    - "bull":     cumulative price change > +threshold
    - "bear":     cumulative price change < -threshold
    - "neutral":  none of the above

Priority order (highest first):
    1. volatile — wins over bull/bear, since high volatility is the
       single most important signal for interpreting forecast error
    2. bull / bear — directional moves
    3. neutral — everything else

Thresholds:
    - Default bull/bear threshold: 20% cumulative return
    - Default volatility threshold: 5% std of percentage returns
    - Both are overridable via Settings (see app/config.py)

The classifier is a pure function on a sequence of prices. It does
NOT read from the DB or depend on the ForecastModel interface.

Usage:
    from app.prediction.market import classify_market_condition

    prices = [50000.0, 50500.0, 51200.0, 50800.0, 51500.0]
    label = classify_market_condition(prices)
    # -> "neutral"
"""

import logging
from typing import Optional, Sequence

import numpy as np

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# The four labels the DB CHECK constraint allows.
CONDITION_BULL = "bull"
CONDITION_BEAR = "bear"
CONDITION_VOLATILE = "volatile"
CONDITION_NEUTRAL = "neutral"

ALL_CONDITIONS = (
    CONDITION_BULL,
    CONDITION_BEAR,
    CONDITION_VOLATILE,
    CONDITION_NEUTRAL,
)

# Priority order when multiple conditions could apply.
# Volatile wins over directional labels.
CONDITION_PRIORITY = (
    CONDITION_VOLATILE,
    CONDITION_BULL,
    CONDITION_BEAR,
    CONDITION_NEUTRAL,
)


# ============================================================
# HELPERS
# ============================================================
def cumulative_return_pct(prices: Sequence[float]) -> Optional[float]:
    """Compute the cumulative percentage return over a price series.

    Args:
        prices: Ordered sequence of prices (oldest → newest).

    Returns:
        Percentage change from first to last (e.g. 25.0 for +25%),
        or None if the series is too short or has a non-positive
        first value.
    """
    if prices is None or len(prices) < 2:
        return None

    first = float(prices[0])
    last = float(prices[-1])

    if first <= 0:
        return None

    return (last - first) / first * 100.0


def return_volatility_pct(prices: Sequence[float]) -> Optional[float]:
    """Compute the standard deviation of percentage returns.

    Percentage returns are computed as `pct_change()` between
    consecutive prices. The return is the standard deviation of
    those values, expressed as a decimal fraction (0.05 = 5%),
    matching the "5%" threshold in the ticket.

    Args:
        prices: Ordered sequence of prices (oldest → newest).

    Returns:
        Standard deviation of percentage returns as a decimal
        (e.g. 0.07 for 7%), or None if there are fewer than 3
        prices (we need at least 2 returns for a meaningful std).
    """
    if prices is None or len(prices) < 3:
        return None

    arr = np.asarray(prices, dtype=float)

    if np.any(arr <= 0):
        # Non-positive prices make pct_change undefined
        return None

    # pct_change: (p[i] - p[i-1]) / p[i-1]
    returns = np.diff(arr) / arr[:-1]

    # Guard against inf/nan from any weird input
    if not np.all(np.isfinite(returns)):
        return None

    return float(np.std(returns))


# ============================================================
# CLASSIFIER
# ============================================================
def classify_market_condition(
    prices: Sequence[float],
    bull_threshold_pct: Optional[float] = None,
    bear_threshold_pct: Optional[float] = None,
    volatility_threshold: Optional[float] = None,
) -> Optional[str]:
    """Classify a forecast window's market condition.

    Priority order (first match wins):
        1. volatile — if `return_volatility_pct(prices)` exceeds
           `volatility_threshold` (default: settings.market_volatility_threshold)
        2. bull — if `cumulative_return_pct(prices) > bull_threshold_pct`
        3. bear — if `cumulative_return_pct(prices) < -bear_threshold_pct`
        4. neutral — otherwise

    Returns None (rather than a label) when there isn't enough data
    to make a determination. Callers should treat None as "unknown"
    and store NULL in the DB.

    Args:
        prices: Ordered sequence of prices (oldest → newest).
        bull_threshold_pct: Override for the bull threshold
            (default: settings.market_bull_threshold_pct).
        bear_threshold_pct: Override for the bear threshold
            (default: settings.market_bear_threshold_pct).
        volatility_threshold: Override for the volatility threshold
            as a decimal (default: settings.market_volatility_threshold).

    Returns:
        One of "bull", "bear", "volatile", "neutral", or None if
        the series is too short to classify.

    Examples:
        >>> classify_market_condition([100.0, 130.0])
        'bull'
        >>> classify_market_condition([100.0, 70.0])
        'bear'
        >>> classify_market_condition([100.0, 105.0])
        'neutral'
        >>> classify_market_condition([100.0])
        None
    """
    # Resolve thresholds (argument > setting > hardcoded default)
    bull_t = (
        bull_threshold_pct
        if bull_threshold_pct is not None
        else settings.market_bull_threshold_pct
    )
    bear_t = (
        bear_threshold_pct
        if bear_threshold_pct is not None
        else settings.market_bear_threshold_pct
    )
    vol_t = (
        volatility_threshold
        if volatility_threshold is not None
        else settings.market_volatility_threshold
    )

    if prices is None or len(prices) < 2:
        logger.debug("Not enough prices to classify market condition")
        return None

    # ---- 1. Volatility (highest priority) ----
    volatility = return_volatility_pct(prices)
    if volatility is not None and volatility > vol_t:
        logger.debug(
            f"Classified as 'volatile': std={volatility:.4f} > "
            f"threshold={vol_t:.4f}"
        )
        return CONDITION_VOLATILE

    # ---- 2. Directional ----
    change = cumulative_return_pct(prices)
    if change is None:
        return None

    if change > bull_t:
        logger.debug(
            f"Classified as 'bull': change={change:.2f}% > "
            f"threshold={bull_t:.2f}%"
        )
        return CONDITION_BULL

    if change < -bear_t:
        logger.debug(
            f"Classified as 'bear': change={change:.2f}% < "
            f"-{bear_t:.2f}%"
        )
        return CONDITION_BEAR

    # ---- 3. Fallback ----
    logger.debug(
        f"Classified as 'neutral': change={change:.2f}%, "
        f"std={volatility if volatility is not None else 0.0:.4f}"
    )
    return CONDITION_NEUTRAL


def classify_market_condition_safe(
    prices: Sequence[float],
) -> Optional[str]:
    """Classify with the default thresholds, swallowing exceptions.

    Wraps `classify_market_condition` in a try/except so callers
    (like the backtest job) don't crash on unexpected input.

    Args:
        prices: Ordered sequence of prices (oldest → newest).

    Returns:
        The condition label, or None on any failure.
    """
    try:
        return classify_market_condition(prices)
    except Exception as e:
        logger.warning(
            f"Failed to classify market condition: {e}"
        )
        return None