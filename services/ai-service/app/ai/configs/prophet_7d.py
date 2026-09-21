"""Prophet 7-day configuration for BTC price predictions.

This module defines the exact Prophet configuration used for
7-day BTC price forecasts. It is tuned for daily data:
    - Daily seasonality disabled (data is already aggregated per day)
    - Weekly seasonality enabled (weekday/weekend effects)
    - Yearly seasonality enabled (7-day horizon can see year-scale patterns)
    - Regressors: all 10 macro + BTC features

The configuration is exposed as:
    - Prophet7dConfig: the dataclass definition (frozen, immutable)
    - PROPHET_7D_CONFIG: a ready-to-use singleton instance
    - build_prophet_kwargs(): helper returning Prophet() kwargs

Design rationale:
    - changepoint_prior_scale=0.10: more flexible trend tracking than
      the 24h config, since a 7-day horizon benefits from adapting to
      recent momentum
    - seasonality_prior_scale=5.0: weaker seasonality prior, since the
      seasonal signal is compressed over daily data
    - holidays_prior_scale=10.0: default
    - seasonality_mode="multiplicative": BTC price levels scale
      seasonality amplitude
    - interval_width=0.95: native Prophet uncertainty at 95%; narrower
      intervals (70%, 85%) are scaled down by the adapter

Differences vs. the 24h config:
    - freq: "D" (daily) instead of "H" (hourly)
    - horizon_hours: 168 instead of 24
    - horizon_days: 7 instead of 1
    - hourly_seasonality: False (irrelevant for daily data)
    - daily_seasonality: False (already aggregated per day)
    - yearly_seasonality: True (year-scale patterns matter over 7 days)
    - changepoint_prior_scale: 0.10 instead of 0.05
    - seasonality_prior_scale: 5.0 instead of 10.0
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.ai.configs.base import PROPHET_REGRESSORS, ProphetConfig

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
HORIZON_LABEL = "7d"
HORIZON_HOURS = 168  # 7 * 24
HORIZON_DAYS = 7
FORECAST_FREQ = "D"


# ============================================================
# 7D PROPHET CONFIG (DATACLASS)
# ============================================================
@dataclass(frozen=True)
class Prophet7dConfig(ProphetConfig):
    """Prophet configuration specialized for 7-day BTC predictions.

    Overrides base defaults to enable weekly + yearly seasonalities
    and disable daily + hourly seasonalities, which is the correct
    combination for a 7-day forecast horizon over daily data.

    Inherits all fields and methods from ProphetConfig; only the
    defaults differ.

    Default values chosen:
        - horizon_label = "7d"
        - horizon_hours = 168
        - horizon_days = 7
        - freq = "D"  (daily)
        - hourly_seasonality = False
        - daily_seasonality = False
        - weekly_seasonality = True
        - yearly_seasonality = True
        - changepoint_prior_scale = 0.10
        - seasonality_prior_scale = 5.0
        - interval_width = 0.95
        - regressors = all 10 base features
    """

    horizon_label: str = HORIZON_LABEL
    horizon_hours: int = HORIZON_HOURS
    horizon_days: int = HORIZON_DAYS
    freq: str = FORECAST_FREQ

    # Enable weekly + yearly; disable hourly + daily
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False
    hourly_seasonality: bool = False

    # Tuned hyperparameters for the 7-day horizon
    changepoint_prior_scale: float = 0.10
    seasonality_prior_scale: float = 5.0
    holidays_prior_scale: float = 10.0

    # Regressors: all 10 base features
    regressors: List[str] = field(
        default_factory=lambda: list(PROPHET_REGRESSORS)
    )

    # Confidence levels supported by the adapter
    confidence_levels: List[float] = field(
        default_factory=lambda: [0.70, 0.85, 0.95]
    )


# ============================================================
# SINGLETON INSTANCE
# ============================================================
PROPHET_7D_CONFIG: Prophet7dConfig = Prophet7dConfig()
PROPHET_7D_CONFIG.validate()


# ============================================================
# HELPER: BUILD PROPHET KWARGS
# ============================================================
def build_prophet_kwargs(
    config: Prophet7dConfig = PROPHET_7D_CONFIG,
) -> Dict[str, Any]:
    """Build the exact kwargs to pass to Prophet() for 7d forecasts.

    The returned dict can be passed directly to the ProphetModel
    adapter's `config` parameter:

        from app.ai.configs.prophet_7d import build_prophet_kwargs
        from app.ai.models import ProphetModel

        model = ProphetModel(
            strategy="fresh",
            config=build_prophet_kwargs(),
        )

    Note: the adapter merges these kwargs on top of its own
    DEFAULT_CONFIG, so any keys not present here retain the adapter's
    defaults.

    Args:
        config: The 7d Prophet configuration. Defaults to the
            module-level singleton.

    Returns:
        Dictionary of Prophet kwargs (without regressors, which are
        added separately by the adapter).
    """
    kwargs = config.to_prophet_kwargs()

    logger.debug(
        f"Built Prophet kwargs for 7d config: {list(kwargs.keys())}"
    )

    return kwargs


# ============================================================
# HELPER: BUILD ADAPTER CONFIG
# ============================================================
def build_adapter_config(
    config: Prophet7dConfig = PROPHET_7D_CONFIG,
) -> Dict[str, Any]:
    """Alias for build_prophet_kwargs(), provided for readability.

    Use this when you want the intent to be clear that you're
    building a config for the ProphetModel adapter (as opposed to
    instantiating Prophet directly).

    Args:
        config: The 7d Prophet configuration.

    Returns:
        Dictionary of Prophet kwargs.
    """
    return build_prophet_kwargs(config)