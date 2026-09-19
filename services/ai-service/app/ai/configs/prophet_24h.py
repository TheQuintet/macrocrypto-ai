"""Prophet 24-hour configuration for BTC price predictions.

This module defines the exact Prophet configuration used for
24-hour BTC price forecasts. It is tuned for hourly data:
    - Hourly seasonality enabled (intraday patterns)
    - Daily seasonality enabled (24h cycle)
    - Weekly seasonality enabled (weekday/weekend effects)
    - Regressors: all 10 macro + BTC features

The configuration is exposed as:
    - Prophet24hConfig: the dataclass definition (frozen, immutable)
    - PROPHET_24H_CONFIG: a ready-to-use singleton instance
    - build_prophet_kwargs(): helper returning Prophet() kwargs

Design rationale:
    - changepoint_prior_scale=0.05: conservative trend flexibility
      to avoid overfitting to intraday noise
    - seasonality_prior_scale=10.0: strong seasonality, since BTC has
      well-documented daily and weekly cycles
    - seasonality_mode="multiplicative": BTC price levels scale
      seasonality amplitude; a 2% daily cycle at $20k is smaller in
      absolute terms than at $100k
    - interval_width=0.95: native Prophet uncertainty at 95%; narrower
      intervals (70%, 85%) are scaled down by the adapter
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.ai.configs.base import PROPHET_REGRESSORS, ProphetConfig

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
HORIZON_LABEL = "24h"
HORIZON_HOURS = 24
HORIZON_DAYS = 1
FORECAST_FREQ = "H"


# ============================================================
# 24H PROPHET CONFIG (DATACLASS)
# ============================================================
@dataclass(frozen=True)
class Prophet24hConfig(ProphetConfig):
    """Prophet configuration specialized for 24-hour BTC predictions.

    Overrides base defaults to enable hourly + daily + weekly
    seasonalities, which is the correct combination for a 24-hour
    forecast horizon.

    Inherits all fields and methods from ProphetConfig; only the
    defaults differ.

    Default values chosen:
        - horizon_label = "24h"
        - horizon_hours = 24
        - horizon_days = 1
        - freq = "H"  (hourly)
        - hourly_seasonality = True
        - daily_seasonality = True
        - weekly_seasonality = True
        - yearly_seasonality = False  (irrelevant over a 24h horizon)
        - interval_width = 0.95
        - regressors = all 10 base features
    """

    horizon_label: str = HORIZON_LABEL
    horizon_hours: int = HORIZON_HOURS
    horizon_days: int = HORIZON_DAYS
    freq: str = FORECAST_FREQ

    # Enable hourly + daily + weekly, disable yearly
    yearly_seasonality: bool = False
    weekly_seasonality: bool = True
    daily_seasonality: bool = True
    hourly_seasonality: bool = True

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
PROPHET_24H_CONFIG: Prophet24hConfig = Prophet24hConfig()
PROPHET_24H_CONFIG.validate()


# ============================================================
# HELPER: BUILD PROPHET KWARGS
# ============================================================
def build_prophet_kwargs(
    config: Prophet24hConfig = PROPHET_24H_CONFIG,
) -> Dict[str, Any]:
    """Build the exact kwargs to pass to Prophet() for 24h forecasts.

    The returned dict can be passed directly to the ProphetModel
    adapter's `config` parameter:

        from app.ai.configs.prophet_24h import build_prophet_kwargs
        from app.ai.models import ProphetModel

        model = ProphetModel(
            strategy="fresh",
            config=build_prophet_kwargs(),
        )

    Note: the adapter merges these kwargs on top of its own
    DEFAULT_CONFIG, so any keys not present here retain the adapter's
    defaults.

    Args:
        config: The 24h Prophet configuration. Defaults to the
            module-level singleton.

    Returns:
        Dictionary of Prophet kwargs (without regressors, which are
        added separately by the adapter).
    """
    kwargs = config.to_prophet_kwargs()

    logger.debug(
        f"Built Prophet kwargs for 24h config: {list(kwargs.keys())}"
    )

    return kwargs


# ============================================================
# HELPER: BUILD ADAPTER CONFIG
# ============================================================
def build_adapter_config(
    config: Prophet24hConfig = PROPHET_24H_CONFIG,
) -> Dict[str, Any]:
    """Alias for build_prophet_kwargs(), provided for readability.

    Use this when you want the intent to be clear that you're
    building a config for the ProphetModel adapter (as opposed to
    instantiating Prophet directly).

    Args:
        config: The 24h Prophet configuration.

    Returns:
        Dictionary of Prophet kwargs.
    """
    return build_prophet_kwargs(config)