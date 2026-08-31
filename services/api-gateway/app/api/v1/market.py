"""Market data API endpoints for BTC prices, indicators, correlation, and regimes.

This module provides REST API endpoints for fetching:
- Historical BTC price data
- Macroeconomic indicators
- BTC-macro correlation analysis
- Market regime data
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user, get_optional_user
from app.services.market_service import market_service
from app.models.user import User

# ============================================
# LOGGING
# ============================================

logger = logging.getLogger(settings.SERVICE_NAME)

# ============================================
# ROUTER
# ============================================

router = APIRouter(tags=["Market Data"])
security = HTTPBearer()


# ============================================
# PYDANTIC MODELS
# ============================================

class PricePoint(BaseModel):
    """Single price data point."""

    timestamp: str = Field(..., description="Timestamp of the price")
    price: float = Field(..., description="Price in USD")
    volume: Optional[float] = Field(None, description="Trading volume")
    market_cap: Optional[float] = Field(None, description="Market capitalization")


class PricesResponse(BaseModel):
    """Price data response model."""

    symbol: str = Field(..., description="Trading symbol")
    prices: List[PricePoint] = Field(..., description="List of price points")
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Records per page")
    offset: int = Field(..., description="Pagination offset")
    timestamp: str = Field(..., description="Response timestamp")
    cached: bool = Field(False, description="Whether response was cached")


class IndicatorValue(BaseModel):
    """Single indicator value."""

    value: float = Field(..., description="Current value")
    previous: Optional[float] = Field(None, description="Previous value")
    change_percent: Optional[float] = Field(None, description="Percentage change")
    source: str = Field(..., description="Data source")
    unit: str = Field(..., description="Unit of measurement")


class IndicatorsResponse(BaseModel):
    """Indicators response model."""

    indicators: Dict[str, IndicatorValue] = Field(..., description="Indicator values")
    timestamp: str = Field(..., description="Response timestamp")
    cached: bool = Field(False, description="Whether response was cached")


class CorrelationItem(BaseModel):
    """Single correlation item."""

    value: float = Field(..., description="Correlation coefficient (-1 to 1)")
    strength: str = Field(..., description="Strength: strong/moderate/weak")


class CorrelationResponse(BaseModel):
    """Correlation response model."""

    symbol: str = Field(..., description="Trading symbol")
    window: str = Field(..., description="Time window")
    days: int = Field(..., description="Number of days analyzed")
    correlations: Dict[str, CorrelationItem] = Field(..., description="Correlation values")
    timestamp: str = Field(..., description="Response timestamp")
    cached: bool = Field(False, description="Whether response was cached")


class RegimeData(BaseModel):
    """Single regime data."""

    regime_type: str = Field(..., description="Regime type: bull/bear/sideways")
    start_date: str = Field(..., description="Start date")
    end_date: Optional[str] = Field(None, description="End date")
    duration_days: Optional[int] = Field(None, description="Duration in days")
    avg_return: Optional[float] = Field(None, description="Average return")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    volatility: Optional[float] = Field(None, description="Volatility")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")


class RegimesResponse(BaseModel):
    """Regimes response model."""

    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Timeframe")
    regimes: List[RegimeData] = Field(..., description="List of regimes")
    current_regime: RegimeData = Field(..., description="Current regime")
    timestamp: str = Field(..., description="Response timestamp")
    cached: bool = Field(False, description="Whether response was cached")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str = Field(..., description="Error message")


# ============================================
# ENDPOINTS
# ============================================

@router.get(
    "/btc/prices",
    response_model=PricesResponse,
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    },
)
async def get_btc_prices(
    request: Request,
    start_date: Optional[str] = Query(
        None,
        description="Start date (ISO 8601, e.g., '2024-01-01')"
    ),
    end_date: Optional[str] = Query(
        None,
        description="End date (ISO 8601, e.g., '2024-12-31')"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Number of records per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get historical BTC price data.

    Returns historical BTC prices with optional date range filtering and pagination.

    Args:
        request: The HTTP request object.
        start_date: Start date for filtering.
        end_date: End date for filtering.
        limit: Number of records per page.
        offset: Pagination offset.
        current_user: The authenticated user (optional).

    Returns:
        PricesResponse: The price data.

    Raises:
        HTTPException: If the Data Service is unavailable or returns an error.
    """
    # Generate cache key
    cache_key = f"prices_btc_{start_date}_{end_date}_{limit}_{offset}"
    from app.core.redis import redis_client

    # Try to get from cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        import json
        logger.info(f"Cache hit for {cache_key}")
        response_data = json.loads(cached_data)
        response_data["cached"] = True
        return response_data

    try:
        # Fetch prices from Data Service
        prices = await market_service.get_prices(
            symbol="BTC",
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )

        # Cache the response (1 hour TTL)
        import json
        await redis_client.set(
            cache_key,
            json.dumps(prices),
            expire=3600  # 1 hour
        )
        logger.info(f"Cached prices for {cache_key}")

        return prices

    except httpx.HTTPStatusError as e:
        logger.error(f"Data Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data Service unavailable: {e.response.status_code}"
        )
    except httpx.TimeoutException:
        logger.error("Data Service timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Data Service request timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch prices: {str(e)}"
        )


@router.get(
    "/indicators",
    response_model=IndicatorsResponse,
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    },
)
async def get_indicators(
    request: Request,
    indicators: Optional[str] = Query(
        None,
        description="Comma-separated list of indicator names (e.g., 'GDP,Inflation')"
    ),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get macroeconomic indicators.

    Returns current values for macroeconomic indicators with trends.

    Args:
        request: The HTTP request object.
        indicators: Comma-separated list of indicator names.
        current_user: The authenticated user (optional).

    Returns:
        IndicatorsResponse: The indicator data.

    Raises:
        HTTPException: If the Data Service is unavailable or returns an error.
    """
    # Parse indicators list
    indicator_list = None
    if indicators:
        indicator_list = [i.strip() for i in indicators.split(",") if i.strip()]

    # Generate cache key
    cache_key = f"indicators_{indicators or 'all'}"
    from app.core.redis import redis_client

    # Try to get from cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        import json
        logger.info(f"Cache hit for {cache_key}")
        response_data = json.loads(cached_data)
        response_data["cached"] = True
        return response_data

    try:
        # Fetch indicators from Data Service
        indicators_data = await market_service.get_indicators(
            indicators=indicator_list,
        )

        # Cache the response (1 hour TTL)
        import json
        await redis_client.set(
            cache_key,
            json.dumps(indicators_data),
            expire=3600  # 1 hour
        )
        logger.info(f"Cached indicators for {cache_key}")

        return indicators_data

    except httpx.HTTPStatusError as e:
        logger.error(f"Data Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data Service unavailable: {e.response.status_code}"
        )
    except httpx.TimeoutException:
        logger.error("Data Service timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Data Service request timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch indicators: {str(e)}"
        )


@router.get(
    "/correlation/btc",
    response_model=CorrelationResponse,
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    },
)
async def get_correlation(
    request: Request,
    window: str = Query(
        "30d",
        description="Time window: '30d', '90d', '1y'",
        pattern="^(30d|90d|1y)$"
    ),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get BTC-macro correlation analysis.

    Returns correlation matrix between BTC and macroeconomic indicators.

    Args:
        request: The HTTP request object.
        window: Time window for correlation analysis.
        current_user: The authenticated user (optional).

    Returns:
        CorrelationResponse: The correlation data.

    Raises:
        HTTPException: If the Data Service is unavailable or returns an error.
    """
    # Validate window
    if window not in ["30d", "90d", "1y"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Window must be one of: '30d', '90d', '1y'"
        )

    # Generate cache key
    cache_key = f"correlation_btc_{window}"
    from app.core.redis import redis_client

    # Try to get from cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        import json
        logger.info(f"Cache hit for {cache_key}")
        response_data = json.loads(cached_data)
        response_data["cached"] = True
        return response_data

    try:
        # Fetch correlation from Data Service
        correlation_data = await market_service.get_correlation(
            symbol="BTC",
            window=window,
        )

        # Cache the response (1 hour TTL)
        import json
        await redis_client.set(
            cache_key,
            json.dumps(correlation_data),
            expire=3600  # 1 hour
        )
        logger.info(f"Cached correlation for {cache_key}")

        return correlation_data

    except httpx.HTTPStatusError as e:
        logger.error(f"Data Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data Service unavailable: {e.response.status_code}"
        )
    except httpx.TimeoutException:
        logger.error("Data Service timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Data Service request timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch correlation: {str(e)}"
        )


@router.get(
    "/regimes/btc",
    response_model=RegimesResponse,
    responses={
        200: {"description": "Successful response"},
        401: {"description": "Unauthorized", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
        503: {"description": "Service unavailable", "model": ErrorResponse},
    },
)
async def get_regimes(
    request: Request,
    timeframe: str = Query(
        "1w",
        description="Timeframe: '1w', '1m', '3m'",
        pattern="^(1w|1m|3m)$"
    ),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get market regime data for BTC.

    Returns historical market regimes with performance metrics.

    Args:
        request: The HTTP request object.
        timeframe: Timeframe for regime analysis.
        current_user: The authenticated user (optional).

    Returns:
        RegimesResponse: The regime data.

    Raises:
        HTTPException: If the Data Service is unavailable or returns an error.
    """
    # Validate timeframe
    if timeframe not in ["1w", "1m", "3m"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Timeframe must be one of: '1w', '1m', '3m'"
        )

    # Generate cache key
    cache_key = f"regimes_btc_{timeframe}"
    from app.core.redis import redis_client

    # Try to get from cache
    cached_data = await redis_client.get(cache_key)
    if cached_data:
        import json
        logger.info(f"Cache hit for {cache_key}")
        response_data = json.loads(cached_data)
        response_data["cached"] = True
        return response_data

    try:
        # Fetch regimes from Data Service
        regimes_data = await market_service.get_regimes(
            symbol="BTC",
            timeframe=timeframe,
        )

        # Cache the response (1 hour TTL)
        import json
        await redis_client.set(
            cache_key,
            json.dumps(regimes_data),
            expire=3600  # 1 hour
        )
        logger.info(f"Cached regimes for {cache_key}")

        return regimes_data

    except httpx.HTTPStatusError as e:
        logger.error(f"Data Service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Data Service unavailable: {e.response.status_code}"
        )
    except httpx.TimeoutException:
        logger.error("Data Service timeout")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Data Service request timed out"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch regimes: {str(e)}"
        )