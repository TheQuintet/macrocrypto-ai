"""Predictions API router.

Exposes:
    - GET /api/v1/predict/btc?horizon=24h

Returns the latest stored prediction batch for the requested
horizon and model, along with:
    - Current BTC price (from btc_prices)
    - Predicted end-of-horizon price
    - Percentage change
    - Trend direction (up / down / neutral)

Design:
    - Reads from the database via PredictionRepository
    - Uses pure helpers from app.prediction.trend for classification
    - Returns a Pydantic PredictionResponse
    - Caches the response in Redis (cache-aside, best-effort)

Caching:
    - Cache key: predict:btc:{horizon}:{model_name}:{confidence}
    - TTL: settings.redis_forecast_ttl (default 300s = 5 min)
    - Invalidation: the generator invalidates after saving new
      predictions; the TTL is a safety net.
    - On Redis failure, we log a warning and fall through to the DB.

Authentication is deliberately out of scope for this branch.
"""

import logging
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_repository
from app.cache.prediction_cache import (
    get_cached_prediction,
    set_cached_prediction,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)
from app.prediction.trend import calculate_trend_and_change
from app.schemas.prediction import (
    PredictionErrorResponse,
    PredictionPoint,
    PredictionResponse,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
VALID_CONFIDENCE_LEVELS = (0.70, 0.85, 0.95)


# ============================================================
# ROUTER
# ============================================================
router = APIRouter(
    prefix="/api/v1/predict",
    tags=["predictions"],
)


# ============================================================
# HELPERS
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


# ============================================================
# ENDPOINT
# ============================================================
@router.get(
    "/btc",
    response_model=PredictionResponse,
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
        "end price, percentage change, and trend direction. Results "
        "are cached in Redis for 5 minutes."
    ),
)
async def get_btc_predictions(
    horizon: Literal["24h", "7d"] = Query(
        default="24h",
        description="Forecast horizon: '24h' or '7d'.",
    ),
    model_name: str = Query(
        default="prophet",
        description="Model that produced the predictions (e.g. 'prophet').",
    ),
    confidence: float = Query(
        default=0.85,
        description="Confidence level for the bounds (0.70, 0.85, or 0.95).",
    ),
    repository: PredictionRepository = Depends(get_repository),
) -> PredictionResponse:
    """Get the latest BTC price predictions.

    Cache-aside flow:
        1. Validate confidence.
        2. Try the cache. On hit, return immediately.
        3. Query the database.
        4. Build the response.
        5. Write to the cache (best-effort).
        6. Return the response.

    Args:
        horizon: Requested forecast horizon.
        model_name: Model identifier.
        confidence: Confidence level for the returned bounds.
        repository: Injected PredictionRepository.

    Returns:
        PredictionResponse with metadata, summary metrics, and
        the full list of forecast points.

    Raises:
        HTTPException: 404 if no predictions exist for the key.
        HTTPException: 422 if confidence is not one of the valid levels.
    """
    logger.info(
        f"GET /api/v1/predict/btc "
        f"(horizon={horizon}, model={model_name}, confidence={confidence})"
    )

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

    # ---- 1. Try cache (best-effort; returns None on miss or error) ----
    cached = await get_cached_prediction(
        horizon=horizon,
        model_name=model_name,
        confidence=confidence,
    )
    if cached is not None:
        logger.debug(
            f"Serving cached response for "
            f"(horizon={horizon}, model={model_name}, "
            f"confidence={confidence})"
        )
        return PredictionResponse.model_validate(cached)

    # ---- 2. Cache miss — query the database ----
    rows = await repository.fetch_latest_predictions(
        horizon=horizon,
        model_name=model_name,
        confidence=confidence,
    )

    if not rows:
        logger.info(
            f"No predictions found for "
            f"(horizon={horizon}, model={model_name}, "
            f"confidence={confidence})"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "no_predictions",
                "message": (
                    f"No predictions available for "
                    f"horizon='{horizon}', model='{model_name}', "
                    f"confidence={confidence}."
                ),
            },
        )

    # ---- 3. Fetch current price (may be None) ----
    current_price = await repository.fetch_latest_close_price()

    # ---- 4. Compute summary metrics ----
    first_row = rows[0]
    last_row = rows[-1]
    predicted_end_price = last_row.predicted_price

    trend, price_change_pct = calculate_trend_and_change(
        current_price=current_price,
        predicted_end_price=predicted_end_price,
        horizon=horizon,
    )

    # ---- 5. Build response ----
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

    # ---- 6. Write to cache (best-effort; failures are logged) ----
    await set_cached_prediction(
        horizon=horizon,
        model_name=model_name,
        confidence=confidence,
        payload=response.model_dump(mode="json"),
    )

    logger.info(
        f"Returning {len(rows)} prediction points "
        f"(trend={trend.value}, price_change_pct={price_change_pct})"
    )

    return response