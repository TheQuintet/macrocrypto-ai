"""
Macroeconomic Regime API.

Provides API endpoints for retrieving:
- Current macroeconomic regime
- Historical macroeconomic regimes
- BTC performance during completed regimes
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.macro_regime import MacroRegime
from app.models.regime_performance import RegimePerformance


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
    Macroeconomic regime response.
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


# ============================================================
# CURRENT REGIME
# ============================================================

@router.get(
    "/current",
    response_model=RegimeResponse,
    summary="Get current macroeconomic regime",
    description="""
    Returns the currently active macroeconomic regime.

    The regime is determined from the latest available
    macroeconomic indicators collected from FRED.

    The response includes BTC performance when performance
    data is available.
    """,
)
async def get_current_regime(
    db: Session = Depends(get_db),
):
    """
    Return the currently active macroeconomic regime.
    """

    regime = (
        db.query(MacroRegime)
        .filter(
            MacroRegime.end_date.is_(None)
        )
        .order_by(
            MacroRegime.start_date.desc()
        )
        .first()
    )

    if regime is None:
        raise HTTPException(
            status_code=404,
            detail="No active macroeconomic regime found",
        )

    performance = (
        db.query(RegimePerformance)
        .filter(
            RegimePerformance.regime_id == regime.id
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
async def get_regime_history(
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
# REGIME BY ID
# ============================================================

@router.get(
    "/{regime_id}",
    response_model=RegimeResponse,
    summary="Get macroeconomic regime by ID",
    description="""
    Returns a specific macroeconomic regime and its
    associated BTC performance metrics.
    """,
)
async def get_regime(
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
            detail=f"Macroeconomic regime {regime_id} not found",
        )

    performance = (
        db.query(RegimePerformance)
        .filter(
            RegimePerformance.regime_id
            == regime.id
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