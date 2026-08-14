"""
API endpoints for similar historical macroeconomic periods.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.services.similar_period_service import (
    SimilarPeriodService,
)


router = APIRouter(
    prefix="/api/v1/regimes",
    tags=["Macroeconomic Regimes"],
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
    """,
)
async def get_similar_periods(
    limit: int = Query(
        default=5,
        ge=3,
        le=5,
        description=(
            "Number of similar historical periods to return."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Return historical macroeconomic periods similar
    to the current environment.
    """

    service = SimilarPeriodService(db)

    try:
        return service.find_similar_periods(
            limit=limit
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate similar "
                "historical periods"
            ),
        ) from exc