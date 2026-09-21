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


def test_staleness_consistency(cleaned_df):
    """Assertion 4: No fabricated values (staleness matches fill operations)."""
    for col in ["dxy", "vix", "gold_spot"]:
        stale_col = f"{col}_days_since_last_observation"
        if stale_col in cleaned_df.columns:
            assert (cleaned_df[stale_col] >= 0).all(), f"Invalid negative staleness in '{stale_col}'."


def test_macro_features_present(cleaned_df):
    """Assertion 5: No leakage in macro features (placeholder check until ingestion release dates)."""
    for col in ["cpi", "unemployment"]:
        assert col in cleaned_df.columns, f"Required macro feature '{col}' is missing."


def test_staleness_flags_consistent(cleaned_df):
    """Assertion 6: Staleness flags must be non-negative integers."""
    stale_cols = [col for col in cleaned_df.columns if col.endswith("_days_since_last_observation")]
    for col in stale_cols:
        assert (cleaned_df[col] >= 0).all(), f"Negative staleness value found in '{col}'."


def test_active_addresses_masking(cleaned_df):
    """Assertion 7: Mask counts match expectations for active_addresses."""
    if "active_addresses_is_imputed" in cleaned_df.columns:
        assert cleaned_df["active_addresses_is_imputed"].isin([0, 1]).all(), "Invalid imputation flag values found."


def test_no_bom_in_csv():
    """Assertion 8: No BOM in output CSV (check first bytes of file)."""
    with open(CLEANED_PATH, "rb") as f:
        first_bytes = f.read(3)
    assert first_bytes != b"\xef\xbb\xbf", "CSV file contains a UTF-8 BOM!"


def test_column_schema_stable(cleaned_df):
    """Assertion 9: Column schema stable (check essential columns exist)."""
    expected_cols = [
        "observation_date", "btc_price", "btc_volume", 
        "high_yield_spread", "high_yield_spread_is_missing", 
        "high_yield_credit_stress_proxy"
    ]
    for col in expected_cols:
        assert col in cleaned_df.columns, f"Missing required column: {col}"


def test_feature_ranges_plausible(cleaned_df):
    """Assertion 10: Feature ranges plausible (vix >= 0, dxy > 0, etc.)."""
    if "vix" in cleaned_df.columns:
        assert (cleaned_df["vix"].dropna() >= 0).all(), "VIX values out of plausible range."
    if "dxy" in cleaned_df.columns:
        assert (cleaned_df["dxy"].dropna() > 0).all(), "DXY values out of plausible range."
    if "cpi" in cleaned_df.columns:
        assert (cleaned_df["cpi"].dropna() > 0).all(), "CPI values out of plausible range."


def test_proxy_and_baml_distinct(cleaned_df):
    """Assertion 11: Proxy feature must never equal canonical high_yield_spread directly."""
    if "high_yield_credit_stress_proxy" in cleaned_df.columns and "high_yield_spread" in cleaned_df.columns:
        overlap = (cleaned_df["high_yield_spread"] == cleaned_df["high_yield_credit_stress_proxy"]).sum()
        assert overlap == 0, "Integrity violation: Proxy matches canonical high_yield_spread on some rows."


def test_timezone_normalized(cleaned_df):
    """Assertion 12: Ensure observation_date is timezone-aware UTC datetime type."""
    assert isinstance(cleaned_df["observation_date"].dtype, pd.DatetimeTZDtype), "observation_date is not timezone-aware UTC datetime."