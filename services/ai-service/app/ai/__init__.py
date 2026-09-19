"""AI Service — Machine learning utilities and model interfaces.

This package contains:
    - ForecastModel: Abstract base class for all forecasting models
    - RetrainingOrchestrator: Shared retraining logic for all models
    - Model implementations: ProphetModel (XGBoost, LightGBM — later)
    - Feature engineering utilities — later branches
    - Training and prediction logic — later branches
"""

from app.ai.base import ForecastModel
from app.ai.orchestrator import RetrainingOrchestrator, RetrainResult
from app.ai.models import ProphetModel

__all__ = [
    "ForecastModel",
    "RetrainingOrchestrator",
    "RetrainResult",
    "ProphetModel",
]