"""AI Service — Machine learning utilities and model interfaces.

This package contains:
    - ForecastModel: Abstract base class for all forecasting models
    - RetrainingOrchestrator: Shared retraining logic for all models
    - ModelComparisonEngine: Runs multiple models and compares them
    - build_default_engine: Factory for all 6 default model variants
    - Model implementations: ProphetModel, XGBoostModel, LightGBMModel
    - Configurations: Per-model, per-horizon config dataclasses
    - Feature engineering utilities — later branches
    - Training and prediction logic — later branches
"""

from app.ai.base import ForecastModel
from app.ai.orchestrator import RetrainingOrchestrator, RetrainResult
from app.ai.comparison import (
    ModelComparisonEngine,
    ComparisonResult,
    ModelPrediction,
    build_default_engine,
)
from app.ai.models import ProphetModel, XGBoostModel, LightGBMModel
from app.ai.configs import (
    ProphetConfig,
    Prophet24hConfig,
    Prophet7dConfig,
    build_prophet_24h_kwargs,
    build_prophet_7d_kwargs,
    PROPHET_24H_CONFIG,
    PROPHET_7D_CONFIG,
)

__all__ = [
    "ForecastModel",
    "RetrainingOrchestrator",
    "RetrainResult",
    "ModelComparisonEngine",
    "ComparisonResult",
    "ModelPrediction",
    "build_default_engine",
    "ProphetModel",
    "XGBoostModel",
    "LightGBMModel",
    "ProphetConfig",
    "Prophet24hConfig",
    "Prophet7dConfig",
    "build_prophet_24h_kwargs",
    "build_prophet_7d_kwargs",
    "PROPHET_24H_CONFIG",
    "PROPHET_7D_CONFIG",
]