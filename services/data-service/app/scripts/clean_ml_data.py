"""Clean and align BTC ML training data for point-in-time macro and market features."""
import pandas as pd
import numpy as np
from pathlib import Path

# Define file paths
INPUT_PATH = Path("app/data/ml_btc_daily_raw.csv")
PROXY_PATH = Path("app/scripts/high_yield_credit_stress_proxy.csv")
MACRO_VINTAGE_PATH = Path("app/data/macro_raw_with_vintages.csv")
OUTPUT_PATH = Path("app/data/ml_btc_daily_cleaned.csv")

# Feature group definitions based on policy
CONTINUOUS_DAILY = ["btc_price", "btc_volume"]

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
    """Load raw dataset and proxy dataset, printing detailed metrics for each CSV."""
    print(f"\n[LOADING] Attempting to load primary dataset from: {filepath}")
    if not filepath.exists():
        raise FileNotFoundError(f"Input artifact not found at {filepath}")
    
    df = pd.read_csv(filepath)
    print(f"[SUCCESS] Loaded primary CSV. Shape: {df.shape[0]:,} rows, {df.shape[1]} columns.")
    
    df["observation_date"] = pd.to_datetime(df["observation_date"], utc=True)
    df = df.sort_values("observation_date").reset_index(drop=True)

    # Load separate proxy dataset
    if proxy_filepath.exists():
        print(f"[LOADING] Attempting to load proxy dataset from: {proxy_filepath}")
        proxy_df = pd.read_csv(proxy_filepath)
        print(f"[SUCCESS] Loaded proxy CSV. Shape: {proxy_df.shape[0]:,} rows, {proxy_df.shape[1]} columns.")
        
        # Verify expected column exists
        if "Date" not in proxy_df.columns or "high_yield_credit_stress_proxy" not in proxy_df.columns:
            raise ValueError("Proxy CSV must contain 'Date' and 'high_yield_credit_stress_proxy' columns.")
            
        proxy_df["observation_date"] = pd.to_datetime(proxy_df["Date"], utc=True)
        proxy_df = proxy_df[["observation_date", "high_yield_credit_stress_proxy"]]
        
        df = pd.merge(df, proxy_df, on="observation_date", how="left")
        
        non_null_proxy_count = df["high_yield_credit_stress_proxy"].notnull().sum()
        print(f" -> Proxy merge verified: {non_null_proxy_count:,} non-null rows matched (expected ~2,283 before ffill).")
        if not (2280 <= non_null_proxy_count <= 2285):
            raise AssertionError(f"Proxy coverage anomaly: found {non_null_proxy_count} non-null rows.")
    else:
        print(f"[WARNING] Proxy file not found at {proxy_filepath}. Skipping proxy merge.")
    
    return df


def align_macro_vintages(market_df: pd.DataFrame, macro_vintage_path: Path) -> pd.DataFrame:
    """Performs point-in-time merge_asof joining market timeline with macro vintage releases."""
    print(f"\n[STAGE 5/6] Aligning Macro Vintages (Point-in-Time merge)...")
    if not macro_vintage_path.exists():
        raise FileNotFoundError(f"Macro vintage dataset not found at {macro_vintage_path}. Run fetch_macro_vintages.py first.")

    print(f" -> Loading macro vintage dataset from: {macro_vintage_path}")
    macro_df = pd.read_csv(macro_vintage_path)
    print(f" -> Loaded macro vintage CSV. Total raw vintage records: {len(macro_df):,}")
    
    # Ensure datetimes are properly parsed and timezone-aware (UTC) to match market_df dtypes
    market_df["observation_date"] = pd.to_datetime(market_df["observation_date"], utc=True)
    macro_df["observation_date"] = pd.to_datetime(macro_df["observation_date"], utc=True)
    macro_df["release_date"] = pd.to_datetime(macro_df["release_date"], utc=True)
    
    market_df = market_df.sort_values("observation_date").reset_index(drop=True)
    
    aligned_macro_cols = []

    for feature_name, group in macro_df.groupby("feature_name"):
        group = group.sort_values("release_date")
        
        merged_subset = pd.merge_asof(
            market_df[["observation_date"]],
            group[["release_date", "value"]].rename(columns={"value": feature_name}),
            left_on="observation_date",
            right_on="release_date",
            direction="backward"
        )
        
        stale_col = f"{feature_name}_days_since_release"
        merged_subset[stale_col] = (market_df["observation_date"] - merged_subset["release_date"]).dt.days
        
        aligned_macro_cols.append(merged_subset[[feature_name, stale_col]])
        print(f"    * Processed feature: {feature_name:<20} (aligned successfully)")

    macro_concat = pd.concat(aligned_macro_cols, axis=1)
    
    market_df = market_df.drop(columns=[col for col in MACRO_FEATURES if col in market_df.columns], errors="ignore")
    market_df = pd.concat([market_df, macro_concat], axis=1)
    
    print(" [DONE] Macro vintage alignment completed successfully.")
    return market_df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Apply deterministic, traceable cleaning rules per feature cadence with step-by-step progress output."""
    cleaned = df.copy()

    # 1. Continuous Daily
    print("\n[STAGE 1/6] Validating Continuous Daily Features (btc_price, btc_volume)...")
    for col in CONTINUOUS_DAILY:
        if cleaned[col].isnull().any():
            raise ValueError(f"Data bug: Missing values detected in continuous daily feature '{col}'.")
    print(" [DONE] Continuous daily features verified (0 missing values).")

    # 2. Business-Day Markets
    print("\n[STAGE 2/6] Processing Business-Day Markets & Proxies...")
    for col in BUSINESS_DAY_MARKETS:
        if col in cleaned.columns:
            stale_col = f"{col}_days_since_last_observation"
            valid_mask = cleaned[col].notnull()
            groups = valid_mask.cumsum()
            
            cleaned[col] = cleaned[col].ffill()
            cleaned[stale_col] = cleaned.groupby(groups).cumcount().astype(int)
            print(f"    * Forward-filled and generated staleness tracking for: {col}")

    # 3. Special Spread Handling
    print("\n[STAGE 3/6] Applying High Yield Spread Missing Governance...")
    if "high_yield_spread" in cleaned.columns:
        cleaned["high_yield_spread_is_missing"] = cleaned["high_yield_spread"].isnull().astype(int)
        print(" [DONE] Created high_yield_spread_is_missing flag.")
    else:
        print(" [SKIP] high_yield_spread column not present.")

    # 4. Sparse On-Chain
    print("\n[STAGE 4/6] Processing Sparse On-Chain Data (active_addresses)...")
    for col in SPARSE_ONCHAIN:
        if col in cleaned.columns:
            imputed_col = f"{col}_is_imputed"
            stale_col = f"{col}_days_since_last_observation"

            valid_mask = cleaned[col].notnull()
            filled_series = cleaned[col].ffill(limit=5)
            
            cleaned[col] = filled_series
            cleaned[stale_col] = (~cleaned[col].notnull()).cumsum()
            cleaned[imputed_col] = ((cleaned[col].notnull()) & (~valid_mask)).astype(int)
            print(f"    * Imputed (<=5 day limit) and tracked staleness for: {col}")

    # 5. Macro Features (Point-in-Time Alignment)
    cleaned = align_macro_vintages(cleaned, MACRO_VINTAGE_PATH)

    # 6. Proxy Governance Checks
    print("\n[STAGE 6/6] Executing Proxy Feature Governance Checks...")
    if "high_yield_credit_stress_proxy" in cleaned.columns and "high_yield_spread" in cleaned.columns:
        overlap_check = (cleaned["high_yield_spread"] == cleaned["high_yield_credit_stress_proxy"])
        if overlap_check.any():
            raise AssertionError("Integrity violation: Proxy feature matches canonical high_yield_spread values directly.")
    print(" [DONE] Governance checks passed successfully.")

    return cleaned


def run_pipeline():
    print("==================================================")
    print("       STARTING ML DATA CLEANING PIPELINE         ")
    print("==================================================")
    
    raw_df = load_data(INPUT_PATH, PROXY_PATH)

    print("\n--------------------------------------------------")
    print("Beginning feature cleaning and transformation steps...")
    print("--------------------------------------------------")
    
    cleaned_df = clean_dataset(raw_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print("\n==================================================")
    print(f"Saving finalized cleaned dataset to: {OUTPUT_PATH}")
    cleaned_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    
    print("--------------------------------------------------")
    print(f" PIPELINE COMPLETE SUCCESSFULLY!")
    print(f" Final Output File: {OUTPUT_PATH}")
    print(f" Final Dataset Shape: {cleaned_df.shape[0]:,} rows, {cleaned_df.shape[1]} columns")
    print("==================================================")


if __name__ == "__main__":
    run_pipeline()