"""AI Service — Machine learning utilities and model interfaces.

This package contains:
    - ForecastModel: Abstract base class for all forecasting models
    - RetrainingOrchestrator: Orchestrates retraining of all models
    - Model implementations (Prophet, XGBoost, LightGBM) — later branches
    - Feature engineering utilities — later branches
    - Training and prediction logic — later branches
"""

from app.ai.base import ForecastModel
from app.ai.orchestrator import RetrainingOrchestrator, RetrainResult

__all__ = [
    "ForecastModel",
    "RetrainingOrchestrator",
    "RetrainResult",
]