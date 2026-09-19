"""Performance API router.

Exposes:
    - GET /api/v1/performance/btc

Returns aggregate model performance metrics for BTC predictions:
    - MAE, RMSE, MAPE, directional accuracy per (model, horizon)
    - Market-condition breakdown (bull/bear/volatile/neutral)
    - Threshold status (recomputed live via check_thresholds)
    - Recent breach count from threshold_breaches
    - Per-metric streak info + warning flag (T5.6)

Design:
    - Reads from prediction_performance + threshold_breaches
    - Recomputes thresholds on-read via app.ai.thresholds
    - Returns a list of entries (one per model-horizon pair)
    - Supports optional ?model_name= and ?horizon= filters
    - No JWT auth (deferred, same as T1.4)
    - No rate limiting (deferred, same as T1.4)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.thresholds import (
    StreakWarningResult,
    check_thresholds,
    consecutive_days_to_metric_map,
    evaluate_streaks,
)
from app.api.dependencies import get_repository
from app.database.engine import session_scope
from app.database.repositories.performance_repository import (
    PerformanceRepository,
)
from app.database.repositories.threshold_repository import (
    ThresholdRepository,
)
from app.schemas.performance import (
    MarketBreakdownEntry,
    PerformanceEntry,
    PerformanceErrorResponse,
    PerformanceMetrics,
    PerformanceResponse,
    ThresholdStatus,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
VALID_HORIZONS = ("24h", "7d")
DEFAULT_DAYS = 30
MAX_DAYS = 365


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/performance",
    tags=["performance"],
)


# ============================================================
# HELPERS
# ============================================================
def _as_float(value) -> Optional[float]:
    """Return a float if value is not None, else None."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def _get_mean_actual_price(
    perf_repo: PerformanceRepository,
    horizon: str,
    model_name: str,
    days: int,
) -> Optional[float]:
    """Return the mean actual price over the recent evaluation window.

    Args:
        perf_repo: The performance repository (its session is used).
        horizon: Horizon label.
        model_name: Model identifier.
        days: How far back to average.

    Returns:
        Mean actual price, or None if no rows exist.
    """
    from datetime import timedelta

    from sqlalchemy import func, select

    from app.database.tables import prediction_performance

    since = datetime.now(timezone.utc) - timedelta(days=days)

    stmt = select(
        func.avg(prediction_performance.c.actual_price)
    ).where(
        prediction_performance.c.horizon == horizon,
        prediction_performance.c.model_name == model_name,
        prediction_performance.c.forecast_date >= since,
    )

    result = await perf_repo.session.execute(stmt)
    value = result.scalar_one_or_none()

    if value is None:
        return None

    return float(value)


def _build_threshold_status(
    checks,
    streak_map: Dict[str, int],
) -> List[ThresholdStatus]:
    """Merge threshold checks with streak info.

    Args:
        checks: List of ThresholdCheckResult from check_thresholds.
        streak_map: Metric → consecutive_days from the batch read.

    Returns:
        List of ThresholdStatus with streak + warning populated.
    """
    from app.config import settings

    warning_threshold = settings.threshold_warning_streak_days
    statuses: List[ThresholdStatus] = []

    for c in checks:
        days = int(streak_map.get(c.metric, 0))
        warning = days >= warning_threshold

        statuses.append(
            ThresholdStatus(
                metric=c.metric,
                value=c.value,
                threshold=c.threshold,
                breached=c.breached,
                breach_direction=c.breach_direction,
                consecutive_days=days,
                warning=warning,
            )
        )

    return statuses


async def _build_entry(
    model_name: str,
    horizon: str,
    metrics: dict,
    samples: int,
    days: int,
    perf_repo: PerformanceRepository,
    threshold_repo: ThresholdRepository,
    streaks_for_key: List[Dict[str, Any]],
) -> PerformanceEntry:
    """Build one PerformanceEntry for a (model, horizon) pair.

    Args:
        model_name: Model identifier.
        horizon: Horizon label.
        metrics: Dict from fetch_latest_metrics_batch.
        samples: Number of matched points in the window.
        days: Look-back window.
        perf_repo: Performance repository (for market breakdown).
        threshold_repo: Threshold repository (for breach count).
        streaks_for_key: The batch-read streak rows filtered to
            this (model, horizon).

    Returns:
        A fully populated PerformanceEntry.
    """
    # ---- 1. Market breakdown ----
    breakdown_rows = await perf_repo.fetch_market_breakdown(
        horizon=horizon,
        model_name=model_name,
        days=days,
    )
    market_breakdown = {
        row["market_condition"]: MarketBreakdownEntry(
            mae=_as_float(row.get("mae")),
            rmse=_as_float(row.get("rmse")),
            mape=_as_float(row.get("mape")),
            samples=int(row.get("samples") or 0),
        )
        for row in breakdown_rows
    }

    # ---- 2. Threshold checks + streak info ----
    mean_actual_price = await _get_mean_actual_price(
        perf_repo=perf_repo,
        horizon=horizon,
        model_name=model_name,
        days=days,
    )

    checks = check_thresholds(
        mae=metrics.get("mae"),
        rmse=metrics.get("rmse"),
        mape=metrics.get("mape"),
        directional_accuracy=None,  # not stored per-row yet
        mean_actual_price=mean_actual_price,
    )

    streak_map = consecutive_days_to_metric_map(streaks_for_key)
    threshold_statuses = _build_threshold_status(checks, streak_map)

    # ---- 3. Aggregate warning state ----
    streak_result: StreakWarningResult = evaluate_streaks(streak_map)
    if streak_result.any_warning:
        logger.warning(
            f"Performance warning for {model_name}/{horizon}: "
            f"{streak_result.warning_count} metric(s) at or above "
            f"{streak_result.warning_threshold} consecutive days"
        )

    # ---- 4. Recent breach count ----
    try:
        recent_breach_count = await threshold_repo.count_breaches(
            horizon=horizon,
            model_name=model_name,
            since_days=days,
        )
    except Exception as e:
        logger.warning(
            f"Failed to count breaches for {model_name}/{horizon}: {e}"
        )
        recent_breach_count = 0

    # ---- 5. Assemble the entry ----
    return PerformanceEntry(
        model_name=model_name,
        model_version=metrics.get("model_version"),
        horizon=horizon,
        samples=samples,
        metrics=PerformanceMetrics(
            mae=_as_float(metrics.get("mae")),
            rmse=_as_float(metrics.get("rmse")),
            mape=_as_float(metrics.get("mape")),
            directional_accuracy=None,
        ),
        market_breakdown=market_breakdown,
        thresholds=threshold_statuses,
        recent_breach_count=recent_breach_count,
        last_updated=metrics.get("forecast_date"),
        warning=streak_result.any_warning,
        warning_count=streak_result.warning_count,
        warning_threshold_days=streak_result.warning_threshold,
    )


# ============================================================
# ENDPOINT
# ============================================================
@router.get(
    "/btc",
    response_model=PerformanceResponse,
    responses={
        422: {
            "model": PerformanceErrorResponse,
            "description": "Invalid query parameters.",
        },
    },
    summary="Get BTC prediction performance metrics",
    description=(
        "Return aggregate performance metrics for all model-horizon "
        "pairs over a configurable look-back window. Includes MAE, "
        "RMSE, MAPE, directional accuracy, market-condition "
        "breakdown, threshold status, and per-metric streak "
        "warnings (3-day rule by default)."
    ),
)
async def get_btc_performance(
    days: int = Query(
        default=DEFAULT_DAYS,
        ge=1,
        le=MAX_DAYS,
        description=(
            f"Look-back window in days (1-{MAX_DAYS}). "
            f"Default {DEFAULT_DAYS}."
        ),
    ),
    horizon: Optional[Literal["24h", "7d"]] = Query(
        default=None,
        description=(
            "Optional horizon filter. If omitted, all horizons "
            "are returned."
        ),
    ),
    model_name: Optional[str] = Query(
        default=None,
        description=(
            "Optional model name filter. If omitted, all models "
            "are returned."
        ),
    ),
) -> PerformanceResponse:
    """Return aggregate performance metrics for BTC predictions.

    Args:
        days: Look-back window.
        horizon: Optional horizon filter ('24h' or '7d').
        model_name: Optional model filter.

    Returns:
        PerformanceResponse with one entry per (model, horizon)
        pair that has metrics in the window.

    Raises:
        HTTPException: 422 if a filter is invalid.
    """
    logger.info(
        f"GET /api/v1/performance/btc "
        f"(days={days}, horizon={horizon}, model_name={model_name})"
    )

    async with session_scope() as session:
        perf_repo = PerformanceRepository(session)
        threshold_repo = ThresholdRepository(session)

        # ---- 1. Fetch latest metrics per (model, horizon) ----
        latest_rows = await perf_repo.fetch_latest_metrics_batch(
            days=days,
            horizon=horizon,
            model_name=model_name,
        )

        # ---- 2. Fetch latest breaches batch (for streaks) ----
        streak_rows = await threshold_repo.fetch_latest_breaches_batch(
            since_days=days,
        )

        # ---- 3. Group streaks by (model, horizon) ----
        streaks_by_key: Dict[tuple, List[Dict[str, Any]]] = {}
        for row in streak_rows:
            key = (row["model_name"], row["horizon"])
            streaks_by_key.setdefault(key, []).append(row)

        # ---- 4. Build one entry per (model, horizon) ----
        entries: List[PerformanceEntry] = []
        for row in latest_rows:
            key = (row["model_name"], row["horizon"])
            try:
                entry = await _build_entry(
                    model_name=row["model_name"],
                    horizon=row["horizon"],
                    metrics=row,
                    samples=int(row.get("samples") or 0),
                    days=days,
                    perf_repo=perf_repo,
                    threshold_repo=threshold_repo,
                    streaks_for_key=streaks_by_key.get(key, []),
                )
                entries.append(entry)
            except Exception as e:
                logger.error(
                    f"Failed to build entry for "
                    f"{row['model_name']}/{row['horizon']}: {e}",
                    exc_info=True,
                )

    # ---- 5. Aggregate warnings ----
    # `warnings_count` is the total number of warned *metrics* across
    # all entries, not the number of entries that contain a warning.
    # A single entry with 3 warned metrics contributes 3 here.
    warnings_count = sum(e.warning_count for e in entries)

    response = PerformanceResponse(
        time_period_days=days,
        generated_at=datetime.now(timezone.utc),
        entries=entries,
        warnings_count=warnings_count,
    )

    logger.info(
        f"Returning {len(entries)} performance entries "
        f"for {days}-day window ({warnings_count} warnings)"
    )

    return response