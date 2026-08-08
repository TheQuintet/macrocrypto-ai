"""
Macroeconomic indicator endpoints for data-service.
"""

import logging
from app.core.rate_limit import limiter
from app.config import settings

from fastapi import (
    APIRouter,
    Request,
    Depends,
    Query,
    HTTPException,
)

from app.api.dependencies import jwt_auth
from app.api.schemas.indicator_response import IndicatorsResponse
from app.services.indicator_service import IndicatorService
from app.database.session import SessionLocal


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Indicators"],
)


INDICATORS_CACHE_TTL = 3600

VALID_PERIODS = {
    "30d",
    "90d",
    "1y",
    "5y",
}


def get_indicators_cache_key(
    period: str | None,
) -> str:
    """
    Return the single cache key used for an indicators response.

    The API endpoint owns the response cache, so both cache
    reads and writes use exactly the same key.
    """

    if period:
        return f"macro_indicators:{period}"

    return "macro_indicators:latest"


@router.get(
    "/indicators",
    response_model=IndicatorsResponse,
    summary="Get latest macroeconomic indicators",
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_indicators(
    request: Request,
    period: str | None = Query(default=None),
    _: str | None = Depends(jwt_auth),
):
    """
    Return latest macroeconomic indicators.

    Cache-aside flow:

    1. Validate the requested period.
    2. Check Redis.
    3. If Redis contains the response, return immediately.
    4. Only on a cache miss, create a database session.
    5. Read indicators from TimescaleDB.
    6. Store the response in Redis.
    7. Return the response.

    This guarantees that a Redis cache hit does not access
    TimescaleDB.
    """

    # --------------------------------------------------
    # 1. Validate period
    # --------------------------------------------------

    if period is not None and period not in VALID_PERIODS:
        raise HTTPException(
            status_code=422,
            detail=(
                "Invalid period. Must be one of: "
                f"{', '.join(sorted(VALID_PERIODS))}"
            ),
        )

    response_period = (
        period
        if period
        else "30d"
    )

    # --------------------------------------------------
    # 2. Get cache client
    # --------------------------------------------------

    cache_client = getattr(
        request.app.state,
        "cache_client",
        None,
    )

    cache_key = get_indicators_cache_key(period)

    # --------------------------------------------------
    # 3. Redis cache lookup
    # --------------------------------------------------

    if (
        cache_client is not None
        and cache_client.is_connected
    ):
        try:
            cached = await cache_client.get(
                cache_key
            )

            if cached is not None:
                logger.info(
                    f"Redis HIT: {cache_key}"
                )

                # IMPORTANT:
                # Return immediately.
                #
                # No SessionLocal()
                # No IndicatorService()
                # No TimescaleDB query.

                return IndicatorsResponse(
                    **cached
                )

            logger.info(
                f"Redis MISS: {cache_key}"
            )

        except Exception as error:
            logger.warning(
                f"Redis read failed: {error}"
            )

    # --------------------------------------------------
    # 4. Cache miss -> TimescaleDB
    # --------------------------------------------------

    logger.info(
        "Reading indicators from TimescaleDB "
        f"(period={period})"
    )

    db = SessionLocal()

    try:
        service = IndicatorService(db)

        indicators = await service.get_indicators(
            period=period
        )

        response = IndicatorsResponse(
            period=response_period,
            count=len(indicators),
            indicators=indicators,
        )

    finally:
        db.close()

        logger.info(
            "Database session closed"
        )

    # --------------------------------------------------
    # 5. Store complete API response in Redis
    # --------------------------------------------------

    if (
        cache_client is not None
        and cache_client.is_connected
    ):
        try:
            success = await cache_client.set(
                cache_key,
                response.model_dump(
                    mode="json"
                ),
                ttl=INDICATORS_CACHE_TTL,
            )

            if success:
                logger.info(
                    f"Redis WRITE: {cache_key}"
                )
            else:
                logger.warning(
                    f"Redis WRITE FAILED: {cache_key}"
                )

        except Exception as error:
            logger.warning(
                f"Redis write failed: {error}"
            )

    return response
