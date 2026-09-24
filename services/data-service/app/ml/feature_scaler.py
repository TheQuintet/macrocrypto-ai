from typing import List, Optional
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
from app.ml.scaler_config import ScalerConfig


class FeatureScaler:
  """Handles feature scaling with strict train-only fitting semantics

  to prevent data leakage in financial time-series pipelines.
  """

  def __init__(self, config: Optional[ScalerConfig] = None):
    self.config = config or ScalerConfig()
    if self.config.scaler_type == "robust":
      self.scaler = RobustScaler()
    elif self.config.scaler_type == "standard":
      self.scaler = StandardScaler()
    else:
      self.scaler = MinMaxScaler()

    self.feature_columns: List[str] = []
    self.is_fitted: bool = False

  def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
    """Identifies continuous feature columns by filtering out timestamps,

    targets, binary flags, and explicit exclusions.
    """
    features = []
    for col in df.columns:
      if col == self.config.date_column or col == self.config.target_column:
        continue
      if col in self.config.explicit_exclusions:
        continue
      if any(col.endswith(suffix) for suffix in self.config.exclude_suffixes):
        continue
      features.append(col)
    return features

  def fit(self, train_df: pd.DataFrame) -> "FeatureScaler":
    """Fits the scaler exclusively on the training partition."""
    self.feature_columns = self._get_feature_columns(train_df)
    self.scaler.fit(train_df[self.feature_columns])
    self.is_fitted = True
    return self

  def transform(self, df: pd.DataFrame) -> pd.DataFrame:
    """Transforms a dataset using parameters learned strictly from the training set."""
    if not self.is_fitted:
      raise ValueError(
          "FeatureScaler must be fitted on training data via fit() before"
          " calling transform()."
      )

    df_out = df.copy()
    scaled_values = self.scaler.transform(df_out[self.feature_columns])
    df_out[self.feature_columns] = scaled_values
    return df_out

  def fit_transform(self, train_df: pd.DataFrame) -> pd.DataFrame:
    """Fits on training data and transforms it in a single step."""
    return self.fit(train_df).transform(train_df)