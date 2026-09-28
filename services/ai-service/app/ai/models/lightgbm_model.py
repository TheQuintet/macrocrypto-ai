"""LightGBM model adapter.

This module provides LightGBMModel, a concrete implementation of the
ForecastModel interface that wraps LightGBM.

Design:
    - Uses the ForecastModel interface from app.ai.base
    - Supports 10 base features (5 macro + 5 BTC)
    - Engineers lag features for time series (LightGBM needs them)
    - Approximates confidence intervals from residual std
    - Serializes with LightGBM's native text format

Naming Convention:
    - Base features come from the data pipeline (e.g., "price_lag_7d")
    - Engineered features are prefixed with "eng_" to avoid collisions
      (e.g., "eng_price_lag_7d", "eng_returns_7d")

Strategies:
    - "fresh": Train from scratch on the full dataset (M4.1)
    - "incremental": Continue training on new data only (M4.2)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import lightgbm as lgb
import numpy as np
import pandas as pd

from app.ai.base import ForecastModel
from app.ai.metrics import current_prices_for_target_dates, directional_accuracy
from app.ai.models.feature_utils import (
    drop_rows_with_unhandled_missing_features,
    missing_required_columns,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
BASE_FEATURES = [
# --- Raw Market & On-Chain ---
    "btc_price",
    "btc_volume",
    "btc_dominance",
    "active_addresses",
    
    # --- Macroeconomic & External Assets ---
    "gold_spot",
    "dxy",
    "ten_year_treasury",
    "vix",
    "high_yield_spread",
    "nasdaq_composite",
    "equity_corr",
    "high_yield_credit_stress_proxy",
    "cpi",
    "federal_funds_rate",
    "gdp",
    "m2_money_supply",
    "unemployment",
    
    # --- Technical Indicators & Ratios ---
    "btc_log_return_1d",
    "btc_log_return_7d",
    "btc_log_return_30d",
    "btc_sma_7",
    "btc_sma_30",
    "btc_sma_90",
    "btc_volatility_7d",
    "btc_volatility_30d",
    "btc_gold_ratio",
    "btc_nasdaq_ratio",
    
    # --- Metadata & Data Quality Flags ---
    "high_yield_spread_is_missing",
    "active_addresses_is_imputed",
    "unemployment_is_imputed",
    "warmup_complete",
    
    # --- Observation Lag / Recency Trackers ---
    "btc_dominance_days_since_last_observation",
    "gold_spot_days_since_last_observation",
    "dxy_days_since_last_observation",
    "ten_year_treasury_days_since_last_observation",
    "vix_days_since_last_observation",
    "nasdaq_composite_days_since_last_observation",
    "equity_corr_days_since_last_observation",
    "high_yield_credit_stress_proxy_days_since_last_observation",
    "active_addresses_days_since_last_observation",
    "cpi_days_since_release",
    "federal_funds_rate_days_since_release",
    "gdp_days_since_release",
    "m2_money_supply_days_since_release",
    "unemployment_days_since_release",
]

LAG_DAYS = [1, 7, 30]

# Engineered features are prefixed with "eng_" to avoid collision
# with the base feature "price_lag_7d"
LAG_FEATURES = [f"eng_price_lag_{d}d" for d in LAG_DAYS]
RETURN_FEATURES = [f"eng_returns_{d}d" for d in LAG_DAYS]
ENGINEERED_FEATURES = LAG_FEATURES + RETURN_FEATURES

ALL_FEATURES = BASE_FEATURES + ENGINEERED_FEATURES

REQUIRED_COLUMNS = ["ds", "y"] + BASE_FEATURES

DEFAULT_CONFIG = {
    "n_estimators": 100,
    "max_depth": 6,
    "learning_rate": 0.1,
    "objective": "regression",
    "verbose": -1,
    "random_state": 42,
}

CONFIDENCE_LEVELS = [0.70, 0.85, 0.95]

# Z-scores for confidence interval approximation
Z_SCORES = {
    0.70: 1.04,
    0.85: 1.44,
    0.95: 1.96,
}

# Minimum rows needed for training (must account for max lag)
MIN_TRAINING_ROWS = max(LAG_DAYS) + 30

# Minimum new rows needed for incremental training
MIN_INCREMENTAL_ROWS = 1


# ============================================================
# LIGHTGBM MODEL
# ============================================================
class LightGBMModel(ForecastModel):
    """LightGBM implementation of the ForecastModel interface.

    This adapter wraps LightGBM and supports:
        - Training from scratch (fresh strategy)
        - Incremental training on new data (incremental strategy)
        - Feature engineering (lag features for time series)
        - Prediction with confidence intervals (approximated)
        - Metrics calculation (MAE, RMSE, MAPE, directional accuracy)
        - Serialization via LightGBM's native text format

    Attributes:
        model: The underlying LGBMRegressor instance.
        strategy: Training strategy ("fresh" or "incremental").
        config: LightGBM configuration dictionary.
        version: Model version string.
        metrics: Last calculated metrics.
        is_trained: Whether the model has been trained.
        last_training_mode: The mode used in the last training
            ("fresh" or "incremental").
        feature_columns: List of feature column names used in training.
        residual_std: Standard deviation of training residuals
            (used for confidence interval approximation).
        last_training_timestamp: Timestamp of the last training data
            point (used to filter new data during incremental training).
    """

    def __init__(
        self,
        strategy: str = "fresh",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the LightGBM model adapter.

        Args:
            strategy: Training strategy. "fresh" trains from scratch.
                "incremental" continues from a previous model.
            config: Optional LightGBM configuration overrides.

        Raises:
            ValueError: If strategy is not "fresh" or "incremental".
        """
        super().__init__()

        if strategy not in ("fresh", "incremental"):
            raise ValueError(
                f"Invalid strategy '{strategy}'. "
                f"Must be 'fresh' or 'incremental'."
            )

        self.strategy = strategy
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.model: Optional[lgb.LGBMRegressor] = None
        self.last_training_mode: str = "fresh"
        self.feature_columns: List[str] = []
        self.residual_std: float = 0.0

        # NEW in M4.2: Track last training timestamp
        self.last_training_timestamp: Optional[datetime] = None

        logger.info(
            f"LightGBMModel initialized (strategy={strategy})"
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
        """Train the LightGBM model.

        Supports two strategies:
            - fresh (warm_start=False): Train from scratch on full data
            - incremental (warm_start=True): Continue training on new data

        For incremental training:
            1. Load previous model from disk
            2. Filter data to only rows after last_training_timestamp
            3. Continue training with `init_model` parameter
            4. Fall back to fresh if anything fails

        Args:
            data: Training DataFrame with columns:
                'ds', 'y', and all 10 base features.
            warm_start: If True, use incremental training.
            previous_model_path: Path to previous model file.
                Required when warm_start=True.

        Returns:
            Dictionary with metrics: mae, rmse, mape, directional_accuracy.

        Raises:
            ValueError: If data is empty or missing required columns.
        """
        self._validate_data(data)

        # Decide training mode
        if warm_start:
            mode = self._try_incremental_train(data, previous_model_path)
        else:
            mode = "fresh"
            self._fresh_train(data)

        # Update timestamp
        self.last_training_timestamp = self._extract_max_timestamp(data)

        logger.info(
            f"LightGBM model trained ({mode}) on {len(data)} rows. "
            f"MAE={self.metrics['mae']:.4f}, "
            f"RMSE={self.metrics['rmse']:.4f}, "
            f"MAPE={self.metrics['mape']:.2f}%"
        )

        return self.metrics

    def _fresh_train(self, data: pd.DataFrame) -> None:
        """Train from scratch on the full dataset.

        Args:
            data: Full training data.
        """
        prepared = self._prepare_features(data)
        X = prepared[self.feature_columns]
        y = prepared["y"]

        logger.info(
            f"Training LightGBM model (fresh) on {len(prepared)} rows, "
            f"{len(self.feature_columns)} features"
        )

        # Initialize fresh LightGBM model
        self.model = lgb.LGBMRegressor(**self.config)
        self.model.fit(X, y)

        # Calculate residual std for confidence intervals
        predictions = self.model.predict(X)
        residuals = y.values - predictions
        self.residual_std = float(np.std(residuals))

        # Calculate metrics
        self.metrics = self._calculate_metrics_from_arrays(
            y.values,
            predictions,
            current_prices_for_target_dates(data, prepared["ds"]),
        )
        self.is_trained = True
        self.last_training_mode = "fresh"

    def _try_incremental_train(
        self,
        data: pd.DataFrame,
        previous_model_path: Optional[str],
    ) -> str:
        """Attempt incremental training. Falls back to fresh if anything fails.

        Args:
            data: Full training data.
            previous_model_path: Path to previous model.

        Returns:
            The mode used ("fresh" or "incremental").
        """
        # No path provided → fall back to fresh
        if not previous_model_path:
            logger.warning(
                "Incremental training requested but no previous_model_path "
                "provided. Falling back to fresh training."
            )
            self._fresh_train(data)
            return "fresh"

        # File doesn't exist → fall back to fresh
        if not os.path.exists(previous_model_path):
            logger.warning(
                f"Previous model not found at '{previous_model_path}'. "
                f"Falling back to fresh training."
            )
            self._fresh_train(data)
            return "fresh"

        # Try to load previous model and incremental train
        try:
            self._load_previous_model(previous_model_path)
            return self._incremental_train(data)
        except Exception as e:
            logger.warning(
                f"Incremental training failed: {e}. "
                f"Falling back to fresh training."
            )
            self._fresh_train(data)
            return "fresh"

    def _load_previous_model(self, path: str) -> None:
        """Load a previous model from disk.

        Args:
            path: Path to the previous model file.
        """
        booster = lgb.Booster(model_file=path)

        # Wrap in sklearn-compatible interface
        self.model = lgb.LGBMRegressor(**self.config)
        self.model._Booster = booster
        self.model._n_features = booster.num_feature()
        self.model.fitted_ = True

        # Load metadata if available
        metadata_path = f"{path}.meta.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            self.feature_columns = metadata.get("feature_columns", [])
            self.residual_std = metadata.get("residual_std", 0.0)
            self.metrics = metadata.get("metrics", {})
            self.version = metadata.get("version", self.version)
            self.last_training_mode = metadata.get(
                "last_training_mode", "fresh"
            )

            # Load last training timestamp if available
            timestamp_str = metadata.get("last_training_timestamp")
            if timestamp_str:
                try:
                    self.last_training_timestamp = datetime.fromisoformat(
                        timestamp_str
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse timestamp: {e}")

        logger.info(f"Loaded previous LightGBM model from '{path}'")

    def _incremental_train(self, data: pd.DataFrame) -> str:
        """Train incrementally on new data only.

        Args:
            data: Full training data (will be filtered to new rows).

        Returns:
            The mode used ("incremental" or "fresh" if no new data).
        """
        # Prepare features on full data (to compute lag features)
        prepared = self._prepare_features(
            data, update_feature_columns=False
        )

        # Filter to new data only
        new_data = self._filter_new_data(prepared)

        if len(new_data) < MIN_INCREMENTAL_ROWS:
            logger.warning(
                f"No new data since last training "
                f"({self.last_training_timestamp}). "
                f"Keeping previous model unchanged."
            )
            # Mark as trained and keep existing metrics
            self.is_trained = True
            self.last_training_mode = "incremental"
            return "incremental"

        X_new = new_data[self.feature_columns]
        y_new = new_data["y"]

        logger.info(
            f"Training LightGBM model (incremental) on {len(X_new)} new rows"
        )

        # Continue training from previous model using init_model
        self.model.fit(X_new, y_new, init_model=self.model.booster_)

        # Recalculate metrics on the full prepared dataset
        X_full = prepared[self.feature_columns]
        y_full = prepared["y"]
        predictions = self.model.predict(X_full)
        residuals = y_full.values - predictions
        self.residual_std = float(np.std(residuals))
        self.metrics = self._calculate_metrics_from_arrays(
            y_full.values,
            predictions,
            current_prices_for_target_dates(data, prepared["ds"]),
        )

        self.is_trained = True
        self.last_training_mode = "incremental"

        return "incremental"

    def _filter_new_data(self, prepared: pd.DataFrame) -> pd.DataFrame:
        """Filter prepared data to only rows after last training timestamp.

        Args:
            prepared: Prepared DataFrame with features.

        Returns:
            Filtered DataFrame with only new rows.
        """
        if self.last_training_timestamp is None:
            return prepared

        # Convert 'ds' column to datetime if needed
        prepared = prepared.copy()
        prepared["ds"] = pd.to_datetime(prepared["ds"])

        last_ts = pd.Timestamp(self.last_training_timestamp)

        filtered = prepared[prepared["ds"] > last_ts].reset_index(drop=True)

        logger.debug(
            f"Filtered {len(prepared)} rows to {len(filtered)} new rows "
            f"(after {last_ts})"
        )

        return filtered

    def _extract_max_timestamp(self, data: pd.DataFrame) -> Optional[datetime]:
        """Extract the maximum timestamp from the data.

        Args:
            data: DataFrame with 'ds' column.

        Returns:
            Max timestamp, or None if 'ds' is missing.
        """
        if "ds" not in data.columns or data.empty:
            return None

        try:
            max_ts = pd.to_datetime(data["ds"]).max()
            return max_ts.to_pydatetime()
        except Exception as e:
            logger.warning(f"Failed to extract max timestamp: {e}")
            return None

    # ============================================================
    # FEATURE ENGINEERING
    # ============================================================
    def _prepare_features(
        self,
        data: pd.DataFrame,
        update_feature_columns: bool = True,
    ) -> pd.DataFrame:
        """Prepare features for LightGBM training or prediction.

        Adds lag features and return features to the base data.

        Engineered features are prefixed with "eng_" to avoid
        colliding with the base feature "price_lag_7d" that comes
        from the data pipeline.

        Args:
            data: DataFrame with 'ds', 'y', and base features.
            update_feature_columns: If True, updates self.feature_columns.

        Returns:
            DataFrame with all engineered features.
        """
        df = data.copy()
        df = df.sort_values("ds").reset_index(drop=True)

        # Create engineered lag features (only if 'y' is present)
        if "y" in df.columns:
            for lag in LAG_DAYS:
                df[f"eng_price_lag_{lag}d"] = df["y"].shift(lag)
                df[f"eng_returns_{lag}d"] = df["y"].pct_change(lag)

        # Update feature columns on first call
        if update_feature_columns:
            self.feature_columns = [
                column for column in BASE_FEATURES if column in df.columns
            ] + ENGINEERED_FEATURES

        df = drop_rows_with_unhandled_missing_features(
            df,
            self.feature_columns,
            missing_feature="high_yield_spread",
            missing_indicator="high_yield_spread_is_missing",
        )

        return df

    # ============================================================
    # PREDICTION
    # ============================================================
    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions with confidence intervals.

        LightGBM does not provide native confidence intervals. We
        approximate them using the residual standard deviation
        from training:
            - 95%: yhat ± 1.96 * residual_std
            - 85%: yhat ± 1.44 * residual_std
            - 70%: yhat ± 1.04 * residual_std

        Args:
            future_data: DataFrame with 'ds', base features, and
                (optionally) 'y' for lagging.

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

        # Prepare features for prediction
        prepared = self._prepare_features(
            future_data, update_feature_columns=False
        )

        if prepared.empty:
            raise ValueError(
                "No valid rows for prediction after feature engineering."
            )

        X = prepared[self.feature_columns]
        predictions = self.model.predict(X)

        # Build output DataFrame with 95% confidence intervals
        result = pd.DataFrame(
            {
                "ds": prepared["ds"].values,
                "yhat": predictions,
                "yhat_lower": predictions - self.residual_std * Z_SCORES[0.95],
                "yhat_upper": predictions + self.residual_std * Z_SCORES[0.95],
            }
        )

        return result

    def predict_with_confidence(
        self,
        future_data: pd.DataFrame,
        confidence_level: float = 0.95,
    ) -> pd.DataFrame:
        """Generate predictions with a specific confidence level.

        LightGBM's confidence intervals are approximated using
        residual std and z-scores:
            - 95%: z = 1.96
            - 85%: z = 1.44
            - 70%: z = 1.04

        Args:
            future_data: DataFrame with 'ds' and base features.
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

        # Get 95% predictions
        forecast = self.predict(future_data)

        if confidence_level == 0.95:
            return forecast

        # Rebuild bounds with the requested z-score
        z = Z_SCORES[confidence_level]
        yhat = forecast["yhat"]
        margin = self.residual_std * z

        return pd.DataFrame(
            {
                "ds": forecast["ds"],
                "yhat": yhat,
                "yhat_lower": yhat - margin,
                "yhat_upper": yhat + margin,
            }
        )

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
        return "lightgbm"

    def get_version(self) -> str:
        """Return the model version."""
        return self.version

    # ============================================================
    # SERIALIZATION
    # ============================================================
    def save(self, path: str) -> None:
        """Save the trained model to disk using LightGBM's native format.

        LightGBM uses a text-based model format. We also save a
        metadata JSON file alongside the model that contains:
            - feature_columns: for consistency between train/predict
            - residual_std: for confidence interval approximation
            - metrics: for reference
            - version: for tracking
            - strategy: for tracking
            - last_training_mode: for incremental tracking
            - last_training_timestamp: for incremental filtering

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

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        # Save LightGBM model using native format
        self.model.booster_.save_model(path)

        # Save metadata (feature columns + residual_std + metrics)
        metadata = {
            "feature_columns": self.feature_columns,
            "residual_std": self.residual_std,
            "metrics": self.metrics,
            "version": self.version,
            "strategy": self.strategy,
            "last_training_mode": self.last_training_mode,
            "last_training_timestamp": (
                self.last_training_timestamp.isoformat()
                if self.last_training_timestamp
                else None
            ),
        }
        metadata_path = f"{path}.meta.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        logger.info(f"LightGBM model saved to {path}")

    def load(self, path: str) -> None:
        """Load a trained model from disk.

        Loads both the LightGBM model file and its associated
        metadata JSON file (if present).

        Args:
            path: File path to load the model from.

        Raises:
            FileNotFoundError: If path or metadata file doesn't exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")

        # Load LightGBM model from native format
        booster = lgb.Booster(model_file=path)

        # Wrap in sklearn-compatible interface
        self.model = lgb.LGBMRegressor(**self.config)
        self.model._Booster = booster
        self.model._n_features = booster.num_feature()
        self.model.fitted_ = True

        # Load metadata
        metadata_path = f"{path}.meta.json"
        if os.path.exists(metadata_path):
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            self.feature_columns = metadata.get("feature_columns", [])
            self.residual_std = metadata.get("residual_std", 0.0)
            self.metrics = metadata.get("metrics", {})
            self.version = metadata.get("version", self.version)
            self.strategy = metadata.get("strategy", self.strategy)
            self.last_training_mode = metadata.get(
                "last_training_mode", "fresh"
            )

            # Load last training timestamp if present
            timestamp_str = metadata.get("last_training_timestamp")
            if timestamp_str:
                try:
                    self.last_training_timestamp = datetime.fromisoformat(
                        timestamp_str
                    )
                except Exception as e:
                    logger.warning(f"Failed to parse timestamp: {e}")

        self.is_trained = True
        logger.info(f"LightGBM model loaded from {path}")

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

    # ============================================================
    # METRICS CALCULATION
    # ============================================================
    def _calculate_metrics_from_arrays(
        self,
        actual: np.ndarray,
        predicted: np.ndarray,
        current_price: np.ndarray,
    ) -> Dict[str, float]:
        """Calculate performance metrics from arrays.

        Computes:
            - MAE: Mean Absolute Error
            - RMSE: Root Mean Square Error
            - MAPE: Mean Absolute Percentage Error, in percentage points
            - directional_accuracy: Correct next-day movement direction (%)

        Args:
            actual: Actual values.
            predicted: Predicted values.

        Returns:
            Dictionary with mae, rmse, mape, directional_accuracy.
        """
        mae = float(np.mean(np.abs(predicted - actual)))
        rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))

        with np.errstate(divide="ignore", invalid="ignore"):
            mape_values = np.abs((predicted - actual) / actual) * 100
            mape_values = mape_values[np.isfinite(mape_values)]
            mape = float(np.mean(mape_values)) if len(mape_values) > 0 else 0.0

        directional = directional_accuracy(actual, predicted, current_price)

        return {
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "directional_accuracy": directional,
        }

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"LightGBMModel("
            f"strategy='{self.strategy}', "
            f"version='{self.version}', "
            f"trained={self.is_trained}, "
            f"last_mode='{self.last_training_mode}')"
        )