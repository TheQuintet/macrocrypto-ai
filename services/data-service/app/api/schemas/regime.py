"""
Schemas for regime API responses.

Sprint 4 - A3.7
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class RegimePerformanceResponse(BaseModel):
    regime_id: int

    avg_return: float | None = None
    max_drawdown: float | None = None
    volatility: float | None = None
    sharpe_ratio: float | None = None

    btc_price_start: float | None = None
    btc_price_end: float | None = None


class RegimeResponse(BaseModel):
    id: int
    regime_type: str
    start_date: date
    end_date: date | None = None
    duration_days: int | None = None
    performance: RegimePerformanceResponse | None = None


class CurrentRegimeResponse(BaseModel):
    regime_type: str
    confidence: float
    visual_indicator: str
    identified_at: datetime
    expires_at: datetime | None = None


class SimilarPeriodResponse(BaseModel):
    start_date: date
    end_date: date | None = None
    regime_type: str
    distance: float | None = None
    reasoning: str | None = None
    btc_performance: float | None = None


class EventAnalysisResponse(BaseModel):
    id: int
    regime_id: int
    event_type: str
    event_date: datetime
    event_value: float | None = None
    btc_price_before: float
    btc_price_after: float
    btc_reaction_percent: float
    reaction_window_hours: int
    source: str
    reasoning: str | None = None


class BTCRegimeResponse(BaseModel):
    regimes: list[RegimeResponse]
    current_regime: CurrentRegimeResponse | None
    similar_periods: list[SimilarPeriodResponse]
    event_analysis: list[EventAnalysisResponse]