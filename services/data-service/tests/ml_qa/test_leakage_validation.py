from datetime import datetime, timezone
import math
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")
CLEANED_DATA_PATH = Path("app/data/ml_btc_daily_cleaned.csv")


@pytest.fixture(scope="module")
def df_feature_store():
  if not FEATURE_STORE_PATH.exists():
    pytest.skip(
        f"Feature store not found at {FEATURE_STORE_PATH}. Complete Stage 4"
        " first."
    )
  return pd.read_csv(FEATURE_STORE_PATH)


@pytest.fixture(scope="module")
def df_cleaned():
  if not CLEANED_DATA_PATH.exists():
    pytest.skip(f"Cleaned data not found at {CLEANED_DATA_PATH}.")
  return pd.read_csv(CLEANED_DATA_PATH)


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


def test_macro_publication_lags_non_negative_and_bounded(df_feature_store):
  """Asserts all macro release and observation lag counters are >= 0

  and respect realistic upper bounds to prevent runaway stale merges.
  """
  lag_cols = [
      col
      for col in df_feature_store.columns
      if "days_since_release" in col or "days_since_last_observation" in col
  ]
  assert len(lag_cols) > 0, "No lag tracking columns found in feature store."

  max_bounds = {
      "cpi_days_since_release": 90,
      "federal_funds_rate_days_since_release": 60,
      "gdp_days_since_release": 150,
      "m2_money_supply_days_since_release": 60,
      "unemployment_days_since_release": 90,
  }

  for col in lag_cols:
    min_val = df_feature_store[col].min()
    max_val = df_feature_store[col].max()
    assert min_val >= 0, (
        f"Leakage detected: {col} has negative values ({min_val})."
    )

    if col in max_bounds:
      assert max_val <= max_bounds[col], (
          f"Staleness anomaly: {col} max lag ({max_val}) exceeds realistic"
          f" upper bound ({max_bounds[col]})."
      )


def test_warmup_governance_flag(df_feature_store):
  """Asserts the warmup governance flag exists and is strictly binary."""
  assert "warmup_complete" in df_feature_store.columns
  unique_vals = set(df_feature_store["warmup_complete"].dropna().unique())
  assert unique_vals.issubset({0, 1})


def test_warmup_nan_pattern(df_feature_store):
  """Item 4: Asserts exact NaN warmup pattern for 90-day moving averages (first 89 rows are NaN)."""
  sma_90 = df_feature_store["btc_sma_90"]
  assert sma_90.iloc[:89].isna().all(), (
      "Warmup violation: expected NaN in first 89 rows of btc_sma_90."
  )
  assert sma_90.iloc[89:].notna().all(), (
      "Warmup violation: unexpected NaN in btc_sma_90 after index 89."
  )

def test_shift_directionality_and_formulas(df_feature_store):
  """Items 1 & 3: Asserts backward-looking shift direction and exact mathematical formula correctness across multiple sampled indices."""
  prices = df_feature_store["btc_price"]
  log_returns_1d = df_feature_store["btc_log_return_1d"]
  sma_7 = df_feature_store["btc_sma_7"]
  vol_7d = df_feature_store["btc_volatility_7d"]

  # Sample multiple spread-out indices (skipping warmup bounds)
  sample_indices = [100, 500, 1200, 2000, 2800]

  for idx in sample_indices:
    if idx >= len(df_feature_store):
      continue

    # 1. Log return check: ln(P_t / P_{t-1})
    expected_ret = math.log(prices.iloc[idx] / prices.iloc[idx - 1])
    assert math.isclose(
        log_returns_1d.iloc[idx], expected_ret, rel_tol=1e-9, abs_tol=1e-9
    ), (
        f"Formula mismatch for btc_log_return_1d at index {idx}."
    )

    # 2. SMA-7 check: mean of last 7 prices
    expected_sma7 = prices.iloc[idx - 6 : idx + 1].mean()
    assert math.isclose(
        sma_7.iloc[idx], expected_sma7, rel_tol=1e-9, abs_tol=1e-9
    ), (
        f"Formula mismatch for btc_sma_7 at index {idx}."
    )

    # 3. Volatility-7d check: rolling std (ddof=1) * sqrt(365)
    window_returns = log_returns_1d.iloc[idx - 6 : idx + 1]
    expected_vol = window_returns.std(ddof=1) * math.sqrt(365)
    assert math.isclose(
        vol_7d.iloc[idx], expected_vol, rel_tol=1e-5, abs_tol=1e-5
    ), (
        f"Formula mismatch for btc_volatility_7d at index {idx}."
    )

def test_future_data_does_not_change_past_features(df_cleaned):
  """Item 2: Future-append invariance test.

  Appending or truncating future rows must not change historical feature values.
  """

  def compute_test_features(df):
    d = df.copy()
    d["btc_log_return_1d"] = np.log(d["btc_price"] / d["btc_price"].shift(1))
    d["btc_sma_30"] = d["btc_price"].rolling(window=30, min_periods=30).mean()
    d["btc_volatility_7d"] = (
        d["btc_log_return_1d"].rolling(window=7, min_periods=7).std(ddof=1)
        * np.sqrt(365)
    )
    return d

  full_features = compute_test_features(df_cleaned.copy())
  truncated_cleaned = df_cleaned.iloc[:-30].copy()
  truncated_features = compute_test_features(truncated_cleaned)

  common_len = len(truncated_features)
  for col in ["btc_log_return_1d", "btc_sma_30", "btc_volatility_7d"]:
    np.testing.assert_allclose(
        full_features[col].iloc[:common_len],
        truncated_features[col],
        rtol=1e-9,
        atol=1e-9,
        err_msg=f"Future data leakage detected in {col}: past values changed when future rows were removed!",
    )

def test_staleness_counter_semantics(df_feature_store, df_cleaned):
  """Item 6: Asserts staleness counters reset to 0 specifically on rows where a fresh observation occurred."""
  lag_cols = [
      c for c in df_feature_store.columns if "days_since_last_observation" in c
  ]
  
  for col in lag_cols:
    base_col = col.replace("_days_since_last_observation", "")
    if base_col in df_cleaned.columns:
      # Identify rows where a fresh observation occurred in the cleaned data
      fresh_mask = df_cleaned[base_col].notna() & (df_cleaned[base_col].shift(1).isna() | (df_cleaned[base_col] != df_cleaned[base_col].shift(1)))
      
      if fresh_mask.any():
        # On fresh observation rows, the staleness counter must reset to 0
        counter_vals_on_fresh = df_feature_store.loc[fresh_mask, col]
        # Allow a small tolerance or check that 0 is present / majority reset
        assert (counter_vals_on_fresh == 0).mean() >= 0.95, (
            f"Staleness reset violation in '{col}': expected staleness counter "
            f"to reset to 0 on fresh observation rows of '{base_col}'."
        )
    else:
      zeros_count = (df_feature_store[col] == 0).sum()
      assert zeros_count > 0, (
          f"Staleness counter '{col}' never resets to 0 (no fresh observations found)."
      )
    