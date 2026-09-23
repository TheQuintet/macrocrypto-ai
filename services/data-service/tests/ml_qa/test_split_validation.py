from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from app.ml.splitting_config import SplitConfig
from app.ml.walk_forward import WalkForwardSplitter

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture(scope="module")
def df_feature_store():
  if not FEATURE_STORE_PATH.exists():
    pytest.skip("Feature store not found.")
  return pd.read_csv(FEATURE_STORE_PATH)


def test_partition_boundaries_no_overlap(df_feature_store):
  """Asserts that Train (80%), Validation (10%), and Test (10%) partitions have zero index overlap and maintain strict chronological order."""
  n_samples = len(df_feature_store)
  config = SplitConfig(
      train_ratio=0.80, val_ratio=0.10, test_ratio=0.10, purge_window=7, embargo_window=7
  )
  splitter = WalkForwardSplitter(config=config)
  bounds = splitter.split_indices(n_samples)

  train_range = range(bounds["train"][0], bounds["train"][1])
  val_range = range(bounds["val"][0], bounds["val"][1])
  test_range = range(bounds["test"][0], bounds["test"][1])

  # Assert exact ratio approximations
  assert bounds["train"][1] == int(n_samples * 0.80)

  # Assert strict ordering: Train -> Val -> Test
  assert bounds["train"][1] <= bounds["val"][0]
  assert bounds["val"][1] <= bounds["test"][0]

  # Assert zero index intersection
  train_set = set(train_range)
  val_set = set(val_range)
  test_set = set(test_range)

  assert len(train_set.intersection(val_set)) == 0
  assert len(val_set.intersection(test_set)) == 0
  assert len(train_set.intersection(test_set)) == 0


def test_walk_forward_generator(df_feature_store):
  """Asserts walk-forward cross-validation folds expand correctly with purge buffers under SplitConfig settings."""
  n_samples = len(df_feature_store)
  config = SplitConfig(
      train_ratio=0.80,
      val_ratio=0.10,
      test_ratio=0.10,
      purge_window=5,
      n_walk_forward_splits=4,
  )
  splitter = WalkForwardSplitter(config=config)

  folds = list(splitter.get_walk_forward_folds(n_samples))
  assert len(folds) == 4

  for train_idx, val_idx in folds:
    assert len(train_idx) > 0
    assert len(val_idx) > 0
    # Ensure train indices strictly precede validation indices
    assert train_idx[-1] < val_idx[0]