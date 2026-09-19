"""AI Service — Machine learning utilities and model interfaces.

This package contains:
    - ForecastModel: Abstract base class for all forecasting models
    - Model implementations (Prophet, XGBoost, LightGBM)
    - Feature engineering utilities
    - Training and prediction logic
"""

from app.ai.base import ForecastModel

__all__ = [
    "ForecastModel",
]