from pathlib import Path
import pandas as pd
import pytest

from app.ml.feature_scaler import FeatureScaler
from app.ml.scaler_config import ScalerConfig
from app.ml.splitting_config import SplitConfig
from app.ml.target_generator import TargetGenerator
from app.ml.walk_forward import WalkForwardSplitter

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture(scope="module")
def prepared_dataset():
  """Loads the raw feature store and applies Stage 6 target generation."""
  if not FEATURE_STORE_PATH.exists():
    pytest.skip("Feature store artifact not found at expected path.")
  df = pd.read_csv(FEATURE_STORE_PATH)
  generator = TargetGenerator(price_column="btc_price")
  return generator.generate_target(df)


def test_scaler_exclusions(prepared_dataset):
  """Verifies that timestamps, dates, targets, binary flags, and explicit exclusions

  are omitted from feature scaling.
  """
  scaler = FeatureScaler()
  scaler.fit(prepared_dataset)

  # Assert excluded types are completely absent from continuous feature columns
  for col in scaler.feature_columns:
    assert not col.endswith("_timestamp")
    assert not col.endswith("_is_missing")
    assert not col.endswith("_is_imputed")
    assert col != "observation_date"
    assert col != "target_next_price"
    assert col != "warmup_complete"

  # Assert critical continuous financial features ARE included
  assert "btc_price" in scaler.feature_columns
  assert "active_addresses" in scaler.feature_columns
  assert "btc_sma_90" in scaler.feature_columns
  assert "dxy" in scaler.feature_columns


def test_train_exclusive_fitting(prepared_dataset):
  """Asserts that scaling statistics are derived strictly from the training partition

  and validation partitions remain untainted (zero data leakage).
  """
  # Setup walk-forward splits to get exact train/val boundaries
  config = SplitConfig(
      train_ratio=0.80, val_ratio=0.10, test_ratio=0.10, purge_window=90
  )
  splitter = WalkForwardSplitter(config=config)
  bounds = splitter.split_indices(len(prepared_dataset))

  train_start, train_end = bounds["train"]
  val_start, val_end = bounds["val"]

  train_df = prepared_dataset.iloc[train_start:train_end]
  val_df = prepared_dataset.iloc[val_start:val_end]

  # Fit scaler ONLY on training data
  scaler = FeatureScaler()
  scaler.fit(train_df)

  # Transform validation set using training parameters
  transformed_val = scaler.transform(val_df)

  # 1. Verify excluded columns in validation set are 100% identical to raw val data
  assert transformed_val["observation_date"].equals(val_df["observation_date"])
  assert transformed_val["target_next_price"].equals(
      val_df["target_next_price"]
  )
  if "active_addresses_is_imputed" in val_df.columns:
    assert transformed_val["active_addresses_is_imputed"].equals(
        val_df["active_addresses_is_imputed"]
    )

  # 2. Verify continuous features were successfully transformed (values changed)
  assert not transformed_val["btc_price"].equals(val_df["btc_price"])
  assert not transformed_val["active_addresses"].equals(
      val_df["active_addresses"]
  )


def test_unfitted_scaler_error(prepared_dataset):
  """Ensures calling transform() before fit() raises a ValueError."""
  scaler = FeatureScaler()
  with pytest.raises(ValueError, match="must be fitted on training data"):
    scaler.transform(prepared_dataset)