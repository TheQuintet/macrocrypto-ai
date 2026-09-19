"""AI Service — Prediction generation package.

This package contains the prediction generation pipeline:
    - PredictionGenerator: orchestrates load → predict → save
    - GenerationResult: structured result of one generation run
    - Trend helpers: direction classification and percentage change

Entry points (runnable scripts):
    - app.prediction.generate_24h: 24-hour prediction CLI (T1.2)
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

__all__ = [
    "PredictionGenerator",
    "GenerationResult",
    "calculate_price_change_pct",
    "calculate_trend",
    "calculate_trend_and_change",
    "TREND_THRESHOLD_24H",
    "TREND_THRESHOLD_7D",
    "TREND_THRESHOLDS",
]