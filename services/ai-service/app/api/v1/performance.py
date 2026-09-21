"""Performance API router.

Exposes:
    - GET /api/v1/performance/btc

Returns aggregate model performance metrics for BTC predictions:
    - MAE, RMSE, MAPE, directional accuracy per (model, horizon)
    - Market-condition breakdown (bull/bear/volatile/neutral)
    - Threshold status (recomputed live via check_thresholds)
    - Recent breach count from threshold_breaches
    - Per-metric streak info + warning flag (T5.6)
    - Historical aggregate points per entry (M8, behind
      ?include_history=true)
    - Best model by mean MAE over the window (M8, always present)

Design:
    - Reads from prediction_performance + threshold_breaches for the
      current snapshot; reads from model_performance for history
      and best-model lookup (both tables are AI Service-owned)
    - Recomputes thresholds on-read via app.ai.thresholds
    - Returns a list of entries (one per model-horizon pair)
    - Supports ?model_name= (single) and ?models= (comma-separated).
      `model_name` is sugar for a one-element `models` list; when both
      are provided, `models` wins and a warning is logged. Unknown
      model names are silently ignored (filtered out) — the response
      simply has no entry for them.
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
from app.database.repositories.model_performance_repository import (
    ModelPerformanceRepository,
)
from app.database.repositories.performance_repository import (
    PerformanceRepository,
)
from app.database.repositories.threshold_repository import (
    ThresholdRepository,
)
from app.schemas.performance import (
    MarketBreakdownEntry,
    ModelHistoryPoint,
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
DEFAULT_HISTORY_LIMIT = 30
MAX_HISTORY_LIMIT = 90


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/performance",
    tags=["performance"],
)


# ============================================================
# HELPERS — model filter parsing (M8)
# ============================================================
def _parse_models(models_param: Optional[str]) -> Optional[List[str]]:
    """Parse the ?models= query parameter.

    Rules:
        - None → None (no filter)
        - Whitespace-only → None (treat as unset)
        - Comma-separated names are stripped of whitespace
        - Empty segments (leading, trailing, doubled comma) → 422
        - Duplicates are deduplicated (first occurrence order kept)

    Malformed input (empty segments) is rejected with 422 because
    it almost certainly indicates a typo. Well-formed names that
    happen to be unknown are NOT rejected here — the endpoint
    filters them out silently, matching the M6a convention.

    Args:
        models_param: Raw string from the query parameter, or None.

    Returns:
        List of unique model names, or None when no filter is
        requested.

    Raises:
        HTTPException: 422 when the parameter is malformed.
    """
    if models_param is None:
        return None

    stripped = models_param.strip()
    if stripped == "":
        return None

    raw_parts = stripped.split(",")
    names = [p.strip() for p in raw_parts]

    if any(name == "" for name in names):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_models",
                "message": (
                    "Empty model name in ?models= — the parameter "
                    "must be a comma-separated list of model names "
                    "with no leading, trailing, or doubled commas"
                ),
            },
        )

    # Deduplicate, preserving first-seen order
    seen: set = set()
    deduped: List[str] = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        deduped.append(name)

    return deduped


def _merge_model_filters(
    models_param: Optional[str],
    model_name_param: Optional[str],
) -> Optional[List[str]]:
    """Collapse `?models=` and `?model_name=` into one filter list.

    Semantics:
        - `?model_name=x` is treated as sugar for `?models=x`.
        - If both are provided, `?models=` wins and a warning is
          logged so operators can spot the confusion in logs.
        - If neither is provided, returns None (no filter).

    Args:
        models_param: Raw `?models=` value, or None.
        model_name_param: Raw `?model_name=` value, or None.

    Returns:
        A list of model names to filter by, or None.

    Raises:
        HTTPException: 422 when `?models=` is malformed.
    """
    parsed = _parse_models(models_param)

    if parsed is not None and model_name_param:
        logger.warning(
            f"Both ?models= and ?model_name= provided "
            f"(models={models_param!r}, model_name={model_name_param!r}); "
            f"?models= wins"
        )
        return parsed

    if parsed is not None:
        return parsed

    if model_name_param:
        return [model_name_param]

    return None


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


def _rows_to_history(
    rows: List[Dict[str, Any]],
) -> List[ModelHistoryPoint]:
    """Convert model_performance rows to ModelHistoryPoint objects.

    Rows come from ModelPerformanceRepository.fetch_history() and
    are already ordered ascending by calculated_at.

    Args:
        rows: List of dicts with keys calculated_at, mae, rmse,
            mape, directional_accuracy, sample_size.

    Returns:
        List of ModelHistoryPoint, one per input row.
    """
    return [
        ModelHistoryPoint(
            calculated_at=row["calculated_at"],
            mae=_as_float(row.get("mae")),
            rmse=_as_float(row.get("rmse")),
            mape=_as_float(row.get("mape")),
            directional_accuracy=_as_float(
                row.get("directional_accuracy")
            ),
            sample_size=int(row.get("sample_size") or 0),
        )
        for row in rows
    ]


async def _build_entry(
    model_name: str,
    horizon: str,
    metrics: dict,
    samples: int,
    days: int,
    perf_repo: PerformanceRepository,
    threshold_repo: ThresholdRepository,
    model_perf_repo: ModelPerformanceRepository,
    streaks_for_key: List[Dict[str, Any]],
    include_history: bool,
    history_limit: int,
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
        model_perf_repo: Model performance repository (for history).
        streaks_for_key: The batch-read streak rows filtered to
            this (model, horizon).
        include_history: When True, fetch and attach the historical
            time series from model_performance.
        history_limit: Maximum number of history points to attach.

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

    # ---- 5. History (M8, opt-in) ----
    history: List[ModelHistoryPoint] = []
    if include_history:
        try:
            history_rows = await model_perf_repo.fetch_history(
                model_name=model_name,
                horizon=horizon,
                days=days,
            )
            # fetch_history returns ascending by calculated_at.
            # Apply the limit as "the most recent N points",
            # keeping ascending order.
            if len(history_rows) > history_limit:
                history_rows = history_rows[-history_limit:]
            history = _rows_to_history(history_rows)
        except Exception as e:
            logger.warning(
                f"Failed to fetch history for "
                f"{model_name}/{horizon}: {e}"
            )
            history = []

    # ---- 6. Assemble the entry ----
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
        history=history,
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
        "warnings (3-day rule by default).\n\n"
        "Set `include_history=true` to attach the historical "
        "aggregate series for each entry (from the pre-aggregated "
        "model_performance table). The envelope also includes "
        "`best_model` — the model with the lowest mean MAE over the "
        "window — whenever any entry has MAE data."
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
            "Optional single-model filter. Sugar for ?models= with "
            "one element. If both are provided, ?models= wins."
        ),
    ),
    models: Optional[str] = Query(
        default=None,
        description=(
            "Optional comma-separated model filter. When provided, "
            "only entries for those models are returned. Unknown "
            "model names are silently ignored."
        ),
    ),
    include_history: bool = Query(
        default=False,
        description=(
            "When true, attach a `history` array to each entry "
            "containing historical aggregate points from the "
            "model_performance table, ordered oldest-first."
        ),
    ),
    history_limit: int = Query(
        default=DEFAULT_HISTORY_LIMIT,
        ge=1,
        le=MAX_HISTORY_LIMIT,
        description=(
            f"Maximum number of history points per entry "
            f"(1-{MAX_HISTORY_LIMIT}). Only used when "
            f"include_history=true. The most recent N points are "
            f"returned."
        ),
    ),
) -> PerformanceResponse:
    """Return aggregate performance metrics for BTC predictions.

    Args:
        days: Look-back window.
        horizon: Optional horizon filter ('24h' or '7d').
        model_name: Optional single-model filter.
        models: Optional comma-separated model filter.
        include_history: When True, attach per-entry history.
        history_limit: Max history points per entry.

    Returns:
        PerformanceResponse with one entry per (model, horizon)
        pair that has metrics in the window.

    Raises:
        HTTPException: 422 if a filter is invalid.
    """
    # ---- 0. Resolve the model filter ----
    model_filter = _merge_model_filters(models, model_name)

    logger.info(
        f"GET /api/v1/performance/btc "
        f"(days={days}, horizon={horizon}, model_filter={model_filter}, "
        f"include_history={include_history}, "
        f"history_limit={history_limit})"
    )

    async with session_scope() as session:
        perf_repo = PerformanceRepository(session)
        threshold_repo = ThresholdRepository(session)
        model_perf_repo = ModelPerformanceRepository(session)

        # ---- 1. Fetch latest metrics per (model, horizon) ----
        # We do NOT push the model filter into the SQL: the
        # repository's single-model filter takes one name, and
        # adding an IN-style parameter would touch
        # PerformanceRepository, which is out of M8's scope.
        # Python-side filtering over at most 12 rows is free.
        latest_rows = await perf_repo.fetch_latest_metrics_batch(
            days=days,
            horizon=horizon,
        )

        # ---- 2. Apply the model filter (if any) ----
        if model_filter is not None:
            wanted = set(model_filter)
            latest_rows = [
                row for row in latest_rows
                if row["model_name"] in wanted
            ]

        # ---- 3. Fetch latest breaches batch (for streaks) ----
        streak_rows = await threshold_repo.fetch_latest_breaches_batch(
            since_days=days,
        )

        # ---- 4. Group streaks by (model, horizon) ----
        streaks_by_key: Dict[tuple, List[Dict[str, Any]]] = {}
        for row in streak_rows:
            key = (row["model_name"], row["horizon"])
            streaks_by_key.setdefault(key, []).append(row)

        # ---- 5. Build one entry per (model, horizon) ----
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
                    model_perf_repo=model_perf_repo,
                    streaks_for_key=streaks_by_key.get(key, []),
                    include_history=include_history,
                    history_limit=history_limit,
                )
                entries.append(entry)
            except Exception as e:
                logger.error(
                    f"Failed to build entry for "
                    f"{row['model_name']}/{row['horizon']}: {e}",
                    exc_info=True,
                )

        # ---- 6. Best model by mean MAE (M8) ----
        # Additive field on the envelope. Cheap: single aggregate
        # query against the pre-aggregated model_performance table.
        # We skip the query when there are no entries to describe.
        best_model: Optional[str] = None
        if entries:
            try:
                best_model = await model_perf_repo.fetch_best_model_by_mae(
                    horizon=horizon or "24h",
                    days=days,
                )
            except Exception as e:
                logger.warning(f"Failed to fetch best model: {e}")
                best_model = None

    # ---- 7. Aggregate warnings ----
    # `warnings_count` is the total number of warned *metrics* across
    # all entries, not the number of entries that contain a warning.
    # A single entry with 3 warned metrics contributes 3 here.
    warnings_count = sum(e.warning_count for e in entries)

    response = PerformanceResponse(
        time_period_days=days,
        generated_at=datetime.now(timezone.utc),
        entries=entries,
        warnings_count=warnings_count,
        best_model=best_model,
    )

    logger.info(
        f"Returning {len(entries)} performance entries "
        f"for {days}-day window ({warnings_count} warnings, "
        f"best_model={best_model})"
    )

    return response