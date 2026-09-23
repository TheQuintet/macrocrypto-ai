from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import pytest

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture(scope="module")
def df_features():
  if not FEATURE_STORE_PATH.exists():
    pytest.skip(
        f"Feature store artifact not found at {FEATURE_STORE_PATH}."
        " Run script first."
    )
  return pd.read_csv(FEATURE_STORE_PATH)


def test_row_and_column_counts(df_features):
  """Asserts exact dimensions: 3,321 rows and 60 columns."""
  assert len(df_features) == 3321, f"Expected 3321 rows, got {len(df_features)}"
  assert df_features.shape[1] == 60, (
      f"Expected 60 columns, got {df_features.shape[1]}"
  )


def test_chronological_ordering(df_features):
  """Asserts observation_date is strictly monotonic increasing."""
  dates = pd.to_datetime(df_features["observation_date"], utc=True)
  assert dates.is_monotonic_increasing, (
      "Feature store is not chronologically sorted!"
  )


def test_no_future_dates(df_features):
  """Asserts no observation date is in the future."""
  dates = pd.to_datetime(df_features["observation_date"], utc=True)
  now = datetime.now(timezone.utc)
  assert (dates <= now).all(), "Feature store contains future dates!"


def test_log_return_bounds(df_features):
  """Asserts 1-day log return stays within a realistic daily bound (< 100% absolute change, i.e., abs < 1.0)."""
  valid_returns = df_features["btc_log_return_1d"].dropna()
  assert (abs(valid_returns) < 1.0).all(), (
      "Found extreme anomalous 1-day log returns exceeding absolute log 1.0."
  )


def test_positive_indicators(df_features):
  """Asserts SMAs, volatilities, and ratios maintain valid mathematical domains."""
  # SMAs must be positive where not NaN
  smas = ["btc_sma_7", "btc_sma_30", "btc_sma_90"]
  for col in smas:
    assert (df_features[col].dropna() > 0).all(), (
        f"{col} contains non-positive values."
    )

  # Volatilities must be non-negative where not NaN
  vols = ["btc_volatility_7d", "btc_volatility_30d"]
  for col in vols:
    assert (df_features[col].dropna() >= 0).all(), (
        f"{col} contains negative volatility."
    )

  # Ratios must be positive where not NaN
  ratios = ["btc_gold_ratio", "btc_nasdaq_ratio"]
  for col in ratios:
    if col in df_features.columns:
      assert (df_features[col].dropna() > 0).all(), (
          f"{col} contains non-positive values."
      )


def test_encoding_no_bom():
  """Asserts output CSV is saved in UTF-8 without BOM."""
  with open(FEATURE_STORE_PATH, "rb") as f:
    header_bytes = f.read(3)
    assert header_bytes != b"\xef\xbb\xbf", (
        "Feature store CSV has a Byte Order Mark (BOM)!"
    )