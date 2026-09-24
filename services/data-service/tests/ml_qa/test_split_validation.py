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
    pytest.skip("Feature store artifact not found.")
  return pd.read_csv(FEATURE_STORE_PATH)


def test_date_density_and_continuity(df_feature_store):
  """Confirms the dataset maintains a strict daily calendar grid with no gaps (delta <= 1 day)."""
  if "date" in df_feature_store.columns:
    dates = pd.to_datetime(df_feature_store["date"])
    date_diffs = dates.diff().dt.days.dropna()
    assert (
        date_diffs <= 1
    ).all(), "Found date gaps greater than 1 day in feature store grid!"


def test_partition_boundaries_no_overlap(df_feature_store):
  """Asserts that Train, Validation, and Test partitions have zero index intersection."""
  n_samples = len(df_feature_store)
  config = SplitConfig(
      train_ratio=0.80,
      val_ratio=0.10,
      test_ratio=0.10,
      purge_window=90,
      embargo_window=7,
  )
  splitter = WalkForwardSplitter(config=config)
  bounds = splitter.split_indices(n_samples)

  train_range = range(bounds["train"][0], bounds["train"][1])
  val_range = range(bounds["val"][0], bounds["val"][1])
  test_range = range(bounds["test"][0], bounds["test"][1])

  # Assert strict chronological ordering: Train -> Val -> Test
  assert bounds["train"][1] <= bounds["val"][0]
  assert bounds["val"][1] <= bounds["test"][0]

  # Assert zero index intersection
  assert len(set(train_range).intersection(set(val_range))) == 0
  assert len(set(val_range).intersection(set(test_range))) == 0
  assert len(set(train_range).intersection(set(test_range))) == 0


def test_walk_forward_generator(df_feature_store):
  """Asserts expanding training window sizes, strict purge buffer enforcement, and test set isolation."""
  n_samples = len(df_feature_store)
  config = SplitConfig(
      train_ratio=0.80,
      val_ratio=0.10,
      test_ratio=0.10,
      purge_window=90,
      n_walk_forward_splits=4,
  )
  splitter = WalkForwardSplitter(config=config)
  bounds = splitter.split_indices(n_samples)
  test_start = bounds["test"][0]

  folds = list(splitter.get_walk_forward_folds(n_samples))
  assert len(folds) == 4

  prev_train_len = 0
  for train_idx, val_idx in folds:
    assert len(train_idx) > 0
    assert len(val_idx) > 0

    # 1. Expanding window invariant: each fold's training size must be strictly greater than the previous
    assert len(train_idx) > prev_train_len
    prev_train_len = len(train_idx)

    # 2. Chronological precedence & purge buffer enforcement
    assert train_idx[-1] < val_idx[0]
    assert (
        val_idx[0] - train_idx[-1] >= config.purge_window
    ), f"Purge window requirement of {config.purge_window} days violated!"

    # 3. Test set isolation invariant: validation sets never reach into the test partition
    assert val_idx[-1] < test_start