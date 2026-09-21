"""AI Service — Prediction generation package.

This package contains the prediction generation pipeline:
    - PredictionGenerator: orchestrates load → predict → save
    - GenerationResult: structured result of one generation run
    - Trend helpers: direction classification and percentage change
    - Market condition classifier: bull/bear/volatile/neutral labels

Entry points (runnable scripts):
    - app.prediction.generate_24h: 24-hour prediction CLI (T1.2)
    - app.prediction.generate_7d: 7-day prediction CLI (T2.2)
"""

from app.prediction.generator import (
    GenerationResult,
    PredictionGenerator,
)
from app.prediction.trend import (
    calculate_price_change_pct,
    calculate_trend,
    calculate_trend_and_change,
    TREND_THRESHOLD_24H,
    TREND_THRESHOLD_7D,
    TREND_THRESHOLDS,
)
from app.prediction.market import (
    ALL_CONDITIONS,
    CONDITION_BEAR,
    CONDITION_BULL,
    CONDITION_NEUTRAL,
    CONDITION_PRIORITY,
    CONDITION_VOLATILE,
    classify_market_condition,
    classify_market_condition_safe,
    cumulative_return_pct,
    return_volatility_pct,
)

__all__ = [
    "PredictionGenerator",
    "GenerationResult",
    "calculate_price_change_pct",
    "calculate_trend",
    "calculate_trend_and_change",
    "TREND_THRESHOLD_24H",
    "TREND_THRESHOLD_7D",
    "TREND_THRESHOLDS",
    "ALL_CONDITIONS",
    "CONDITION_BEAR",
    "CONDITION_BULL",
    "CONDITION_NEUTRAL",
    "CONDITION_PRIORITY",
    "CONDITION_VOLATILE",
    "classify_market_condition",
    "classify_market_condition_safe",
    "cumulative_return_pct",
    "return_volatility_pct",
]