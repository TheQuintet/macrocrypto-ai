"""Prophet model adapter.

This module provides ProphetModel, a concrete implementation of the
ForecastModel interface that wraps Facebook Prophet.

Design:
    - Uses the ForecastModel interface from app.ai.base
    - Supports 10 regressors (5 macro + 5 BTC features)
    - Uses multiplicative seasonality (better for crypto)
    - Provides confidence intervals at 70%, 85%, 95%
    - Serializes with Prophet's JSON format (not pickle)

Strategies:
    - "fresh": Train from scratch on the full dataset (M2.1)
    - "warm": Reload previous model parameters, still train on
      the full dataset (M2.2). Prophet doesn't support incremental
      training, so warm-start is a speed optimization only.

Branch M2.2 adds warm-start support on top of M2.1's fresh strategy.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from prophet import Prophet
from prophet.serialize import model_from_json, model_to_json

from app.ai.base import ForecastModel
from app.ai.metrics import current_prices_for_target_dates, directional_accuracy
from app.ai.models.feature_utils import missing_required_columns

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
REGRESSORS = [
# --- Exact Parquet Column Names ---
    "cpi",
    "federal_funds_rate",     # Replaces 'interest_rate'
    "m2_money_supply",        # Replaces 'm2_growth'
    "dxy",
    "ten_year_treasury",      # Replaces 'treasury_yield'
    "btc_volume",             # Replaces 'volume'
    "btc_volatility_7d",      # Replaces 'volatility'
    "btc_dominance",          # Replaces 'dominance'
    "active_addresses",
    "btc_log_return_7d",      # Replaces 'price_lag_7d'
    "btc_nasdaq_ratio",       # New addition
    "vix",                    # New addition
    "btc_sma_30",             # New addition
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

# Minimum rows required for training
MIN_TRAINING_ROWS = 30


# ============================================================
# PROPHET MODEL
# ============================================================
class ProphetModel(ForecastModel):
    """Prophet implementation of the ForecastModel interface.

    This adapter wraps Facebook Prophet and supports:
        - Training from scratch (fresh strategy)
        - Warm-start training (warm strategy)
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
        last_training_mode: The mode used in the last training
            ("fresh" or "warm").
    """

    def __init__(
        self,
        strategy: str = "fresh",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the Prophet model adapter.

        Args:
            strategy: Training strategy. "fresh" trains from scratch.
                "warm" reloads previous model parameters.
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
        self.regressors = REGRESSORS.copy()
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.model: Optional[Prophet] = None
        self.last_training_mode: str = "fresh"

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

        Supports two strategies:
            - fresh (warm_start=False): New Prophet instance
            - warm (warm_start=True): Uses previous model's parameters

        Important: Even with warm_start=True, Prophet trains on the
        FULL dataset. Prophet does not support incremental training
        on new data alone. The warm-start only speeds up convergence.

        Args:
            data: Training DataFrame with columns:
                'ds', 'y', and all 10 regressors.
            warm_start: If True, use warm-start strategy.
            previous_model_path: Path to previous model (for warm-start).
                Required when warm_start=True.

        Returns:
            Dictionary with metrics: mae, rmse, mape, directional_accuracy.

        Raises:
            ValueError: If data is empty or missing required columns.
        """
        self._validate_data(data)

        # Decide training mode
        init_params: Optional[Dict[str, Any]] = None

        if warm_start:
            init_params, _ = self._try_load_warm_start_params(
                previous_model_path
            )

        logger.info(
            "Training Prophet model (%s) on %s rows",
            "warm" if init_params is not None else "fresh",
            len(data),
        )

        self.model = self._create_prophet_model()
        self.regressors = [
            regressor for regressor in REGRESSORS if regressor in data.columns
        ]
        self._add_regressors(self.model, self.regressors)
        mode = "fresh"
        try:
            if init_params is None:
                self.model.fit(data)
            else:
                self.model.fit(data, init=init_params)
                mode = "warm"
        except Exception as e:
            if init_params is None:
                raise
            logger.warning(
                "Prophet warm-start fit failed (%s). Falling back to fresh "
                "training.",
                e,
            )
            self.model = self._create_prophet_model()
            self._add_regressors(self.model, self.regressors)
            self.model.fit(data)

        self.last_training_mode = mode

        # Calculate metrics
        self.metrics = self._calculate_metrics(data)
        self.is_trained = True

        logger.info(
            f"Prophet model trained ({mode}). "
            f"MAE={self.metrics['mae']:.4f}, "
            f"RMSE={self.metrics['rmse']:.4f}, "
            f"MAPE={self.metrics['mape']:.2f}%"
        )

        return self.metrics

    # ============================================================
    # WARM-START HELPERS
    # ============================================================
    def _try_load_warm_start_params(
        self,
        previous_model_path: Optional[str],
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Attempt to load warm-start parameters from a previous model.

        Falls back to fresh training if any step fails:
            - No path provided
            - File not found
            - Parameter extraction fails
            - Any other error

        Args:
            previous_model_path: Path to the previous model file.

        Returns:
            Tuple of (init_params, mode):
                - init_params: Parameters for warm-start, or None
                - mode: "warm" if successful, "fresh" if fallback
        """
        # No path provided → fall back to fresh
        if not previous_model_path:
            logger.warning(
                "Warm-start requested but no previous_model_path "
                "provided. Falling back to fresh training."
            )
            return None, "fresh"

        # File doesn't exist → fall back to fresh
        if not os.path.exists(previous_model_path):
            logger.warning(
                f"Previous model not found at '{previous_model_path}'. "
                f"Falling back to fresh training."
            )
            return None, "fresh"

        # Try to extract params from previous model
        try:
            with open(previous_model_path, "r") as f:
                previous_model = model_from_json(f.read())

            init_params = self._extract_init_params(previous_model)

            if init_params is None:
                logger.warning(
                    "Could not extract init parameters from previous "
                    "model. Falling back to fresh training."
                )
                return None, "fresh"

            logger.info(
                f"Warm-start parameters loaded from '{previous_model_path}'"
            )
            return init_params, "warm"

        except Exception as e:
            logger.warning(
                f"Failed to load warm-start parameters from "
                f"'{previous_model_path}': {e}. "
                f"Falling back to fresh training."
            )
            return None, "fresh"

    def _extract_init_params(
        self,
        previous_model: Prophet,
    ) -> Optional[Dict[str, Any]]:
        """Extract initialization parameters from a trained Prophet model.

        Prophet expects Stan parameter initial values when fitting, not
        changepoint dates or constructor configuration. Parameter arrays
        are reduced across posterior samples so the resulting values can
        initialize another fit with compatible regressors and changepoints.

        Args:
            previous_model: A trained Prophet instance.

        Returns:
            Dictionary of init parameters, or None if extraction fails.
        """
        try:
            parameter_names = ("k", "m", "sigma_obs", "delta", "beta")
            params = getattr(previous_model, "params", {})
            if not all(name in params for name in parameter_names):
                logger.warning(
                    "Previous Prophet model is missing Stan parameters "
                    "required for warm-start"
                )
                return None

            init: Dict[str, Any] = {}
            for name in parameter_names:
                values = np.asarray(params[name], dtype=float)
                if values.ndim > 0:
                    values = np.mean(values, axis=0)
                if not np.isfinite(values).all():
                    logger.warning(
                        "Previous Prophet parameter '%s' contains "
                        "non-finite values",
                        name,
                    )
                    return None
                init[name] = (
                    float(values)
                    if values.ndim == 0
                    else values
                )

            logger.debug(
                f"Extracted warm-start params: {list(init.keys())}"
            )
            return init

        except Exception as e:
            logger.warning(f"Failed to extract init params: {e}")
            return None

    def _create_prophet_model(self) -> Prophet:
        """Create a new Prophet instance configured for this adapter."""
        return Prophet(**self.config)

    @staticmethod
    def _add_regressors(
        model: Prophet,
        regressors: List[str],
    ) -> None:
        for regressor in regressors:
            model.add_regressor(regressor)

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

        missing = missing_required_columns(data, REQUIRED_COLUMNS)
        if missing:
            raise ValueError(
                f"Training data is missing required columns: {missing}"
            )

        if len(data) < MIN_TRAINING_ROWS:
            raise ValueError(
                f"Training data must have at least {MIN_TRAINING_ROWS} "
                f"rows, got {len(data)}"
            )

    def _validate_future_data(self, future_data: pd.DataFrame) -> None:
        """Validate future data.

        Raises:
            ValueError: If future_data is invalid.
        """
        if future_data is None or future_data.empty:
            raise ValueError("Future data cannot be empty")

        regressors = (
            list(self.model.extra_regressors)
            if self.model is not None
            else self.regressors
        )
        required = ["ds"] + regressors
        missing = missing_required_columns(future_data, required)
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
        current_price = current_prices_for_target_dates(
            data, data["ds"], strict=False
        )

        # MAE
        mae = float(np.mean(np.abs(predicted - actual)))

        # RMSE
        rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))

        # MAPE (avoid division by zero)
        with np.errstate(divide="ignore", invalid="ignore"):
            mape_values = np.abs((predicted - actual) / actual) * 100
            mape_values = mape_values[np.isfinite(mape_values)]
            mape = float(np.mean(mape_values)) if len(mape_values) > 0 else 0.0

        direction_score = directional_accuracy(
            actual, predicted, current_price
        )

        return {
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "directional_accuracy": direction_score,
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
            f"trained={self.is_trained}, "
            f"last_mode='{self.last_training_mode}')"
        )