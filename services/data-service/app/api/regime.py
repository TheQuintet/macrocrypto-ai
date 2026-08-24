# """
# Macroeconomic Regime API.

# Provides API endpoints for retrieving:
# - Current macroeconomic regime
# - Historical macroeconomic regimes
# - BTC performance during completed and active regimes
# """

# from datetime import date, datetime
# from typing import Optional
# from typing import Any

# from app.services.regime_api_service import RegimeAPIService

# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from sqlalchemy.orm import Session

# from app.database.session import SessionLocal
# from app.models.macro_regime import MacroRegime
# from app.models.current_regime import CurrentRegime
# from app.models.regime_performance import RegimePerformance
# from app.services.regime_performance_service import (
#     RegimePerformanceService,
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

# class RegimePerformanceResponse(BaseModel):
#     """
#     BTC performance during a macroeconomic regime.
#     """

#     avg_return: Optional[float] = None
#     max_drawdown: Optional[float] = None
#     volatility: Optional[float] = None
#     sharpe_ratio: Optional[float] = None

#     btc_price_start: Optional[float] = None
#     btc_price_end: Optional[float] = None

#     model_config = {
#         "from_attributes": True
#     }


# class RegimeResponse(BaseModel):
#     """
#     Historical macroeconomic regime response.
#     """

#     id: int
#     regime_type: str
#     start_date: date
#     end_date: Optional[date] = None

#     performance: Optional[
#         RegimePerformanceResponse
#     ] = None

#     model_config = {
#         "from_attributes": True
#     }


# class CurrentRegimeResponse(BaseModel):
#     """
#     Currently identified macroeconomic regime.

#     Includes confidence and visual classification
#     for the current regime.
#     """

#     id: int
#     regime_type: str
#     confidence: float
#     visual_indicator: str
#     identified_at: datetime
#     expires_at: Optional[datetime] = None

#     model_config = {
#         "from_attributes": True
#     }


# class BTCRegimeResponse(BaseModel):
#     """
#     Combined response for the BTC macroeconomic regime API.
#     """

#     current_regime: Optional[dict[str, Any]] = None

#     historical_regimes: list[dict[str, Any]] = []

#     similar_periods: list[dict[str, Any]] = []

#     event_analysis: list[dict[str, Any]] = []


# # ============================================================
# # CURRENT REGIME
# # ============================================================

# @router.get(
#     "/current",
#     response_model=CurrentRegimeResponse,
#     summary="Get current macroeconomic regime",
#     description="""
#     Returns the most recently identified current macroeconomic regime.

#     The regime is determined from the latest available
#     macroeconomic indicators collected from FRED.

#     The response includes:

#     - Regime type
#     - Confidence percentage
#     - Visual indicator
#     - Identification timestamp
#     - Optional expiration timestamp
#     """,
# )
# @limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
# async def get_current_regime(
#     request: Request,
#     db: Session = Depends(get_db),
# ):
#     """
#     Return the most recently identified current regime.
#     """

#     current_regime = (
#         db.query(CurrentRegime)
#         .order_by(
#             CurrentRegime.identified_at.desc()
#         )
#         .first()
#     )

#     if current_regime is None:
#         raise HTTPException(
#             status_code=404,
#             detail="No current macroeconomic regime found",
#         )

#     return CurrentRegimeResponse(
#         id=current_regime.id,
#         regime_type=current_regime.regime_type,
#         confidence=current_regime.confidence,
#         visual_indicator=current_regime.visual_indicator,
#         identified_at=current_regime.identified_at,
#         expires_at=current_regime.expires_at,
#     )


# # ============================================================
# # REGIME HISTORY
# # ============================================================

# @router.get(
#     "",
#     response_model=list[RegimeResponse],
#     summary="Get macroeconomic regime history",
#     description="""
#     Returns historical macroeconomic regimes.

#     Regimes are ordered from newest to oldest.

#     Completed regimes include BTC performance metrics
#     when available.
#     """,
# )
# @limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
# async def get_regime_history(
#     request: Request,
#     db: Session = Depends(get_db),
# ):
#     """
#     Return historical macroeconomic regimes.
#     """

#     regimes = (
#         db.query(MacroRegime)
#         .order_by(
#             MacroRegime.start_date.desc()
#         )
#         .all()
#     )

#     results = []

#     for regime in regimes:

#         performance = (
#             db.query(RegimePerformance)
#             .filter(
#                 RegimePerformance.regime_id
#                 == regime.id
#             )
#             .order_by(
#                 RegimePerformance.created_at.desc()
#             )
#             .first()
#         )

#         results.append(
#             RegimeResponse(
#                 id=regime.id,
#                 regime_type=regime.regime_type,
#                 start_date=regime.start_date,
#                 end_date=regime.end_date,
#                 performance=performance,
#             )
#         )

#     return results


# # ============================================================
# # BTC PERFORMANCE
# # ============================================================

# @router.get(
#     "/performance",
#     summary="Get BTC performance by macroeconomic regime",
#     description="""
#     Returns BTC performance metrics associated with
#     macroeconomic regimes.

#     Completed regimes use persisted RegimePerformance records.

#     The currently active regime is calculated dynamically
#     from the existing BTCPrice data.
#     """,
# )
# @limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
# async def get_regime_performance(
#     request: Request,
#     db: Session = Depends(get_db),
# ):
#     """
#     Return BTC performance for completed and active regimes.
#     """

#     service = RegimePerformanceService(db)

#     results = []

#     # ========================================================
#     # COMPLETED REGIMES
#     # ========================================================

#     completed_regimes = (
#         db.query(MacroRegime)
#         .filter(
#             MacroRegime.end_date.isnot(None)
#         )
#         .order_by(
#             MacroRegime.start_date.desc()
#         )
#         .all()
#     )

#     for regime in completed_regimes:

#         performance = (
#             db.query(RegimePerformance)
#             .filter(
#                 RegimePerformance.regime_id
#                 == regime.id
#             )
#             .order_by(
#                 RegimePerformance.created_at.desc()
#             )
#             .first()
#         )

#         if performance is None:
#             continue

#         results.append(
#             {
#                 "regime_id": regime.id,
#                 "regime_type": regime.regime_type,
#                 "start_date": regime.start_date,
#                 "end_date": regime.end_date,
#                 "status": "completed",
#                 "performance": {
#                     "avg_return": performance.avg_return,
#                     "max_drawdown": performance.max_drawdown,
#                     "volatility": performance.volatility,
#                     "sharpe_ratio": performance.sharpe_ratio,
#                     "btc_price_start": performance.btc_price_start,
#                     "btc_price_end": performance.btc_price_end,
#                 },
#             }
#         )

#     # ========================================================
#     # ACTIVE REGIME
#     # ========================================================

#     active_regime = (
#         db.query(MacroRegime)
#         .filter(
#             MacroRegime.end_date.is_(None)
#         )
#         .order_by(
#             MacroRegime.start_date.desc()
#         )
#         .first()
#     )

#     if active_regime is not None:

#         prices = service.get_regime_prices(
#             active_regime
#         )

#         if len(prices) >= 2:

#             metrics = service.calculate_metrics(
#                 prices
#             )

#             results.append(
#                 {
#                     "regime_id": active_regime.id,
#                     "regime_type": active_regime.regime_type,
#                     "start_date": active_regime.start_date,
#                     "end_date": None,
#                     "status": "active",
#                     "performance": {
#                         "avg_return": metrics["avg_return"],
#                         "max_drawdown": metrics["max_drawdown"],
#                         "volatility": metrics["volatility"],
#                         "sharpe_ratio": metrics["sharpe_ratio"],
#                         "btc_price_start": metrics[
#                             "btc_price_start"
#                         ],
#                         "btc_price_end": metrics[
#                             "btc_price_end"
#                         ],
#                     },
#                 }
#             )

#     return results


# # ============================================================
# # BTC REGIME SUMMARY
# # ============================================================

# @router.get(
#     "/btc",
#     response_model=BTCRegimeResponse,
#     summary="Get BTC macroeconomic regime analysis",
#     description="""
#     Returns the complete macroeconomic regime analysis for Bitcoin.

#     The response includes:

#     - Current macroeconomic regime
#     - Historical regimes
#     - BTC performance metrics for historical regimes
#     - Similar historical periods
#     - Macro event analysis

#     Optional filters:

#     - regime_type
#     - start_date
#     - end_date

#     Results are returned in JSON format.
#     """,
# )
# @limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
# async def get_btc_regime(
#     request: Request,
#     regime_type: Optional[str] = None,
#     start_date: Optional[date] = None,
#     end_date: Optional[date] = None,
#     similar_limit: int = 5,
#     db: Session = Depends(get_db),
# ):
#     """
#     Return the combined BTC macroeconomic regime analysis.
#     """

#     # --------------------------------------------------------
#     # Validate similar-period limit
#     # --------------------------------------------------------

#     if similar_limit < 1 or similar_limit > 10:
#         raise HTTPException(
#             status_code=400,
#             detail="similar_limit must be between 1 and 10",
#         )

#     # --------------------------------------------------------
#     # Validate date range
#     # --------------------------------------------------------

#     if (
#         start_date is not None
#         and end_date is not None
#         and start_date > end_date
#     ):
#         raise HTTPException(
#             status_code=400,
#             detail="start_date cannot be later than end_date",
#         )

#     # --------------------------------------------------------
#     # Build combined response
#     # --------------------------------------------------------

#     service = RegimeAPIService(db)

#     return service.get_btc_regime_data(
#         regime_type=regime_type,
#         start_date=start_date,
#         end_date=end_date,
#         similar_limit=similar_limit,
#     )


# # ============================================================
# # REGIME BY ID
# # ============================================================

# @router.get(
#     "/{regime_id}",
#     response_model=RegimeResponse,
#     summary="Get macroeconomic regime by ID",
#     description="""
#     Returns a specific historical macroeconomic regime
#     and its associated BTC performance metrics.
#     """,
# )
# @limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
# async def get_regime(
#     request: Request,
#     regime_id: int,
#     db: Session = Depends(get_db),
# ):
#     """
#     Return a specific macroeconomic regime.
#     """

#     regime = (
#         db.query(MacroRegime)
#         .filter(
#             MacroRegime.id == regime_id
#         )
#         .first()
#     )

#     if regime is None:
#         raise HTTPException(
#             status_code=404,
#             detail=f"Macroeconomic regime {regime_id} not found",
#         )

#     performance = (
#         db.query(RegimePerformance)
#         .filter(
#             RegimePerformance.regime_id
#             == regime.id
#         )
#         .order_by(
#             RegimePerformance.created_at.desc()
#         )
#         .first()
#     )

#     return RegimeResponse(
#         id=regime.id,
#         regime_type=regime.regime_type,
#         start_date=regime.start_date,
#         end_date=regime.end_date,
#         performance=performance,
#     )


"""
Macroeconomic Regime API.

Provides API endpoints for retrieving:
- Current macroeconomic regime
- Historical macroeconomic regimes
- BTC performance during completed and active regimes
"""

import logging
from datetime import date, datetime
from typing import Optional
from typing import Any

from app.services.regime_api_service import RegimeAPIService

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.macro_regime import MacroRegime
from app.models.current_regime import CurrentRegime
from app.models.regime_performance import RegimePerformance
from app.services.regime_performance_service import (
    RegimePerformanceService,
)
from fastapi import Request
from app.core.rate_limit import limiter
from app.config import settings


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/regimes",
    tags=["Macroeconomic Regimes"],
)


# ============================================================
# CACHE CONFIGURATION
# ============================================================

REGIME_CACHE_TTL = settings.MACRO_REGIME_CACHE_TTL


def get_btc_regime_cache_key(
    regime_type: Optional[str],
    start_date: Optional[date],
    end_date: Optional[date],
    similar_limit: int,
) -> str:
    """
    Return the cache key for a BTC regime response.

    Cache keys include all request parameters that affect
    the response so different filtered requests do not
    share the wrong cached response.
    """

    regime_type_key = (
        regime_type
        if regime_type
        else "all"
    )

    start_date_key = (
        start_date.isoformat()
        if start_date
        else "none"
    )

    end_date_key = (
        end_date.isoformat()
        if end_date
        else "none"
    )

    return (
        "macro_regimes:btc:"
        f"{regime_type_key}:"
        f"{start_date_key}:"
        f"{end_date_key}:"
        f"limit_{similar_limit}"
    )


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():
    """
    Provide a database session for API requests.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# RESPONSE MODELS
# ============================================================

class RegimePerformanceResponse(BaseModel):
    """
    BTC performance during a macroeconomic regime.
    """

    avg_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    volatility: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    btc_price_start: Optional[float] = None
    btc_price_end: Optional[float] = None

    model_config = {
        "from_attributes": True
    }


class RegimeResponse(BaseModel):
    """
    Historical macroeconomic regime response.
    """

    id: int
    regime_type: str
    start_date: date
    end_date: Optional[date] = None

    performance: Optional[
        RegimePerformanceResponse
    ] = None

    model_config = {
        "from_attributes": True
    }


class CurrentRegimeResponse(BaseModel):
    """
    Currently identified macroeconomic regime.

    Includes confidence and visual classification
    for the current regime.
    """

    id: int
    regime_type: str
    confidence: float
    visual_indicator: str
    identified_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class BTCRegimeResponse(BaseModel):
    """
    Combined response for the BTC macroeconomic regime API.
    """

    current_regime: Optional[dict[str, Any]] = None

    historical_regimes: list[dict[str, Any]] = []

    similar_periods: list[dict[str, Any]] = []

    event_analysis: list[dict[str, Any]] = []


# ============================================================
# CURRENT REGIME
# ============================================================

@router.get(
    "/current",
    response_model=CurrentRegimeResponse,
    summary="Get current macroeconomic regime",
    description="""
    Returns the most recently identified current macroeconomic regime.

    The regime is determined from the latest available
    macroeconomic indicators collected from FRED.

    The response includes:

    - Regime type
    - Confidence percentage
    - Visual indicator
    - Identification timestamp
    - Optional expiration timestamp
    """,
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_current_regime(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Return the most recently identified current regime.
    """

    current_regime = (
        db.query(CurrentRegime)
        .order_by(
            CurrentRegime.identified_at.desc()
        )
        .first()
    )

    if current_regime is None:
        raise HTTPException(
            status_code=404,
            detail="No current macroeconomic regime found",
        )

    return CurrentRegimeResponse(
        id=current_regime.id,
        regime_type=current_regime.regime_type,
        confidence=current_regime.confidence,
        visual_indicator=current_regime.visual_indicator,
        identified_at=current_regime.identified_at,
        expires_at=current_regime.expires_at,
    )


# ============================================================
# REGIME HISTORY
# ============================================================

@router.get(
    "",
    response_model=list[RegimeResponse],
    summary="Get macroeconomic regime history",
    description="""
    Returns historical macroeconomic regimes.

    Regimes are ordered from newest to oldest.

    Completed regimes include BTC performance metrics
    when available.
    """,
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_regime_history(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Return historical macroeconomic regimes.
    """

    regimes = (
        db.query(MacroRegime)
        .order_by(
            MacroRegime.start_date.desc()
        )
        .all()
    )

    results = []

    for regime in regimes:

        performance = (
            db.query(RegimePerformance)
            .filter(
                RegimePerformance.regime_id
                == regime.id
            )
            .order_by(
                RegimePerformance.created_at.desc()
            )
            .first()
        )

        results.append(
            RegimeResponse(
                id=regime.id,
                regime_type=regime.regime_type,
                start_date=regime.start_date,
                end_date=regime.end_date,
                performance=performance,
            )
        )

    return results


# ============================================================
# BTC PERFORMANCE
# ============================================================

@router.get(
    "/performance",
    summary="Get BTC performance by macroeconomic regime",
    description="""
    Returns BTC performance metrics associated with
    macroeconomic regimes.

    Completed regimes use persisted RegimePerformance records.

    The currently active regime is calculated dynamically
    from the existing BTCPrice data.
    """,
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_regime_performance(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Return BTC performance for completed and active regimes.
    """

    service = RegimePerformanceService(db)

    results = []

    # ========================================================
    # COMPLETED REGIMES
    # ========================================================

    completed_regimes = (
        db.query(MacroRegime)
        .filter(
            MacroRegime.end_date.isnot(None)
        )
        .order_by(
            MacroRegime.start_date.desc()
        )
        .all()
    )

    for regime in completed_regimes:

        performance = (
            db.query(RegimePerformance)
            .filter(
                RegimePerformance.regime_id
                == regime.id
            )
            .order_by(
                RegimePerformance.created_at.desc()
            )
            .first()
        )

        if performance is None:
            continue

        results.append(
            {
                "regime_id": regime.id,
                "regime_type": regime.regime_type,
                "start_date": regime.start_date,
                "end_date": regime.end_date,
                "status": "completed",
                "performance": {
                    "avg_return": performance.avg_return,
                    "max_drawdown": performance.max_drawdown,
                    "volatility": performance.volatility,
                    "sharpe_ratio": performance.sharpe_ratio,
                    "btc_price_start": performance.btc_price_start,
                    "btc_price_end": performance.btc_price_end,
                },
            }
        )

    # ========================================================
    # ACTIVE REGIME
    # ========================================================

    active_regime = (
        db.query(MacroRegime)
        .filter(
            MacroRegime.end_date.is_(None)
        )
        .order_by(
            MacroRegime.start_date.desc()
        )
        .first()
    )

    if active_regime is not None:

        prices = service.get_regime_prices(
            active_regime
        )

        if len(prices) >= 2:

            metrics = service.calculate_metrics(
                prices
            )

            results.append(
                {
                    "regime_id": active_regime.id,
                    "regime_type": active_regime.regime_type,
                    "start_date": active_regime.start_date,
                    "end_date": None,
                    "status": "active",
                    "performance": {
                        "avg_return": metrics["avg_return"],
                        "max_drawdown": metrics["max_drawdown"],
                        "volatility": metrics["volatility"],
                        "sharpe_ratio": metrics["sharpe_ratio"],
                        "btc_price_start": metrics[
                            "btc_price_start"
                        ],
                        "btc_price_end": metrics[
                            "btc_price_end"
                        ],
                    },
                }
            )

    return results


# ============================================================
# BTC REGIME SUMMARY
# ============================================================

@router.get(
    "/btc",
    response_model=BTCRegimeResponse,
    summary="Get BTC macroeconomic regime analysis",
    description="""
    Returns the complete macroeconomic regime analysis for Bitcoin.

    The response includes:

    - Current macroeconomic regime
    - Historical regimes
    - BTC performance metrics for historical regimes
    - Similar historical periods
    - Macro event analysis

    Optional filters:

    - regime_type
    - start_date
    - end_date

    Results are returned in JSON format.

    Redis caching is used to reduce repeated database and
    similarity-analysis queries.
    """,
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_btc_regime(
    request: Request,
    regime_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    similar_limit: int = 5,
    db: Session = Depends(get_db),
):
    """
    Return the combined BTC macroeconomic regime analysis.

    Redis cache-aside flow:

        1. Validate request parameters.
        2. Check Redis.
        3. Return immediately on cache hit.
        4. Create database session only on cache miss.
        5. Build response through RegimeAPIService.
        6. Store complete response in Redis.
        7. Return response.
    """

    # --------------------------------------------------------
    # 1. Validate similar-period limit
    # --------------------------------------------------------

    if similar_limit < 1 or similar_limit > 10:
        raise HTTPException(
            status_code=400,
            detail="similar_limit must be between 1 and 10",
        )

    # --------------------------------------------------------
    # 2. Validate date range
    # --------------------------------------------------------

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be later than end_date",
        )

    # --------------------------------------------------------
    # 3. Get cache client
    # --------------------------------------------------------

    cache_client = getattr(
        request.app.state,
        "cache_client",
        None,
    )

    cache_key = get_btc_regime_cache_key(
        regime_type=regime_type,
        start_date=start_date,
        end_date=end_date,
        similar_limit=similar_limit,
    )

    logger.info(
        f"Redis client: {cache_client}, "
        f"connected={getattr(cache_client, 'is_connected', None)}, "
        f"key={cache_key}"
    )

    # --------------------------------------------------------
    # 4. Redis cache lookup
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
                # No RegimeAPIService()
                # No TimescaleDB/PostgreSQL query.
                # No similar-period calculation.

                return BTCRegimeResponse(
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
    # 5. Cache miss -> database/service layer
    # --------------------------------------------------------

    logger.info(
        "Reading BTC regime analysis from database "
        f"(regime_type={regime_type}, "
        f"start_date={start_date}, "
        f"end_date={end_date}, "
        f"similar_limit={similar_limit})"
    )

    db = SessionLocal()

    try:
        service = RegimeAPIService(db)

        result = service.get_btc_regime_data(
            regime_type=regime_type,
            start_date=start_date,
            end_date=end_date,
            similar_limit=similar_limit,
        )

        response = BTCRegimeResponse(
            **result
        )

    finally:
        db.close()

        logger.info(
            "Database session closed"
        )

    # --------------------------------------------------------
    # 6. Store complete API response in Redis
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
                ttl=REGIME_CACHE_TTL,
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


# ============================================================
# REGIME BY ID
# ============================================================

@router.get(
    "/{regime_id}",
    response_model=RegimeResponse,
    summary="Get macroeconomic regime by ID",
    description="""
    Returns a specific historical macroeconomic regime
    and its associated BTC performance metrics.
    """,
)
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def get_regime(
    request: Request,
    regime_id: int,
    db: Session = Depends(get_db),
):
    """
    Return a specific macroeconomic regime.
    """

    regime = (
        db.query(MacroRegime)
        .filter(
            MacroRegime.id == regime_id
        )
        .first()
    )

    if regime is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Macroeconomic regime "
                f"{regime_id} not found"
            ),
        )

    performance = (
        db.query(RegimePerformance)
        .filter(
            RegimePerformance.regime_id
            == regime.id
        )
        .order_by(
            RegimePerformance.created_at.desc()
        )
        .first()
    )

    return RegimeResponse(
        id=regime.id,
        regime_type=regime.regime_type,
        start_date=regime.start_date,
        end_date=regime.end_date,
        performance=performance,
    )