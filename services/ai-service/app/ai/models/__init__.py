"""AI Service — Model implementations.

This package contains concrete implementations of the ForecastModel
interface for each supported model:
    - ProphetModel (Prophet)
    - XGBoostModel (XGBoost) — later branch
    - LightGBMModel (LightGBM) — later branch
"""

from app.ai.models.prophet_model import ProphetModel

__all__ = [
    "ProphetModel",
]