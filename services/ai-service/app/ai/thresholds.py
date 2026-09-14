"""Threshold checking for model performance metrics.

This module provides a pure function that compares a model's
performance metrics against configured thresholds and produces
a list of breach records.

Design:
    - Pure function; no I/O, no state
    - Thresholds come from Settings (app/config.py)
    - MAE and RMSE are normalized to percentages of the mean
      actual price before comparison (their raw values are in USD)
    - Directional accuracy is compared as-is (already a percentage)
    - Returns a list of ThresholdCheckResult dataclasses

Thresholds (from Settings):
    - threshold_mae_pct: 10.0 (10% of mean price)
    - threshold_rmse_pct: 15.0
    - threshold_mape: 10.0
    - threshold_directional: 55.0 (percent, minimum)

Metric units used downstream:
    - mae_pct:             percent
    - rmse_pct:            percent
    - mape:                percent
    - directional_accuracy: percent
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Metric identifiers used in the breach records and in the
# threshold_breaches.metric column.
METRIC_MAE_PCT = "mae_pct"
METRIC_RMSE_PCT = "rmse_pct"
METRIC_MAPE = "mape"
METRIC_DIRECTIONAL = "directional_accuracy"

ALL_METRICS = (
    METRIC_MAE_PCT,
    METRIC_RMSE_PCT,
    METRIC_MAPE,
    METRIC_DIRECTIONAL,
)

# Every metric we track uses percent units
METRIC_UNIT_PERCENT = "percent"

# Breach directions
DIRECTION_ABOVE = "above"
DIRECTION_BELOW = "below"


# ============================================================
# RESULT TYPE
# ============================================================
@dataclass
class ThresholdCheckResult:
    """Result of checking one metric against its threshold.

    Attributes:
        metric: 'mae_pct', 'rmse_pct', 'mape', or
            'directional_accuracy'.
        metric_unit: 'percent' (all current metrics).
        value: The metric's actual value.
        threshold: The configured threshold.
        breached: True if the value exceeded the threshold.
        breach_direction: 'above' (for error metrics) or 'below'
            (for directional accuracy). Set even when not breached
            so callers know the expected direction.
    """

    metric: str
    metric_unit: str
    value: float
    threshold: float
    breached: bool
    breach_direction: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "metric": self.metric,
            "metric_unit": self.metric_unit,
            "value": self.value,
            "threshold": self.threshold,
            "breached": self.breached,
            "breach_direction": self.breach_direction,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        status = "BREACH" if self.breached else "ok"
        return (
            f"ThresholdCheckResult(metric='{self.metric}', "
            f"value={self.value:.2f}, "
            f"threshold={self.threshold:.2f}, "
            f"status={status})"
        )


# ============================================================
# NORMALIZATION
# ============================================================
def normalize_usd_to_pct(
    usd_value: Optional[float],
    mean_actual_price: Optional[float],
) -> Optional[float]:
    """Convert an absolute USD error to a percentage of mean price.

    Args:
        usd_value: The error in USD (e.g., MAE = 500.0).
        mean_actual_price: The mean of the actual prices observed
            during the evaluation window (e.g., 50_000.0).

    Returns:
        The error as a percentage of the mean price (e.g., 1.0 for
        1%), or None if either input is missing or non-positive.
    """
    if usd_value is None or mean_actual_price is None:
        return None
    if mean_actual_price <= 0:
        return None
    return (usd_value / mean_actual_price) * 100.0


# ============================================================
# CHECKER
# ============================================================
def check_thresholds(
    mae: Optional[float],
    rmse: Optional[float],
    mape: Optional[float],
    directional_accuracy: Optional[float],
    mean_actual_price: Optional[float],
    thresholds: Optional[Dict[str, float]] = None,
) -> List[ThresholdCheckResult]:
    """Check a set of metrics against configured thresholds.

    MAE and RMSE are in raw USD; they are normalized to percentages
    of `mean_actual_price` before comparison. MAPE and directional
    accuracy are already percentages.

    Args:
        mae: Mean Absolute Error in USD, or None.
        rmse: Root Mean Square Error in USD, or None.
        mape: Mean Absolute Percentage Error, or None.
        directional_accuracy: Directional accuracy in percent
            (0-100), or None.
        mean_actual_price: Mean of the actual prices over the
            evaluation window. Required to normalize MAE/RMSE.
            If None, MAE and RMSE checks are skipped.
        thresholds: Optional override dict. Keys:
            'mae_pct', 'rmse_pct', 'mape', 'directional_accuracy'.
            Defaults to the values in Settings.

    Returns:
        List of ThresholdCheckResult — one per metric that had a
        value to check. Metrics with None values are omitted.
    """
    # Resolve thresholds (argument > settings)
    if thresholds is None:
        thresholds = {
            METRIC_MAE_PCT: settings.threshold_mae * 100.0,       # 0.10 → 10.0
            METRIC_RMSE_PCT: settings.threshold_rmse * 100.0,     # 0.15 → 15.0
            METRIC_MAPE: settings.threshold_mape,                 # 10.0
            METRIC_DIRECTIONAL: settings.threshold_directional,   # 55.0
        }

    results: List[ThresholdCheckResult] = []

    # ---- MAE ----
    mae_pct = normalize_usd_to_pct(mae, mean_actual_price)
    if mae_pct is not None:
        threshold = thresholds[METRIC_MAE_PCT]
        results.append(
            ThresholdCheckResult(
                metric=METRIC_MAE_PCT,
                metric_unit=METRIC_UNIT_PERCENT,
                value=mae_pct,
                threshold=threshold,
                breached=mae_pct > threshold,
                breach_direction=DIRECTION_ABOVE,
            )
        )

    # ---- RMSE ----
    rmse_pct = normalize_usd_to_pct(rmse, mean_actual_price)
    if rmse_pct is not None:
        threshold = thresholds[METRIC_RMSE_PCT]
        results.append(
            ThresholdCheckResult(
                metric=METRIC_RMSE_PCT,
                metric_unit=METRIC_UNIT_PERCENT,
                value=rmse_pct,
                threshold=threshold,
                breached=rmse_pct > threshold,
                breach_direction=DIRECTION_ABOVE,
            )
        )

    # ---- MAPE ----
    if mape is not None:
        threshold = thresholds[METRIC_MAPE]
        results.append(
            ThresholdCheckResult(
                metric=METRIC_MAPE,
                metric_unit=METRIC_UNIT_PERCENT,
                value=mape,
                threshold=threshold,
                breached=mape > threshold,
                breach_direction=DIRECTION_ABOVE,
            )
        )

    # ---- Directional accuracy (lower is worse) ----
    if directional_accuracy is not None:
        threshold = thresholds[METRIC_DIRECTIONAL]
        results.append(
            ThresholdCheckResult(
                metric=METRIC_DIRECTIONAL,
                metric_unit=METRIC_UNIT_PERCENT,
                value=directional_accuracy,
                threshold=threshold,
                breached=directional_accuracy < threshold,
                breach_direction=DIRECTION_BELOW,
            )
        )

    breached_count = sum(1 for r in results if r.breached)
    logger.debug(
        f"Threshold check: {len(results)} metrics, "
        f"{breached_count} breached"
    )

    return results


def filter_breaches(
    results: List[ThresholdCheckResult],
) -> List[ThresholdCheckResult]:
    """Return only the results where `breached` is True.

    Args:
        results: The full list from check_thresholds().

    Returns:
        Filtered list.
    """
    return [r for r in results if r.breached]