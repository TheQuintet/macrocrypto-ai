"""Predictions API router.

Exposes:
    - GET /api/v1/predict/btc?horizon=24h
    - GET /api/v1/predict/btc?horizon=24h&models=prophet,xgboost_fresh

Single-model mode (default):
    Returns the latest stored prediction batch for the requested
    horizon and model, along with:
        - Current BTC price (from btc_prices)
        - Predicted end-of-horizon price
        - Percentage change
        - Trend direction (up / down / neutral)

Multi-model mode (when ?models= names 2 or more models):
    Returns one stored batch per requested model plus a comparison
    envelope containing:
        - Consensus (mean prediction across models per timestamp)
        - Agreement score in [0, 1]
        - Best model by recent MAE
        - Per-model batches
        - Models requested but missing from storage

Design:
    - Reads from the database via PredictionRepository
    - For multi-model mode, constructs a PerformanceRepository from
      the same session to look up the best model by MAE — no extra
      dependency needed
    - Uses pure helpers from app.prediction.trend and
      app.prediction.compare for classification and comparison math
    - Caches the response in Redis (cache-aside, best-effort)

Caching:
    - Single-model cache key:
        predict:btc:{horizon}:{model_name}:{confidence}
    - Multi-model cache key:
        predict:btc:{horizon}:multi:{comma_joined_models}:{confidence}
      where `comma_joined_models` is the sorted, deduplicated model
      list, so different orderings share one cache entry.
    - TTL: settings.redis_forecast_ttl (default 300s = 5 min)
    - Invalidation: the generator invalidates after saving new
      predictions; the TTL is a safety net.
    - On Redis failure, we log a warning and fall through to the DB.

Authentication is deliberately out of scope for this branch.
"""

import logging
from datetime import datetime, timezone
from typing import List, Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_repository
from app.cache.prediction_cache import (
    get_cached_prediction,
    set_cached_prediction,
)
from app.database.repositories.performance_repository import (
    PerformanceRepository,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)
from app.prediction.compare import compare_stored_predictions
from app.prediction.trend import calculate_trend_and_change
from app.schemas.prediction import (
    ComparisonResponse,
    ModelBatch,
    PredictionErrorResponse,
    PredictionPoint,
    PredictionResponse,
    StoredComparisonPayload,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
VALID_CONFIDENCE_LEVELS = (0.70, 0.85, 0.95)

# The default model name matches what the scheduler currently
# writes to btc_predictions. Additional model variants will be
# written by Branch 30 (M6b).
DEFAULT_MODEL = "prophet"

# Separator for the ?models= query parameter. Comma matches the
# convention used by the CLI tools and the OpenAPI examples.
VALID_MODEL_SEPARATOR = ","

# Upper bound on how many models a single request may name. Keeps
# the SQL IN clause and the response payload bounded.
MAX_MODELS = 20

# How far back to look when picking "best model by MAE". Matches
# the default window used by the performance API.
BEST_MODEL_LOOKBACK_DAYS = 30


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/predict",
    tags=["predictions"],
)


# ============================================================
# HELPERS — model list parsing
# ============================================================
def _parse_models(models_param: Optional[str]) -> List[str]:
    """Parse and validate the ?models= query parameter.

    Rules:
        - None → [DEFAULT_MODEL]
        - Empty string or whitespace-only → ValueError
        - Comma-separated names are stripped of whitespace
        - Any empty segment (leading, trailing, or doubled comma)
          → ValueError
        - Duplicates → ValueError
        - More than MAX_MODELS names → ValueError

    Args:
        models_param: Raw string from the query parameter, or None.

    Returns:
        Ordered list of model names with no duplicates.

    Raises:
        ValueError: If the raw string is malformed (empty segment,
            duplicate name, or too many names). The endpoint converts
            this to a 422 response.
    """
    if models_param is None:
        return [DEFAULT_MODEL]

    raw_parts = models_param.split(VALID_MODEL_SEPARATOR)
    names = [p.strip() for p in raw_parts]

    if any(name == "" for name in names):
        raise ValueError(
            "Empty model name in ?models= — the parameter must be a "
            "non-empty, comma-separated list of model names with no "
            "leading, trailing, or doubled commas"
        )

    if len(names) > MAX_MODELS:
        raise ValueError(
            f"Too many models requested (max {MAX_MODELS})"
        )

    seen = set()
    for name in names:
        if name in seen:
            raise ValueError(f"Duplicate model name: {name!r}")
        seen.add(name)

    return names


def _validate_models_param_or_422(models_param: Optional[str]) -> List[str]:
    """Parse ?models= or raise a 422 HTTPException.

    Thin wrapper so the endpoint reads cleanly. Kept separate from
    _parse_models so the pure parser stays unit-testable without
    FastAPI exceptions.

    Args:
        models_param: Raw string from the query parameter, or None.

    Returns:
        Parsed list of model names.

    Raises:
        HTTPException: 422 when the parameter is malformed.
    """
    try:
        return _parse_models(models_param)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_models",
                "message": str(e),
            },
        )


# ============================================================
# HELPERS — response building
# ============================================================
def _rows_to_points(rows: List[PredictionRow]) -> List[PredictionPoint]:
    """Convert repository rows to API prediction points.

    Args:
        rows: Ordered list of PredictionRow (ascending by time).

    Returns:
        List of PredictionPoint instances.
    """
    return [
        PredictionPoint(
            time=row.time,
            predicted_price=row.predicted_price,
            lower_bound=row.lower_bound,
            upper_bound=row.upper_bound,
        )
        for row in rows
    ]


def _build_model_batch(rows: List[PredictionRow]) -> ModelBatch:
    """Wrap a batch of PredictionRow in a ModelBatch schema.

    Assumes `rows` is non-empty and internally consistent (all rows
    share the same horizon/model_name/confidence/prediction_time).
    The repository guarantees this.

    Args:
        rows: Non-empty list of PredictionRow for one model.

    Returns:
        ModelBatch instance.
    """
    first = rows[0]
    return ModelBatch(
        model_name=first.model_name,
        model_version=None,
        prediction_time=first.prediction_time,
        horizon=first.horizon,
        confidence=first.confidence,
        predictions=_rows_to_points(rows),
    )


async def _build_comparison_response(
    repository: PredictionRepository,
    horizon: str,
    model_names: List[str],
    confidence: float,
) -> ComparisonResponse:
    """Compose a ComparisonResponse from stored predictions.

    Does three reads:
        1. Batch fetch of the latest stored predictions per model
           (one repo call regardless of model count)
        2. Best model by MAE over the last BEST_MODEL_LOOKBACK_DAYS
        3. Current close price

    Then runs compare_stored_predictions() over the batches.

    Args:
        repository: PredictionRepository bound to the request session.
        horizon: Horizon label ('24h' or '7d').
        model_names: Non-empty, deduplicated list of model names.
        confidence: Confidence level for the bounds.

    Returns:
        ComparisonResponse with all fields populated.

    Raises:
        HTTPException: 404 if none of the requested models has any
            stored predictions.
    """
    # ---- 1. Fetch batches ----
    batches = await repository.fetch_latest_predictions_batch(
        model_names=model_names,
        horizon=horizon,
        confidence=confidence,
    )

    if not batches:
        logger.info(
            f"No stored predictions found for any of "
            f"models={model_names} (horizon={horizon}, "
            f"confidence={confidence})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_predictions",
                "message": (
                    f"No stored predictions available for any of "
                    f"models={model_names} on horizon='{horizon}' "
                    f"at confidence={confidence}."
                ),
            },
        )

    # ---- 2. Best model by MAE (same session, separate repo) ----
    # We construct a PerformanceRepository on the same session so
    # both reads share one transaction snapshot. This is a local
    # convenience — no new dependency is registered.
    try:
        perf_repo = PerformanceRepository(repository.session)
        best_model = await perf_repo.fetch_best_model_by_mae(
            horizon=horizon,
            days=BEST_MODEL_LOOKBACK_DAYS,
        )
    except Exception as e:
        # Best model is advisory, not load-bearing — log and move on.
        logger.warning(f"Failed to fetch best model by MAE: {e}")
        best_model = None

    # ---- 3. Run the comparison (pure) ----
    # `requested_models` is passed through so the comparison can
    # correctly report models the caller asked for but which have
    # no stored predictions. `batches` only contains models that
    # had data, so it alone can't answer "what was requested".
    comparison = compare_stored_predictions(
        batches=batches,
        best_model=best_model,
        requested_models=model_names,
    )

    # ---- 4. Current price (best-effort) ----
    current_price = await repository.fetch_latest_close_price()

    # ---- 5. Assemble ----
    return ComparisonResponse(
        horizon=horizon,
        confidence=confidence,
        current_price=current_price,
        models={
            name: _build_model_batch(rows)
            for name, rows in batches.items()
        },
        comparison=StoredComparisonPayload(
            models_compared=comparison.models_compared,
            models_missing=comparison.models_missing,
            agreement_score=comparison.agreement_score,
            best_model=comparison.best_model,
            timestamps_compared=comparison.timestamps_compared,
        ),
        missing_models=comparison.models_missing,
        generated_at=datetime.now(timezone.utc),
    )


# ============================================================
# ENDPOINT
# ============================================================
@router.get(
    "/btc",
    response_model=Union[PredictionResponse, ComparisonResponse],
    responses={
        404: {
            "model": PredictionErrorResponse,
            "description": "No predictions available for the requested key.",
        },
        422: {
            "model": PredictionErrorResponse,
            "description": "Invalid query parameters.",
        },
    },
    summary="Get BTC price predictions",
    description=(
        "Return the latest stored prediction batch for the requested "
        "horizon and model, along with the current price, predicted "
        "end price, percentage change, and trend direction. "
        "Results are cached in Redis for 5 minutes.\n\n"
        "When the `models` query parameter names **two or more** "
        "models, the endpoint returns a comparison envelope instead: "
        "one stored batch per model plus a consensus, agreement "
        "score, and best-model identifier. The single-model response "
        "shape is unchanged."
    ),
)
async def get_btc_predictions(
    horizon: Literal["24h", "7d"] = Query(
        default="24h",
        description="Forecast horizon: '24h' or '7d'.",
    ),
    model_name: str = Query(
        default="prophet",
        description=(
            "Model that produced the predictions (e.g. 'prophet'). "
            "Ignored when `models` is provided."
        ),
    ),
    models: Optional[str] = Query(
        default=None,
        description=(
            "Comma-separated list of models to compare. When two or "
            "more models are named, the endpoint returns a "
            "comparison envelope instead of a single prediction "
            "batch. Example: `?models=prophet,xgboost_fresh`."
        ),
    ),
    confidence: float = Query(
        default=0.85,
        description="Confidence level for the bounds (0.70, 0.85, or 0.95).",
    ),
    repository: PredictionRepository = Depends(get_repository),
) -> Union[PredictionResponse, ComparisonResponse]:
    """Get the latest BTC price predictions.

    Two modes:
        - Single-model: same behavior as before M6. Returns a
          PredictionResponse with one model's stored batch.
        - Multi-model: when `?models=` names 2+ models, returns a
          ComparisonResponse with per-model batches plus a
          consensus, agreement score, and best model.

    Cache-aside flow (both modes):
        1. Validate confidence and (if present) the models list.
        2. Try the cache. On hit, return immediately.
        3. Query the database.
        4. Build the response.
        5. Write to the cache (best-effort).
        6. Return the response.

    Args:
        horizon: Requested forecast horizon.
        model_name: Model identifier (used only in single-model mode).
        models: Optional comma-separated list of models. When it
            names two or more models, the endpoint returns a
            comparison envelope.
        confidence: Confidence level for the returned bounds.
        repository: Injected PredictionRepository.

    Returns:
        PredictionResponse in single-model mode, or
        ComparisonResponse in multi-model mode.

    Raises:
        HTTPException: 404 if no predictions exist for the key.
        HTTPException: 422 if confidence is invalid or the models
            list is malformed.
    """
    # ---- 0. Validate confidence (manual — Literal[float] is unreliable) ----
    if confidence not in VALID_CONFIDENCE_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": "invalid_confidence",
                "message": (
                    f"Invalid confidence '{confidence}'. "
                    f"Must be one of {list(VALID_CONFIDENCE_LEVELS)}."
                ),
            },
        )

    # ---- 0b. Parse the ?models= parameter ----
    # None → single-model default. Malformed (empty string, empty
    # segments, duplicates, too many) → 422 via
    # _validate_models_param_or_422.
    parsed_models = _validate_models_param_or_422(models)
    is_multi_model = len(parsed_models) >= 2

    logger.info(
        f"GET /api/v1/predict/btc "
        f"(horizon={horizon}, model={model_name}, "
        f"models={parsed_models}, multi={is_multi_model}, "
        f"confidence={confidence})"
    )

    # ---- 1. Multi-model branch ----
    if is_multi_model:
        # Cache key uses the sorted, deduplicated model list so
        # different orderings of the same set share one entry.
        cache_models_key = ",".join(sorted(parsed_models))

        cached = await get_cached_prediction(
            horizon=horizon,
            model_name=f"multi:{cache_models_key}",
            confidence=confidence,
        )
        if cached is not None:
            logger.debug(
                f"Serving cached multi-model response for "
                f"(horizon={horizon}, models={parsed_models}, "
                f"confidence={confidence})"
            )
            return ComparisonResponse.model_validate(cached)

        response = await _build_comparison_response(
            repository=repository,
            horizon=horizon,
            model_names=parsed_models,
            confidence=confidence,
        )

        await set_cached_prediction(
            horizon=horizon,
            model_name=f"multi:{cache_models_key}",
            confidence=confidence,
            payload=response.model_dump(mode="json"),
        )

        logger.info(
            f"Returning multi-model comparison: "
            f"{len(response.models)} batches, "
            f"agreement={response.comparison.agreement_score:.3f}, "
            f"best='{response.comparison.best_model}', "
            f"missing={response.missing_models}"
        )
        return response

    # ---- 2. Single-model branch (existing behavior) ----
    # When `models` was provided with exactly one name, use that
    # name; otherwise fall back to the `model_name` parameter.
    # This keeps `?models=prophet` and `?model_name=prophet`
    # equivalent, and preserves the default when neither is given.
    effective_model = (
        parsed_models[0] if parsed_models != [DEFAULT_MODEL] else model_name
    )

    cached = await get_cached_prediction(
        horizon=horizon,
        model_name=effective_model,
        confidence=confidence,
    )
    if cached is not None:
        logger.debug(
            f"Serving cached response for "
            f"(horizon={horizon}, model={effective_model}, "
            f"confidence={confidence})"
        )
        return PredictionResponse.model_validate(cached)

    rows = await repository.fetch_latest_predictions(
        horizon=horizon,
        model_name=effective_model,
        confidence=confidence,
    )

    if not rows:
        logger.info(
            f"No predictions found for "
            f"(horizon={horizon}, model={effective_model}, "
            f"confidence={confidence})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_predictions",
                "message": (
                    f"No predictions available for "
                    f"horizon='{horizon}', model='{effective_model}', "
                    f"confidence={confidence}."
                ),
            },
        )

    current_price = await repository.fetch_latest_close_price()

    first_row = rows[0]
    last_row = rows[-1]
    predicted_end_price = last_row.predicted_price

    trend, price_change_pct = calculate_trend_and_change(
        current_price=current_price,
        predicted_end_price=predicted_end_price,
        horizon=horizon,
    )

    response = PredictionResponse(
        horizon=first_row.horizon,
        model_name=first_row.model_name,
        confidence=first_row.confidence,
        prediction_time=first_row.prediction_time,
        current_price=current_price,
        predicted_end_price=predicted_end_price,
        price_change_pct=price_change_pct,
        trend=trend,
        predictions=_rows_to_points(rows),
    )

    await set_cached_prediction(
        horizon=horizon,
        model_name=effective_model,
        confidence=confidence,
        payload=response.model_dump(mode="json"),
    )

    logger.info(
        f"Returning {len(rows)} prediction points "
        f"(trend={trend.value}, price_change_pct={price_change_pct})"
    )

    return response