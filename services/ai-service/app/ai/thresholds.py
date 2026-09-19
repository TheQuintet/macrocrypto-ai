"""Threshold checking and streak monitoring for model performance.

This module provides:
    - A pure threshold checker that compares a model's metrics
      against configured thresholds and produces breach records
    - A streak evaluator that turns per-metric breach streaks into
      warnings (used by T5.6's 3-day escalation rule)

Threshold checking:
    - MAE and RMSE are normalized to percentages of mean actual
      price before comparison (their raw values are in USD)
    - Directional accuracy is compared as-is (already a percentage)
    - Returns a list of ThresholdCheckResult dataclasses

Streak evaluation (T5.6):
    - Given a map of metric → consecutive_days, decides which
      metrics have crossed the warning threshold
    - Defaults to `settings.threshold_warning_streak_days` (3)
    - Returns a StreakWarningResult with per-metric details

Thresholds (from Settings):
    - threshold_mae_pct: 10.0 (10% of mean price)
    - threshold_rmse_pct: 15.0
    - threshold_mape: 10.0
    - threshold_directional: 55.0 (percent, minimum)
    - threshold_warning_streak_days: 3

Metric units used downstream:
    - mae_pct:             percent
    - rmse_pct:            percent
    - mape:                percent
    - directional_accuracy: percent
"""

import logging
from dataclasses import dataclass, field
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
# RESULT TYPES
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


@dataclass
class StreakInfo:
    """Streak information for one metric.

    Attributes:
        metric: Metric identifier.
        consecutive_days: Number of consecutive days the metric has
            been breaching. Zero if not currently breaching.
        warning: True if `consecutive_days >= warning_threshold`.
    """

    metric: str
    consecutive_days: int = 0
    warning: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "metric": self.metric,
            "consecutive_days": self.consecutive_days,
            "warning": self.warning,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        status = "WARNING" if self.warning else "ok"
        return (
            f"StreakInfo(metric='{self.metric}', "
            f"days={self.consecutive_days}, "
            f"status={status})"
        )


@dataclass
class StreakWarningResult:
    """Aggregated streak warnings for one (model, horizon).

    Attributes:
        streaks: Mapping of metric identifier → StreakInfo.
        any_warning: True if at least one metric has a warning.
        warning_count: Number of metrics currently warning.
        warning_threshold: The streak-day threshold used for the
            decision (from settings by default).
    """

    streaks: Dict[str, StreakInfo] = field(default_factory=dict)
    any_warning: bool = False
    warning_count: int = 0
    warning_threshold: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "streaks": {
                name: info.to_dict()
                for name, info in self.streaks.items()
            },
            "any_warning": self.any_warning,
            "warning_count": self.warning_count,
            "warning_threshold": self.warning_threshold,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        status = "WARNING" if self.any_warning else "ok"
        return (
            f"StreakWarningResult(warnings={self.warning_count}, "
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
    if thresholds is None:
        thresholds = {
            METRIC_MAE_PCT: settings.threshold_mae * 100.0,
            METRIC_RMSE_PCT: settings.threshold_rmse * 100.0,
            METRIC_MAPE: settings.threshold_mape,
            METRIC_DIRECTIONAL: settings.threshold_directional,
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


# ============================================================
# STREAK EVALUATION (T5.6)
# ============================================================
def evaluate_streaks(
    consecutive_days_by_metric: Dict[str, int],
    warning_threshold: Optional[int] = None,
) -> StreakWarningResult:
    """Evaluate per-metric breach streaks against the warning rule.

    A metric "warns" when its `consecutive_days` is >= the
    configured warning threshold (default:
    `settings.threshold_warning_streak_days`, currently 3).

    Args:
        consecutive_days_by_metric: Mapping of metric identifier
            → number of consecutive days it has breached. Metrics
            not present are treated as having 0 consecutive days.
        warning_threshold: Optional override. If None, uses the
            value from settings.

    Returns:
        StreakWarningResult with one StreakInfo per known metric
        (i.e., every metric in ALL_METRICS is represented — even
        those with zero consecutive days, for API stability).
    """
    if warning_threshold is None:
        warning_threshold = settings.threshold_warning_streak_days

    streaks: Dict[str, StreakInfo] = {}
    warning_count = 0

    for metric in ALL_METRICS:
        days = int(consecutive_days_by_metric.get(metric, 0))
        warning = days >= warning_threshold
        if warning:
            warning_count += 1
        streaks[metric] = StreakInfo(
            metric=metric,
            consecutive_days=days,
            warning=warning,
        )

    result = StreakWarningResult(
        streaks=streaks,
        any_warning=warning_count > 0,
        warning_count=warning_count,
        warning_threshold=warning_threshold,
    )

    if warning_count > 0:
        logger.warning(
            f"Threshold streak warnings: {warning_count} metric(s) "
            f"at or above {warning_threshold} consecutive days "
            f"({[s.metric for s in streaks.values() if s.warning]})"
        )
    else:
        logger.debug(
            f"Threshold streaks: no metric reached "
            f"{warning_threshold} consecutive days"
        )

    return result


def consecutive_days_to_metric_map(
    rows: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Turn a list of breach rows into a metric → consecutive_days map.

    Intended to consume the output of
    `ThresholdRepository.fetch_latest_breaches_batch()` filtered to
    one (model, horizon).

    Rows with a `consecutive_days` value of 0 (or absent) are
    skipped. Duplicate metrics keep the max value.

    Args:
        rows: List of dicts, each with 'metric' and
            'consecutive_days' keys.

    Returns:
        Dict of metric → consecutive_days.
    """
    result: Dict[str, int] = {}
    for row in rows:
        metric = row.get("metric")
        days = int(row.get("consecutive_days") or 0)
        if metric is None or days <= 0:
            continue
        result[metric] = max(result.get(metric, 0), days)
    return result