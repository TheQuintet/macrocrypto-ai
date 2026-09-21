"""AI Service — Model configuration package.

This package contains per-model, per-horizon configuration dataclasses
and helpers. Each configuration captures the exact parameters used
for training and prediction, so results are reproducible.

Configurations available:
    - ProphetConfig: Base Prophet configuration (shared by all horizons)
    - Prophet24hConfig: Prophet configuration for 24-hour BTC predictions
    - Prophet7dConfig: Prophet configuration for 7-day BTC predictions

Future configurations (later branches):
    - XGBoost24hConfig, XGBoost7dConfig: XGBoost configurations
    - LightGBM24hConfig, LightGBM7dConfig: LightGBM configurations
"""

from app.ai.configs.base import ProphetConfig
from app.ai.configs.prophet_24h import (
    Prophet24hConfig,
    build_prophet_kwargs as build_prophet_24h_kwargs,
    PROPHET_24H_CONFIG,
)
from app.ai.configs.prophet_7d import (
    Prophet7dConfig,
    build_prophet_kwargs as build_prophet_7d_kwargs,
    PROPHET_7D_CONFIG,
)

__all__ = [
    "ProphetConfig",
    "Prophet24hConfig",
    "Prophet7dConfig",
    "build_prophet_24h_kwargs",
    "build_prophet_7d_kwargs",
    "PROPHET_24H_CONFIG",
    "PROPHET_7D_CONFIG",
]