import pandas as pd
import numpy as np
from pathlib import Path

# Define file paths
INPUT_PATH = Path("app/data/ml_btc_daily_raw.csv")
PROXY_PATH = Path("app/scripts/high_yield_credit_stress_proxy.csv")
OUTPUT_PATH = Path("app/data/ml_btc_daily_cleaned.csv")

# Feature group definitions based on policy
CONTINUOUS_DAILY = ["btc_price", "btc_volume"]

# Business-Day Markets (Includes proxy and market-close assets requiring calendar-day forward-fill)
BUSINESS_DAY_MARKETS = [
    "btc_dominance",
    "gold_spot",
    "dxy",
    "ten_year_treasury",
    "vix",
    "nasdaq_composite",
    "equity_corr",
    "high_yield_credit_stress_proxy",
]

SPARSE_ONCHAIN = ["active_addresses"]

MACRO_FEATURES = [
    "cpi",
    "federal_funds_rate",
    "m2_money_supply",
    "unemployment",
    "gdp",
]


def load_data(filepath: Path, proxy_filepath: Path) -> pd.DataFrame:
    """Load raw dataset and proxy dataset (Date, high_yield_credit_stress_proxy), merging them on observation_date."""
    if not filepath.exists():
        raise FileNotFoundError(f"Input artifact not found at {filepath}")
    
    df = pd.read_csv(filepath)
    df["observation_date"] = pd.to_datetime(df["observation_date"], utc=True)
    df = df.sort_values("observation_date").reset_index(drop=True)

    # Merge separate proxy dataset using specified structure: Date, high_yield_credit_stress_proxy
    if proxy_filepath.exists():
        proxy_df = pd.read_csv(proxy_filepath)
        
        # Verify expected column exists
        if "Date" not in proxy_df.columns or "high_yield_credit_stress_proxy" not in proxy_df.columns:
            raise ValueError("Proxy CSV must contain 'Date' and 'high_yield_credit_stress_proxy' columns.")
            
        proxy_df["observation_date"] = pd.to_datetime(proxy_df["Date"], utc=True)
        proxy_df = proxy_df[["observation_date", "high_yield_credit_stress_proxy"]]
        
        df = pd.merge(df, proxy_df, on="observation_date", how="left")
        
        # QA Bug 3 Verification: Confirm expected pre-ffill coverage (~2,285 non-null rows)
        non_null_proxy_count = df["high_yield_credit_stress_proxy"].notnull().sum()
        print(f"Proxy merge verified: {non_null_proxy_count} non-null rows loaded (expected ~2,283 before ffill).")
        if not (2280 <= non_null_proxy_count <= 2285):
            raise AssertionError(f"Proxy coverage anomaly: found {non_null_proxy_count} non-null rows.")
    
    return df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Apply deterministic, traceable cleaning rules per feature cadence."""
    cleaned = df.copy()

    # 1. Continuous Daily: Assert completeness (no missing values expected)
    for col in CONTINUOUS_DAILY:
        if cleaned[col].isnull().any():
            raise ValueError(f"Data bug: Missing values detected in continuous daily feature '{col}'.")


    # 2. Business-Day Markets (including Proxy): Forward-fill to calendar days + staleness flags
    for col in BUSINESS_DAY_MARKETS:
        if col in cleaned.columns:
            stale_col = f"{col}_days_since_last_observation"
            
            valid_mask = cleaned[col].notnull()
            groups = valid_mask.cumsum()
            
            cleaned[col] = cleaned[col].ffill()
            cleaned[stale_col] = cleaned.groupby(groups).cumcount().astype(int)

    # 3. Special Handling for high_yield_spread: Leave untouched with NaN in gap, add missing flag only
    if "high_yield_spread" in cleaned.columns:
        cleaned["high_yield_spread_is_missing"] = cleaned["high_yield_spread"].isnull().astype(int)

    # 4. Sparse On-Chain (Active Addresses): Forward-fill <= 5 days, mask beyond
    for col in SPARSE_ONCHAIN:
        if col in cleaned.columns:
            imputed_col = f"{col}_is_imputed"
            stale_col = f"{col}_days_since_last_observation"

            valid_mask = cleaned[col].notnull()
            filled_series = cleaned[col].ffill(limit=5)
            
            cleaned[col] = filled_series
            cleaned[stale_col] = (~cleaned[col].notnull()).cumsum()
            cleaned[imputed_col] = ((cleaned[col].notnull()) & (~valid_mask)).astype(int)

    # 5. Macro Features: Release-date as-of alignment handling (Deferred to Ingestion Stage)
    # Note: Full release-date as-of joining requires vintage metadata from ingestion. 
    # For now, macro features are carried forward until a new value appears, 
    # with release alignment explicitly deferred to the next pipeline stage.
    for col in MACRO_FEATURES:
        if col in cleaned.columns:
            stale_col = f"{col}_days_since_release"
            cleaned[col] = cleaned[col].ffill()
            # Placeholder tracking until vintage metadata is integrated
            valid_mask = cleaned[col].notnull()
            groups = valid_mask.cumsum()
            cleaned[stale_col] = cleaned.groupby(groups).cumcount().astype(int)

    # 6. Handle Proxy Feature Governance (Ensure distinct standalone existence)
    if "high_yield_credit_stress_proxy" in cleaned.columns and "high_yield_spread" in cleaned.columns:
        overlap_check = (cleaned["high_yield_spread"] == cleaned["high_yield_credit_stress_proxy"])
        if overlap_check.any():
            raise AssertionError("Integrity violation: Proxy feature matches canonical high_yield_spread values directly.")

    return cleaned


def run_pipeline():
    print("Loading raw ML dataset and proxy data...")
    raw_df = load_data(INPUT_PATH, PROXY_PATH)
    print(f"Loaded dataset with shape: {raw_df.shape}")

    print("Applying data cleaning policies...")
    cleaned_df = clean_dataset(raw_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Saving cleaned dataset to {OUTPUT_PATH}...")
    cleaned_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print("Data cleaning pipeline completed successfully!")


if __name__ == "__main__":
    run_pipeline()