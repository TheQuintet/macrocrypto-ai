from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from app.ml.splitting_config import SplitConfig
from app.ml.target_generator import TargetGenerator
from app.ml.walk_forward import WalkForwardSplitter

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture(scope="module")
def df_feature_store():
  if not FEATURE_STORE_PATH.exists():
    pytest.skip("Feature store artifact not found.")
  return pd.read_csv(FEATURE_STORE_PATH)


@pytest.fixture(scope="module")
def prepared_data(df_feature_store):
  generator = TargetGenerator()
  return generator.generate_target(df_feature_store)


def test_date_density_and_continuity(df_feature_store):
  """Confirms the dataset maintains a strict daily calendar grid with zero gaps (delta == 1 day) using observation_date."""
  assert (
      "observation_date" in df_feature_store.columns
  ), "Column 'observation_date' missing from feature store."
  dates = pd.to_datetime(df_feature_store["observation_date"], utc=True)
  date_diffs = dates.diff().dt.days.dropna()
  gaps = date_diffs[date_diffs != 1]
  assert (
      date_diffs == 1
  ).all(), f"Found date gaps or duplicates in feature store grid: {gaps}"


def test_target_generator_and_frontier(prepared_data):
  """Verifies TargetGenerator aligns y_t = Price_{t+1} and isolates the final row as the live inference frontier (NaN)."""
  assert "target_next_price" in prepared_data.columns
  # The absolute final row must have a NaN target (unlabeled live frontier)
  assert pd.isna(prepared_data["target_next_price"].iloc[-1])
  # Historical rows must have valid targets
  assert not prepared_data["target_next_price"].iloc[:-1].isna().any()


def test_exact_partition_sizes_and_boundaries(prepared_data):
  """Asserts exact row counts and boundary indices matching review specifications for N=3321."""
  n_samples = len(prepared_data)
  assert n_samples == 3321, f"Expected 3321 samples, got {n_samples}"

  config = SplitConfig(
      train_ratio=0.80,
      val_ratio=0.10,
      test_ratio=0.10,
      purge_window=90,
      embargo_window=7,
  )
  splitter = WalkForwardSplitter(config=config)
  bounds = splitter.split_indices(n_samples)

  # Assert exact boundary indices matching the review specification
  assert bounds["train"] == (0, 2656)
  assert bounds["val"] == (2746, 3078)
  assert bounds["test"] == (3085, 3321)

  train_len = bounds["train"][1] - bounds["train"][0]
  val_len = bounds["val"][1] - bounds["val"][0]
  test_len = bounds["test"][1] - bounds["test"][0]

  assert train_len == 2656, f"Expected train len 2656, got {train_len}"
  assert val_len == 332, f"Expected val len 332, got {val_len}"
  assert test_len == 236, f"Expected test len 236, got {test_len}"
  assert bounds["val"][0] - bounds["train"][1] == 90, "Purge window must be 90"
  assert bounds["test"][0] - bounds["val"][1] == 7, "Embargo window must be 7"


def test_partition_boundaries_no_overlap(prepared_data):
  """Asserts that Train, Validation, and Test partitions have zero index intersection."""
  n_samples = len(prepared_data)
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

  assert bounds["train"][1] <= bounds["val"][0]
  assert bounds["val"][1] <= bounds["test"][0]

  assert len(set(train_range).intersection(set(val_range))) == 0
  assert len(set(val_range).intersection(set(test_range))) == 0
  assert len(set(train_range).intersection(set(test_range))) == 0


def test_walk_forward_generator(prepared_data):
  """Asserts expanding training window sizes, strict purge buffer enforcement, and test set isolation."""
  n_samples = len(prepared_data)
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
    assert len(train_idx) > prev_train_len
    prev_train_len = len(train_idx)

    assert train_idx[-1] < val_idx[0]
    assert val_idx[0] - train_idx[-1] >= config.purge_window
    assert val_idx[-1] < test_start