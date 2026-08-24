# """
# API endpoints for similar historical macroeconomic periods.
# """

# from typing import Optional

# from fastapi import APIRouter, Depends, HTTPException, Query
# from pydantic import BaseModel, Field

# from sqlalchemy.orm import Session

# from app.database.session import SessionLocal
# from app.services.similar_period_service import (
#     SimilarPeriodService,
# )
# from fastapi import Request
# from app.core.rate_limit import limiter
# from app.config import settings


# router = APIRouter(
#     prefix="/api/v1/regimes",
#     tags=["Macroeconomic Regimes"],
# )


# # ============================================================
# # DATABASE DEPENDENCY
# # ============================================================

# def get_db():
#     """
#     Provide a database session for API requests.
#     """

#     db = SessionLocal()

#     try:
#         yield db
#     finally:
#         db.close()


# # ============================================================
# # RESPONSE MODELS
# # ============================================================

# class BTCPerformanceResponse(BaseModel):
#     """
#     BTC performance during a similar historical period.
#     """

#     price_start: float
#     price_end: float
#     return_percent: float
#     observations: int


# class MatchingIndicatorResponse(BaseModel):
#     """
#     Indicator contributing to historical similarity.
#     """

#     indicator: str
#     normalized_difference: float


# class SimilarPeriodResponse(BaseModel):
#     """
#     Historical period similar to the current macro environment.
#     """

#     period_start: str
#     period_end: str

#     distance: float
#     similarity_score: float

#     reason: str

#     matching_indicators: list[
#         MatchingIndicatorResponse
#     ]

#     macro_conditions: dict[str, float]

#     btc_performance: Optional[
#         BTCPerformanceResponse
#     ] = None


# class SimilarPeriodsResponse(BaseModel):
#     """
#     Similar historical macroeconomic periods.
#     """

#     current_conditions: dict[str, float]

#     method: str

#     period_count: int

#     similar_periods: list[
#         SimilarPeriodResponse
#     ]

#     message: Optional[str] = None


# # ============================================================
# # SIMILAR HISTORICAL PERIODS
# # ============================================================

# @router.get(
#     "/history/similar-periods",
#     response_model=SimilarPeriodsResponse,
#     summary="Find similar historical macroeconomic periods",
#     description="""
#     Identifies historical periods with macroeconomic conditions
#     similar to the current environment.

#     Similarity is calculated using normalized Euclidean distance
#     across the available macroeconomic indicators.

#     The response returns between 3 and 5 historical periods,
#     including:

#     - Similarity distance
#     - Similarity score
#     - Reasoning for the similarity
#     - Matching macroeconomic indicators
#     - Historical macroeconomic conditions
#     - BTC performance when historical BTC data is available

#     Suggestions are generated on-the-fly and are not persisted.
#     """,
# )
# @limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
# async def get_similar_periods(
#     request: Request,
#     limit: int = Query(
#         default=5,
#         ge=3,
#         le=5,
#         description=(
#             "Number of similar historical periods to return."
#         ),
#     ),
#     db: Session = Depends(get_db),
# ):
#     """
#     Return historical macroeconomic periods similar
#     to the current environment.
#     """

#     service = SimilarPeriodService(db)

#     try:
#         return service.find_similar_periods(
#             limit=limit
#         )

#     except ValueError as exc:
#         raise HTTPException(
#             status_code=422,
#             detail=str(exc),
#         ) from exc

#     except Exception as exc:
#         raise HTTPException(
#             status_code=500,
#             detail=(
#                 "Failed to calculate similar "
#                 "historical periods"
#             ),
#         ) from exc


"""
API endpoints for similar historical macroeconomic periods.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.rate_limit import limiter
from app.database.session import SessionLocal
from app.services.similar_period_service import (
    SimilarPeriodService,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/regimes",
    tags=["Macroeconomic Regimes"],
)


# ============================================================
# CACHE CONFIGURATION
# ============================================================

SIMILAR_PERIODS_CACHE_TTL = (
    settings.MACRO_REGIME_CACHE_TTL
)


def get_similar_periods_cache_key(
    limit: int,
) -> str:
    """
    Return the cache key for a similar-periods response.

    The limit is included because it changes the response.
    """

    return (
        "macro_regimes:similar_periods:"
        f"limit_{limit}"
    )


# ============================================================
# RESPONSE MODELS
# ============================================================

class BTCPerformanceResponse(BaseModel):
    """
    BTC performance during a similar historical period.
    """

    price_start: float
    price_end: float
    return_percent: float
    observations: int


class MatchingIndicatorResponse(BaseModel):
    """
    Indicator contributing to historical similarity.
    """

    indicator: str
    normalized_difference: float


class SimilarPeriodResponse(BaseModel):
    """
    Historical period similar to the current macro environment.
    """

    period_start: str
    period_end: str

    distance: float
    similarity_score: float

    reason: str

    matching_indicators: list[
        MatchingIndicatorResponse
    ]

    macro_conditions: dict[str, float]

    btc_performance: Optional[
        BTCPerformanceResponse
    ] = None


class SimilarPeriodsResponse(BaseModel):
    """
    Similar historical macroeconomic periods.
    """

    current_conditions: dict[str, float]

    method: str

    period_count: int

    similar_periods: list[
        SimilarPeriodResponse
    ]

    message: Optional[str] = None


# ============================================================
# SIMILAR HISTORICAL PERIODS
# ============================================================

@router.get(
    "/history/similar-periods",
    response_model=SimilarPeriodsResponse,
    summary="Find similar historical macroeconomic periods",
    description="""
    Identifies historical periods with macroeconomic conditions
    similar to the current environment.

    Similarity is calculated using normalized Euclidean distance
    across the available macroeconomic indicators.

    The response returns between 3 and 5 historical periods,
    including:

    - Similarity distance
    - Similarity score
    - Reasoning for the similarity
    - Matching macroeconomic indicators
    - Historical macroeconomic conditions
    - BTC performance when historical BTC data is available

    Suggestions are generated on-the-fly and are not persisted.

    Redis caching is used to reduce repeated similarity
    calculations and database queries.
    """,
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_similar_periods(
    request: Request,
    limit: int = Query(
        default=5,
        ge=3,
        le=5,
        description=(
            "Number of similar historical periods to return."
        ),
    ),
):
    """
    Return historical macroeconomic periods similar
    to the current environment.

    Redis cache-aside flow:

        1. Get Redis client.
        2. Check Redis.
        3. Return immediately on cache hit.
        4. Create database session only on cache miss.
        5. Calculate similar periods.
        6. Store complete response in Redis.
        7. Return response.
    """

    # --------------------------------------------------------
    # 1. Get cache client
    # --------------------------------------------------------

    cache_client = getattr(
        request.app.state,
        "cache_client",
        None,
    )

    cache_key = get_similar_periods_cache_key(
        limit=limit
    )

    logger.info(
        f"Redis client: {cache_client}, "
        f"connected={getattr(cache_client, 'is_connected', None)}, "
        f"key={cache_key}"
    )

    # --------------------------------------------------------
    # 2. Redis cache lookup
    # --------------------------------------------------------

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
                #
                # Return immediately.
                #
                # No SessionLocal()
                # No SimilarPeriodService()
                # No database query.
                # No similarity calculation.

                return SimilarPeriodsResponse(
                    **cached
                )

            logger.info(
                f"Redis MISS: {cache_key}"
            )

        except Exception as error:
            logger.warning(
                f"Redis read failed: {error}"
            )

    # --------------------------------------------------------
    # 3. Cache miss -> database/service layer
    # --------------------------------------------------------

    logger.info(
        "Calculating similar historical periods "
        f"(limit={limit})"
    )

    db = SessionLocal()

    try:
        service = SimilarPeriodService(db)

        result = service.find_similar_periods(
            limit=limit
        )

        response = SimilarPeriodsResponse(
            **result
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Failed to calculate similar "
            "historical periods"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate similar "
                "historical periods"
            ),
        ) from exc

    finally:
        db.close()

        logger.info(
            "Database session closed"
        )

    # --------------------------------------------------------
    # 4. Store complete API response in Redis
    # --------------------------------------------------------

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
                ttl=SIMILAR_PERIODS_CACHE_TTL,
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