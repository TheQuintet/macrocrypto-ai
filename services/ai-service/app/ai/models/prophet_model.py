"""Prophet model adapter.

This module provides ProphetModel, a concrete implementation of the
ForecastModel interface that wraps Facebook Prophet.

Design:
    - Uses the ForecastModel interface from app.ai.base
    - Supports 10 regressors (5 macro + 5 BTC features)
    - Uses multiplicative seasonality (better for crypto)
    - Provides confidence intervals at 70%, 85%, 95%
    - Serializes with Prophet's JSON format (not pickle)

Branch M2.1 implements only the "fresh" strategy (train from scratch).
Branch M2.2 will add the "warm-start" strategy.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from prophet import Prophet
from prophet.serialize import model_from_json, model_to_json

from app.ai.base import ForecastModel

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
REGRESSORS = [
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

REQUIRED_COLUMNS = ["ds", "y"] + REGRESSORS

DEFAULT_CONFIG = {
    "changepoint_prior_scale": 0.05,
    "seasonality_prior_scale": 10.0,
    "holidays_prior_scale": 10.0,
    "seasonality_mode": "multiplicative",
    "yearly_seasonality": True,
    "weekly_seasonality": True,
    "daily_seasonality": False,
    "interval_width": 0.95,
}

CONFIDENCE_LEVELS = [0.70, 0.85, 0.95]


# ============================================================
# PROPHET MODEL
# ============================================================
class ProphetModel(ForecastModel):
    """Prophet implementation of the ForecastModel interface.

    This adapter wraps Facebook Prophet and supports:
        - Training from scratch (fresh strategy)
        - Prediction with confidence intervals
        - Metrics calculation (MAE, RMSE, MAPE, directional accuracy)
        - Serialization via Prophet's JSON format

    Attributes:
        model: The underlying Prophet instance.
        strategy: Training strategy ("fresh" or "warm").
        config: Prophet configuration dictionary.
        version: Model version string.
        metrics: Last calculated metrics.
        is_trained: Whether the model has been trained.
    """

    def __init__(
        self,
        strategy: str = "fresh",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the Prophet model adapter.

        Args:
            strategy: Training strategy. Currently only "fresh" is
                implemented. "warm" will be added in M2.2.
            config: Optional Prophet configuration overrides.

        Raises:
            ValueError: If strategy is not "fresh" or "warm".
        """
        super().__init__()

        if strategy not in ("fresh", "warm"):
            raise ValueError(
                f"Invalid strategy '{strategy}'. "
                f"Must be 'fresh' or 'warm'."
            )

        self.strategy = strategy
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.model: Optional[Prophet] = None

        logger.info(
            f"ProphetModel initialized (strategy={strategy})"
        )

    # ============================================================
    # TRAINING
    # ============================================================
    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        """Train the Prophet model.

        In Branch M2.1, this only implements the "fresh" strategy.
        Warm-start is implemented in M2.2.

        Args:
            data: Training DataFrame with columns:
                'ds', 'y', and all 10 regressors.
            warm_start: If True, attempts warm-start training.
                In M2.1, this falls back to fresh training.
            previous_model_path: Path to previous model (for warm-start).
                Currently unused in M2.1.

        Returns:
            Dictionary with metrics: mae, rmse, mape, directional_accuracy.

        Raises:
            ValueError: If data is empty or missing required columns.
        """
        self._validate_data(data)

        if warm_start:
            logger.warning(
                "Warm-start requested but not implemented in M2.1. "
                "Falling back to fresh training."
            )

        logger.info(
            f"Training Prophet model (fresh) on {len(data)} rows"
        )

        # Initialize fresh Prophet model
        self.model = Prophet(**self.config)

        # Add all regressors
        for regressor in REGRESSORS:
            self.model.add_regressor(regressor)

        # Fit model
        self.model.fit(data)

        # Calculate metrics
        self.metrics = self._calculate_metrics(data)
        self.is_trained = True

        logger.info(
            f"Prophet model trained. "
            f"MAE={self.metrics['mae']:.4f}, "
            f"RMSE={self.metrics['rmse']:.4f}, "
            f"MAPE={self.metrics['mape']:.2f}%"
        )

        return self.metrics

    # ============================================================
    # PREDICTION
    # ============================================================
    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions with confidence intervals.

        Args:
            future_data: DataFrame with columns 'ds' and all 10 regressors.

        Returns:
            DataFrame with columns: ds, yhat, yhat_lower, yhat_upper.

        Raises:
            RuntimeError: If model is not trained.
            ValueError: If future_data is missing required columns.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError(
                "Cannot predict: model is not trained. "
                "Call train() first."
            )

        self._validate_future_data(future_data)

        # Make prediction
        forecast = self.model.predict(future_data)

        # Extract required columns
        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()

        return result

    def predict_with_confidence(
        self,
        future_data: pd.DataFrame,
        confidence_level: float = 0.95,
    ) -> pd.DataFrame:
        """Generate predictions with a specific confidence level.

        Prophet provides native 95% intervals. For 70% and 85%, we
        scale the margin around yhat proportionally.

        Args:
            future_data: DataFrame with columns 'ds' and 10 regressors.
            confidence_level: One of 0.70, 0.85, 0.95.

        Returns:
            DataFrame with columns: ds, yhat, yhat_lower, yhat_upper
            at the requested confidence level.

        Raises:
            ValueError: If confidence_level is not 0.70, 0.85, or 0.95.
        """
        if confidence_level not in CONFIDENCE_LEVELS:
            raise ValueError(
                f"Invalid confidence_level {confidence_level}. "
                f"Must be one of {CONFIDENCE_LEVELS}."
            )

        forecast = self.predict(future_data)

        if confidence_level == 0.95:
            return forecast

        # Scale margin for 70% and 85%
        scale_map = {0.70: 0.50, 0.85: 0.75}
        scale = scale_map[confidence_level]

        scaled = forecast.copy()
        margin_lower = forecast["yhat"] - forecast["yhat_lower"]
        margin_upper = forecast["yhat_upper"] - forecast["yhat"]

        scaled["yhat_lower"] = forecast["yhat"] - margin_lower * scale
        scaled["yhat_upper"] = forecast["yhat"] + margin_upper * scale

        return scaled

    # ============================================================
    # METRICS
    # ============================================================
    def get_metrics(self) -> Dict[str, float]:
        """Return the current metrics.

        Returns:
            Dictionary with mae, rmse, mape, directional_accuracy.
            Empty dict if not trained yet.
        """
        return self.metrics.copy()

    # ============================================================
    # METADATA
    # ============================================================
    def get_name(self) -> str:
        """Return the model name."""
        return "prophet"

    def get_version(self) -> str:
        """Return the model version."""
        return self.version

    # ============================================================
    # SERIALIZATION
    # ============================================================
    def save(self, path: str) -> None:
        """Save the trained model to disk using Prophet's JSON format.

        Prophet's Stan backend does not pickle well, so we use
        Prophet's native `model_to_json` / `model_from_json`.

        Args:
            path: File path to save the model.

        Raises:
            RuntimeError: If model is not trained.
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError(
                "Cannot save: model is not trained. "
                "Call train() first."
            )

        # Ensure directory exists
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        # Save model as JSON
        with open(path, "w") as f:
            f.write(model_to_json(self.model))

        logger.info(f"Prophet model saved to {path}")

    def load(self, path: str) -> None:
        """Load a trained model from disk.

        Args:
            path: File path to load the model from.

        Raises:
            FileNotFoundError: If path does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")

        with open(path, "r") as f:
            self.model = model_from_json(f.read())

        self.is_trained = True
        logger.info(f"Prophet model loaded from {path}")

    # ============================================================
    # VALIDATION
    # ============================================================
    def _validate_data(self, data: pd.DataFrame) -> None:
        """Validate training data.

        Raises:
            ValueError: If data is invalid.
        """
        if data is None or data.empty:
            raise ValueError("Training data cannot be empty")

        missing = [col for col in REQUIRED_COLUMNS if col not in data.columns]
        if missing:
            raise ValueError(
                f"Training data is missing required columns: {missing}"
            )

        if len(data) < 30:
            raise ValueError(
                f"Training data must have at least 30 rows, "
                f"got {len(data)}"
            )

    def _validate_future_data(self, future_data: pd.DataFrame) -> None:
        """Validate future data.

        Raises:
            ValueError: If future_data is invalid.
        """
        if future_data is None or future_data.empty:
            raise ValueError("Future data cannot be empty")

        required = ["ds"] + REGRESSORS
        missing = [col for col in required if col not in future_data.columns]
        if missing:
            raise ValueError(
                f"Future data is missing required columns: {missing}"
            )

    # ============================================================
    # METRICS CALCULATION
    # ============================================================
    def _calculate_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance metrics.

        Uses the training data to compute in-sample metrics:
            - MAE: Mean Absolute Error
            - RMSE: Root Mean Square Error
            - MAPE: Mean Absolute Percentage Error
            - directional_accuracy: % of correct direction predictions

        Args:
            data: Training data with columns 'ds' and 'y'.

        Returns:
            Dictionary of metrics.
        """
        # Get in-sample predictions
        forecast = self.model.predict(data)
        predicted = forecast["yhat"].values
        actual = data["y"].values

        # MAE
        mae = float(np.mean(np.abs(predicted - actual)))

        # RMSE
        rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))

        # MAPE (avoid division by zero)
        with np.errstate(divide="ignore", invalid="ignore"):
            mape_values = np.abs((predicted - actual) / actual) * 100
            mape_values = mape_values[np.isfinite(mape_values)]
            mape = float(np.mean(mape_values)) if len(mape_values) > 0 else 0.0

        # Directional accuracy
        actual_diff = np.diff(actual)
        predicted_diff = np.diff(predicted)
        if len(actual_diff) > 0:
            correct_directions = np.sum(
                np.sign(actual_diff) == np.sign(predicted_diff)
            )
            directional_accuracy = float(
                correct_directions / len(actual_diff) * 100
            )
        else:
            directional_accuracy = 0.0

        return {
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "directional_accuracy": directional_accuracy,
        }

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ProphetModel("
            f"strategy='{self.strategy}', "
            f"version='{self.version}', "
            f"trained={self.is_trained})"
        )