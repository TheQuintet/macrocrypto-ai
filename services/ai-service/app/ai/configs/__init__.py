"""AI Service — Model configuration package.

This package contains per-model, per-horizon configuration dataclasses
and helpers. Each configuration captures the exact parameters used
for training and prediction, so results are reproducible.

Configurations available:
    - Prophet24hConfig: Prophet configuration for 24-hour BTC predictions
    - ProphetConfig: Base Prophet configuration (shared by all horizons)

Future configurations (later branches):
    - Prophet7dConfig: Prophet configuration for 7-day predictions (T2.1)
    - XGBoost24hConfig, XGBoost7dConfig: XGBoost configurations
    - LightGBM24hConfig, LightGBM7dConfig: LightGBM configurations
"""

from app.ai.configs.base import ProphetConfig
from app.ai.configs.prophet_24h import (
    Prophet24hConfig,
    build_prophet_kwargs,
    PROPHET_24H_CONFIG,
)

__all__ = [
    "ProphetConfig",
    "Prophet24hConfig",
    "build_prophet_kwargs",
    "PROPHET_24H_CONFIG",
]