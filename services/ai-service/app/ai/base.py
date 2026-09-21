"""Abstract base class for all forecasting models.

This module defines the contract that every forecasting model
(Prophet, XGBoost, LightGBM) must implement.

The interface ensures:
    - Consistent API across all models
    - Easy addition of new models
    - Decoupled retraining orchestrator
    - Testability
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import pandas as pd


class ForecastModel(ABC):
    """Abstract base class for all forecasting models.

    Every forecasting model must implement this interface to be used
    by the retraining orchestrator and comparison engine.

    The interface covers:
        - Training (fresh or warm-start)
        - Prediction
        - Metrics retrieval
        - Model metadata (name, version)
        - Serialization (save/load)

    Attributes:
        version: Model version string (e.g., "1.0.0").
        metrics: Dictionary of performance metrics.
        is_trained: Whether the model has been trained.
    """

    def __init__(self) -> None:
        """Initialize the forecast model."""
        self.version: str = "1.0.0"
        self.metrics: Dict[str, float] = {}
        self.is_trained: bool = False

    # ============================================================
    # TRAINING
    # ============================================================
    @abstractmethod
    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        """Train the model on historical data.

        Args:
            data: DataFrame with columns:
                - 'ds' (datetime): timestamps
                - 'y' (float): target values (BTC price)
                - regressor columns: 10 features (CPI, rates, etc.)

            warm_start: If True, uses the previous model to initialize
                training. Only used by models that support warm-start
                (Prophet warm-start, XGBoost/LightGBM incremental).

            previous_model_path: Path to a previously saved model.
                Required when warm_start=True.

        Returns:
            Dictionary of performance metrics (e.g., MAE, RMSE, MAPE).

        Raises:
            ValueError: If data is empty or missing required columns.
            FileNotFoundError: If warm_start=True and previous_model_path
                does not exist.
        """
        pass

    # ============================================================
    # PREDICTION
    # ============================================================
    @abstractmethod
    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        """Generate predictions for future data.

        Args:
            future_data: DataFrame with columns:
                - 'ds' (datetime): future timestamps
                - regressor columns: forward-filled feature values

        Returns:
            DataFrame with columns:
                - 'ds' (datetime): timestamps
                - 'yhat' (float): predicted values
                - 'yhat_lower' (float): lower confidence bound
                - 'yhat_upper' (float): upper confidence bound

        Raises:
            RuntimeError: If the model has not been trained.
        """
        pass

    # ============================================================
    # METRICS
    # ============================================================
    @abstractmethod
    def get_metrics(self) -> Dict[str, float]:
        """Return performance metrics for the model.

        Returns:
            Dictionary with at least:
                - 'mae' (float): Mean Absolute Error
                - 'rmse' (float): Root Mean Square Error
                - 'mape' (float): Mean Absolute Percentage Error
                - 'directional_accuracy' (float): Percentage of correct directions
        """
        pass

    # ============================================================
    # METADATA
    # ============================================================
    @abstractmethod
    def get_name(self) -> str:
        """Return the model name.

        Returns:
            Model identifier (e.g., 'prophet', 'xgboost', 'lightgbm').
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return the model version.

        Returns:
            Version string (e.g., '1.0.0').
        """
        pass

    # ============================================================
    # SERIALIZATION
    # ============================================================
    @abstractmethod
    def save(self, path: str) -> None:
        """Save the model to disk.

        Args:
            path: File path to save the model.

        Raises:
            RuntimeError: If the model has not been trained.
        """
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Load the model from disk.

        Args:
            path: File path to load the model from.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        pass

    # ============================================================
    # STATE
    # ============================================================
    def is_model_trained(self) -> bool:
        """Check if the model has been trained.

        Returns:
            True if the model has been trained, False otherwise.
        """
        return self.is_trained

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation of the model."""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.get_name()}', "
            f"version='{self.get_version()}', "
            f"trained={self.is_trained})"
        )