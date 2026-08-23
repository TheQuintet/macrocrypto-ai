"""BTC price endpoints for data-service"""

import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from typing import Optional

from app.api.dependencies import jwt_auth
from app.api.schemas.price_response import (
    BtcPriceHistoryResponse,
    PriceResponse,
)
from app.core.rate_limit import limiter
from app.config import settings
from app.services.price_history_service import (
    PriceHistoryService,
    PriceHistoryValidationError,
)

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/btc",
    tags=["Bitcoin"]
)


@router.get(
    "/price",
    response_model=PriceResponse,
    summary="Get current BTC market data"
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_btc_price(
    request: Request,
    response: Response,
    data_processor: Optional = Depends(lambda: None),  # Will be set in main.py
    cache_client: Optional = Depends(lambda: None),    # Will be set in main.py
    _: str | None = Depends(jwt_auth)
):
    """
    BTC price endpoint.

    Provides the latest Bitcoin market snapshot, including current price,
    24-hour statistics, and 7-day price changes.

    Features:
    - Retrieves the latest BTC market data from the data processor.
    - Uses Redis caching to reduce load and improve response time.
    - Cached responses are stored for 5 seconds.
    - If no valid cache entry exists, data is retrieved from the data processor
      and stored in Redis for subsequent requests.
    - Requests are rate-limited to configured requests per minute.
    - JWT authentication support is prepared for future secured endpoints.
    """
    # Get services from request app state
    data_processor = request.app.state.data_processor
    cache_client = request.app.state.cache_client

    cache_key = "btc_price_snapshot"

    # --------------------------------------------
    # 1. Try Redis cache first
    # --------------------------------------------
    if cache_client and cache_client.is_connected:
        try:
            cached_snapshot = await cache_client.get(cache_key)
            if cached_snapshot:
                logger.info("✅ Returning BTC price from Redis cache")
                return PriceResponse(**cached_snapshot)
        except Exception as error:
            logger.warning(f"⚠️ Cache read failed: {error}")

    # --------------------------------------------
    # 2. Cache miss - fetch from data processor
    # --------------------------------------------
    logger.info("📡 Reading BTC price from DataProcessor")

    if not data_processor:
        logger.error("❌ DataProcessor not available")
        return PriceResponse(
            current_price=None,
            updated_at=None,
            change_24h=None,
            change_24h_percent=None,
            high_24h=None,
            low_24h=None,
            volume_24h=None,
            change_7d=None,
            change_7d_percent=None,
        )

    snapshot = data_processor.get_snapshot()

    response = PriceResponse(
        current_price=snapshot.current_price,
        change_24h=snapshot.change_24h,
        change_24h_percent=snapshot.change_24h_percent,
        high_24h=snapshot.high_24h,
        low_24h=snapshot.low_24h,
        volume_24h=snapshot.volume_24h,
        change_7d=snapshot.change_7d,
        change_7d_percent=snapshot.change_7d_percent,
        updated_at=snapshot.updated_at,
    )

    # --------------------------------------------
    # 3. Cache the response
    # --------------------------------------------
    if cache_client and cache_client.is_connected:
        try:
            # Convert to dict for caching
            cache_data = response.model_dump()
            await cache_client.set(cache_key, cache_data, ttl=5)
            logger.info("💾 BTC price cached in Redis")
        except Exception as error:
            logger.warning(f"⚠️ Cache write failed: {error}")

    return response


@router.get(
    "/price/history",
    response_model=BtcPriceHistoryResponse,
    summary="Get historical BTC OHLC candles",
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_btc_history(
    request: Request,
    response: Response,
    range: str = "7d",
    interval: str = "1h",
    _: str | None = Depends(jwt_auth),
):
    """
    Historical BTC OHLC candles for the dashboard chart.

    Interval bucketing and the point cap are applied server-side.
    Redis caching follows the same cache-aside pattern as `/price`.

    Query parameters:
    - range: 24h, 7d, 30d, or 90d (default 7d)
    - interval: 1m, 5m, 1h, 1d, 1w, or 1y (default 1h)
    """

    cache_client = request.app.state.cache_client
    cache_key = f"btc_price_history:{range}:{interval}"

    if cache_client and cache_client.is_connected:
        try:
            cached = await cache_client.get(cache_key)
            if cached is not None:
                logger.info("✅ Returning BTC history from Redis cache")
                return BtcPriceHistoryResponse(**cached)
        except Exception as error:
            logger.warning(f"⚠️ History cache read failed: {error}")

    service = PriceHistoryService()

    try:
        response = await service.get_history(
            range_value=range,
            interval=interval,
        )
    except PriceHistoryValidationError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception:
        logger.exception(
            "Failed to retrieve BTC price history "
            "range=%s interval=%s",
            range,
            interval,
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve historical BTC price data",
        )
    finally:
        await service.close()

    if cache_client and cache_client.is_connected:
        try:
            await cache_client.set(
                cache_key,
                response.model_dump(),
                ttl=settings.PRICE_HISTORY_CACHE_TTL,
            )
            logger.info("💾 BTC history cached in Redis")
        except Exception as error:
            logger.warning(f"⚠️ History cache write failed: {error}")

    return response

@router.get(
    "/status",
    summary="Get BTC service status"
)
async def get_btc_status(request: Request):
    """
    Get the status of the BTC data service.

    Returns:
        Status information including current price and service health.
    """
    data_processor = request.app.state.data_processor
    cache_client = request.app.state.cache_client

    status = {
        "service": "btc",
        "status": "healthy",
        "current_price": None,
        "price_7d_reference": None,
        "cache_enabled": False,
        "cache_connected": False,
        "data_processor_initialized": False,
        "websocket_connected": False,
    }

    if data_processor:
        status["current_price"] = data_processor.get_price()
        status["price_7d_reference"] = data_processor.price_service.price_7d_reference if data_processor.price_service else None
        status["data_processor_initialized"] = data_processor.is_initialized()

    if cache_client:
        status["cache_enabled"] = cache_client.is_enabled
        status["cache_connected"] = cache_client.is_connected

    # Check WebSocket status (if available in app state)
    if hasattr(request.app.state, 'btc_task'):
        btc_task = request.app.state.btc_task
        if btc_task:
            status["websocket_connected"] = not btc_task.done()

    return status