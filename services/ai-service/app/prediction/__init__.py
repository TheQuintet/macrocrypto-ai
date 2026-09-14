"""AI Service — Prediction generation package.

This package contains the prediction generation pipeline:
    - PredictionGenerator: orchestrates load → predict → save
    - GenerationResult: structured result of one generation run

Entry points (runnable scripts):
    - app.prediction.generate_24h: 24-hour prediction CLI (T1.2)
"""

from app.prediction.generator import (
    GenerationResult,
    PredictionGenerator,
)

__all__ = [
    "PredictionGenerator",
    "GenerationResult",
]