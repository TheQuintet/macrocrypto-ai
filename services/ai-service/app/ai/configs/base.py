"""Base configuration dataclasses for forecasting models.

This module defines the shared configuration structure used by all
Prophet-based configurations. Horizon-specific configurations
(24h, 7d) extend or instantiate this base.

Design:
    - Frozen dataclasses for immutability
    - All Prophet parameters explicit (no hidden defaults at train time)
    - JSON serialization helpers for reproducibility artifacts
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


# ============================================================
# REGRESSORS
# ============================================================
# The 10 regressors used by all Prophet models in this service:
#   5 macro features + 5 BTC features
PROPHET_REGRESSORS: List[str] = [
    "cpi",
    "interest_rate",
    "m2_growth",
    "dxy",
    "treasury_yield",
    "volume",
    "volatility",
    "dominance",
    "active_addresses",
    "price_lag_7d",
]


# ============================================================
# BASE PROPHET CONFIG
# ============================================================
@dataclass(frozen=True)
class ProphetConfig:
    """Base Prophet configuration.

    Captures every parameter passed to Prophet() plus metadata about
    the intended horizon and regressors. Subclassed or instantiated
    per horizon by the specific config modules (e.g., prophet_24h).

    Attributes:
        horizon_label: Human-readable label (e.g., "24h", "7d").
        horizon_hours: Prediction horizon in hours.
        horizon_days: Prediction horizon in days (for daily models).
        freq: Pandas frequency string for the forecast index
            (e.g., "H" for hourly, "D" for daily).
        regressors: List of regressor column names.
        changepoint_prior_scale: Flexibility of the trend.
        seasonality_prior_scale: Strength of seasonality.
        holidays_prior_scale: Strength of holiday effects.
        seasonality_mode: "additive" or "multiplicative".
        yearly_seasonality: Enable yearly seasonality.
        weekly_seasonality: Enable weekly seasonality.
        daily_seasonality: Enable daily seasonality.
        hourly_seasonality: Enable hourly seasonality (custom).
        interval_width: Native uncertainty interval width (0-1).
        confidence_levels: Supported confidence levels for prediction.
    """

    # Horizon metadata
    horizon_label: str = "24h"
    horizon_hours: int = 24
    horizon_days: int = 1
    freq: str = "H"

    # Regressors
    regressors: List[str] = field(
        default_factory=lambda: list(PROPHET_REGRESSORS)
    )

    # Prophet hyperparameters
    changepoint_prior_scale: float = 0.05
    seasonality_prior_scale: float = 10.0
    holidays_prior_scale: float = 10.0
    seasonality_mode: str = "multiplicative"
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False
    hourly_seasonality: bool = False
    interval_width: float = 0.95

    # Confidence levels
    confidence_levels: List[float] = field(
        default_factory=lambda: [0.70, 0.85, 0.95]
    )

    # ============================================================
    # SERIALIZATION
    # ============================================================
    def to_dict(self) -> Dict[str, Any]:
        """Convert to a plain dictionary.

        Returns:
            Dictionary representation suitable for JSON serialization.
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to a JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def save(self, path: str) -> None:
        """Save the configuration to a JSON file.

        Args:
            path: File path to write the configuration to.
        """
        import os

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(self.to_json())
        logger.info(f"ProphetConfig saved to {path}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProphetConfig":
        """Build a config from a plain dictionary.

        Unknown keys are ignored, so configs saved by future versions
        with extra fields can still be loaded.

        Args:
            data: Dictionary of configuration values.

        Returns:
            ProphetConfig instance.
        """
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)

    @classmethod
    def load(cls, path: str) -> "ProphetConfig":
        """Load a configuration from a JSON file.

        Args:
            path: File path to read the configuration from.

        Returns:
            ProphetConfig instance.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    # ============================================================
    # PROPHET KWARGS
    # ============================================================
    def to_prophet_kwargs(self) -> Dict[str, Any]:
        """Return the exact kwargs to pass to Prophet().

        Extracts only the Prophet hyperparameters from this config,
        excluding horizon metadata and regressor lists.

        Returns:
            Dictionary of kwargs for Prophet(**kwargs).
        """
        return {
            "changepoint_prior_scale": self.changepoint_prior_scale,
            "seasonality_prior_scale": self.seasonality_prior_scale,
            "holidays_prior_scale": self.holidays_prior_scale,
            "seasonality_mode": self.seasonality_mode,
            "yearly_seasonality": self.yearly_seasonality,
            "weekly_seasonality": self.weekly_seasonality,
            "daily_seasonality": self.daily_seasonality,
            "interval_width": self.interval_width,
        }

    # ============================================================
    # VALIDATION
    # ============================================================
    def validate(self) -> None:
        """Validate the configuration.

        Raises:
            ValueError: If any field is invalid.
        """
        if self.horizon_hours <= 0:
            raise ValueError(
                f"horizon_hours must be positive, got {self.horizon_hours}"
            )

        if self.horizon_days <= 0:
            raise ValueError(
                f"horizon_days must be positive, got {self.horizon_days}"
            )

        if not 0.0 < self.interval_width < 1.0:
            raise ValueError(
                f"interval_width must be in (0, 1), got {self.interval_width}"
            )

        if self.seasonality_mode not in ("additive", "multiplicative"):
            raise ValueError(
                f"seasonality_mode must be 'additive' or 'multiplicative', "
                f"got '{self.seasonality_mode}'"
            )

        if not self.regressors:
            raise ValueError("regressors list cannot be empty")

        if not self.confidence_levels:
            raise ValueError("confidence_levels list cannot be empty")

        for level in self.confidence_levels:
            if not 0.0 < level < 1.0:
                raise ValueError(
                    f"confidence level must be in (0, 1), got {level}"
                )

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ProphetConfig("
            f"horizon='{self.horizon_label}', "
            f"freq='{self.freq}', "
            f"seasonality_mode='{self.seasonality_mode}', "
            f"regressors={len(self.regressors)})"
        )