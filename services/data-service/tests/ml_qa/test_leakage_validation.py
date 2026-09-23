from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pytest

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture(scope="module")
def df_feature_store():
  if not FEATURE_STORE_PATH.exists():
    pytest.skip(
        f"Feature store not found at {FEATURE_STORE_PATH}. Complete Stage 4"
        " first."
    )
  return pd.read_csv(FEATURE_STORE_PATH)


def test_feature_store_dimensions(df_feature_store):
  """Asserts exact row and column dimensions for leakage prevention audit."""
  assert len(df_feature_store) == 3321
  assert df_feature_store.shape[1] == 60


def test_temporal_monotonicity(df_feature_store):
  """Asserts strict chronological ordering to prevent look-ahead bias."""
  dates = pd.to_datetime(df_feature_store["observation_date"], utc=True)
  assert dates.is_monotonic_increasing


def test_no_future_timestamps(df_feature_store):
  """Asserts no observation date exceeds current execution time."""
  dates = pd.to_datetime(df_feature_store["observation_date"], utc=True)
  now = datetime.now(timezone.utc)
  assert (dates <= now).all()


def test_macro_publication_lags_non_negative(df_feature_store):
  """Asserts all macro release and observation lag counters are >= 0."""
  lag_cols = [
      col
      for col in df_feature_store.columns
      if "days_since_release" in col or "days_since_last_observation" in col
  ]
  assert len(lag_cols) > 0, "No lag tracking columns found in feature store."
  for col in lag_cols:
    assert df_feature_store[col].min() >= 0, (
        f"Leakage detected: {col} has negative values."
    )


def test_warmup_governance_flag(df_feature_store):
  """Asserts the warmup governance flag exists and is strictly binary."""
  assert "warmup_complete" in df_feature_store.columns
  unique_vals = set(df_feature_store["warmup_complete"].dropna().unique())
  assert unique_vals.issubset({0, 1})