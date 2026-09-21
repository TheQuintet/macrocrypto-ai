import pytest
import pandas as pd
from pathlib import Path

CLEANED_PATH = Path("app/data/ml_btc_daily_cleaned.csv")

@pytest.fixture(scope="module")
def cleaned_df():
    if not CLEANED_PATH.exists():
        pytest.skip("Cleaned dataset not found. Run clean_ml_data.py first.")
    df = pd.read_csv(CLEANED_PATH)
    df["observation_date"] = pd.to_datetime(df["observation_date"], utc=True)
    return df


def test_no_duplicate_observation_dates(cleaned_df):
    """Assertion 1: Ensure unique UTC observation dates."""
    assert cleaned_df["observation_date"].is_unique, "Found duplicate observation dates in cleaned data."


def test_no_future_observations(cleaned_df):
    """Assertion 2: Ensure no observation dates are in the future."""
    max_date = cleaned_df["observation_date"].max()
    today = pd.Timestamp.utcnow().normalize()
    assert max_date <= today, f"Future observation date found: {max_date}"


def test_row_count_preserved(cleaned_df):
    """Assertion 3: Ensure row count matches expected raw baseline (3,321 rows)."""
    assert len(cleaned_df) == 3321, f"Unexpected row count: {len(cleaned_df)}"


def test_continuous_features_complete(cleaned_df):
    """Assertion 4: Continuous daily features must have zero missing values."""
    for col in ["btc_price", "btc_volume"]:
        assert cleaned_df[col].isnull().sum() == 0, f"Missing values found in continuous feature '{col}'."


def test_staleness_flags_consistent(cleaned_df):
    """Assertion 6: Staleness flags must be non-negative integers."""
    stale_cols = [col for col in cleaned_df.columns if col.endswith("_days_since_last_observation")]
    for col in stale_cols:
        assert (cleaned_df[col] >= 0).all(), f"Negative staleness value found in '{col}'."


def test_proxy_and_baml_distinct(cleaned_df):
    """Assertion 11: Proxy feature must never equal canonical high_yield_spread directly."""
    if "high_yield_credit_stress_proxy" in cleaned_df.columns and "high_yield_spread" in cleaned_df.columns:
        overlap = (cleaned_df["high_yield_spread"] == cleaned_df["high_yield_credit_stress_proxy"]).sum()
        assert overlap == 0, "Integrity violation: Proxy matches canonical high_yield_spread on some rows."


def test_timezone_normalized(cleaned_df):
    """Assertion 12: Ensure observation_date is datetime type."""
    assert pd.api.types.is_datetime64tz_dtype(cleaned_df["observation_date"]), "observation_date is not timezone-aware UTC datetime."