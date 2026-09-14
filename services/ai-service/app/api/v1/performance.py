"""Performance API router.

Exposes:
    - GET /api/v1/performance/btc

Returns aggregate model performance metrics for BTC predictions:
    - MAE, RMSE, MAPE, directional accuracy per (model, horizon)
    - Market-condition breakdown (bull/bear/volatile/neutral)
    - Threshold status (recomputed live via check_thresholds)
    - Recent breach count from threshold_breaches

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
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.ai.thresholds import check_thresholds
from app.api.dependencies import get_repository
from app.database.repositories.performance_repository import (
    PerformanceRepository,
)
from app.database.repositories.threshold_repository import (
    ThresholdRepository,
)
from app.database.engine import session_scope
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
async def _build_entry(
    model_name: str,
    horizon: str,
    metrics: dict,
    samples: int,
    days: int,
    perf_repo: PerformanceRepository,
    threshold_repo: ThresholdRepository,
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

    # ---- 2. Threshold status ----
    # We need mean_actual_price to normalize MAE/RMSE. We compute
    # it from the same window we're reporting on.
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
    thresholds = [
        ThresholdStatus(
            metric=c.metric,
            value=c.value,
            threshold=c.threshold,
            breached=c.breached,
            breach_direction=c.breach_direction,
        )
        for c in checks
    ]

    # ---- 3. Recent breach count ----
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

    # ---- 4. Assemble the entry ----
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
        thresholds=thresholds,
        recent_breach_count=recent_breach_count,
        last_updated=metrics.get("forecast_date"),
    )


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
        "breakdown, threshold status, and recent breach count."
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

        # ---- 2. Build one entry per (model, horizon) ----
        entries: List[PerformanceEntry] = []
        for row in latest_rows:
            try:
                entry = await _build_entry(
                    model_name=row["model_name"],
                    horizon=row["horizon"],
                    metrics=row,
                    samples=int(row.get("samples") or 0),
                    days=days,
                    perf_repo=perf_repo,
                    threshold_repo=threshold_repo,
                )
                entries.append(entry)
            except Exception as e:
                logger.error(
                    f"Failed to build entry for "
                    f"{row['model_name']}/{row['horizon']}: {e}",
                    exc_info=True,
                )

    response = PerformanceResponse(
        time_period_days=days,
        generated_at=datetime.now(timezone.utc),
        entries=entries,
    )

    logger.info(
        f"Returning {len(entries)} performance entries "
        f"for {days}-day window"
    )

    return response