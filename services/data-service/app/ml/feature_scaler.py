from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from app.ml.scaler_config import ScalerConfig


class FeatureScaler:
    """Handles feature normalization using configurable scalers (Robust, Standard,
    MinMax), ensuring fitting is performed exclusively on the training partition.
    """

    def __init__(self, config: ScalerConfig = None):
        self.config = config or ScalerConfig()
        self._init_scaler()
        self.feature_columns = []
        self.is_fitted = False

    def _init_scaler(self):
        """Initializes the underlying scikit-learn scaler based on configuration."""
        if self.config.scaler_type == "robust":
            self.scaler = RobustScaler()
        elif self.config.scaler_type == "standard":
            self.scaler = StandardScaler()
        elif self.config.scaler_type == "minmax":
            self.scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unsupported scaler_type: {self.config.scaler_type}")

    def _should_exclude(self, col: str) -> bool:
        """Determines if a column should be excluded from scaling based on config rules."""
        if col == self.config.target_column or col == self.config.date_column:
            return True
        if col in self.config.explicit_exclusions:
            return True
        if any(col.endswith(suffix) for suffix in self.config.exclude_suffixes):
            return True
        return False

    def fit(self, train_df: pd.DataFrame):
        """Fits the scaler on the training set with defensive NaN validation."""
        numeric_cols = train_df.select_dtypes(include=["number"]).columns
        self.feature_columns = [
            col for col in numeric_cols if not self._should_exclude(col)
        ]

        # Fail loudly if the training set still has NaN in feature columns
        null_counts = train_df[self.feature_columns].isna().sum()
        if null_counts.any():
            raise ValueError(
                f"Training set contains NaN in feature columns: "
                f"{null_counts[null_counts > 0].to_dict()}"
            )

        self.scaler.fit(train_df[self.feature_columns])
        self.is_fitted = True
        return self

    def fit_transform(self, train_df: pd.DataFrame) -> pd.DataFrame:
        """Fits and transforms the training partition."""
        self.fit(train_df)
        return self.transform(train_df)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transforms partitions using fitted parameters from training."""
        if not self.is_fitted:
            raise ValueError(
                "FeatureScaler must be fitted using fit() or fit_transform() before calling transform()."
            )

        transformed_df = df.copy()

        # Guard against empty DataFrames (0 samples) to prevent scikit-learn errors
        if transformed_df.empty:
            raise ValueError(
                "Cannot transform an empty DataFrame (0 samples received). "
                "Check your data splitting, slicing, or filtering logic."
            )

        cols_to_scale = [
            col for col in self.feature_columns if col in transformed_df.columns
        ]
        
        if cols_to_scale:
            transformed_df[cols_to_scale] = self.scaler.transform(
                transformed_df[cols_to_scale]
            )
        return transformed_df