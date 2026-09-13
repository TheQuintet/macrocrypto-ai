"""AI Service — Model implementations.

This package contains concrete implementations of the ForecastModel
interface for each supported model:
    - ProphetModel (Prophet)
    - XGBoostModel (XGBoost)
    - LightGBMModel (LightGBM) — later branch
"""

from app.ai.models.prophet_model import ProphetModel
from app.ai.models.xgboost_model import XGBoostModel

__all__ = [
    "ProphetModel",
    "XGBoostModel",
]