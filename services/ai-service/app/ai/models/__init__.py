"""AI Service — Model implementations.

This package contains concrete implementations of the ForecastModel
interface for each supported model:
    - ProphetModel (Prophet)
    - XGBoostModel (XGBoost)
    - LightGBMModel (LightGBM)
"""

from app.ai.models.prophet_model import ProphetModel
from app.ai.models.xgboost_model import XGBoostModel
from app.ai.models.lightgbm_model import LightGBMModel

__all__ = [
    "ProphetModel",
    "XGBoostModel",
    "LightGBMModel",
]