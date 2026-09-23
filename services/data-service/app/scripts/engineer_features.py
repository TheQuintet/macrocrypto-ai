from pathlib import Path
import numpy as np
import pandas as pd

INPUT_PATH = Path("app/data/ml_btc_daily_cleaned.csv")
OUTPUT_PATH = Path("app/data/ml_btc_daily_features.csv")


def engineer_features(input_path: Path, output_path: Path) -> pd.DataFrame:
  """Loads the cleaned SSOT dataset and appends technical indicators,

  log returns, volatility metrics, cross-asset ratios, and warmup governance
  flags
  while preserving all original macro features, timestamps, and staleness
  trackers.
  """
  print(f"Loading cleaned dataset from {input_path}...")
  if not input_path.exists():
    raise FileNotFoundError(f"Cleaned dataset not found at {input_path}")

  df = pd.read_csv(input_path)

  # Ensure proper datetime parsing and strict chronological sorting assertion
  df["observation_date"] = pd.to_datetime(df["observation_date"], utc=True)
  df = df.sort_values("observation_date").reset_index(drop=True)
  assert df["observation_date"].is_monotonic_increasing, (
      "Dataset is not chronologically sorted!"
  )

  print("Computing technical indicators and momentum features...")

  # 1. Multi-horizon Log Returns (Captures short/medium term momentum)
  df["btc_log_return_1d"] = np.log(df["btc_price"] / df["btc_price"].shift(1))
  df["btc_log_return_7d"] = np.log(df["btc_price"] / df["btc_price"].shift(7))
  df["btc_log_return_30d"] = np.log(df["btc_price"] / df["btc_price"].shift(30))

  # 2. Moving Averages (Trend Indicators with explicit min_periods warmup)
  # Note: Rows 0 to 89 contain NaNs in high-window features due to min_periods warmup.
  df["btc_sma_7"] = df["btc_price"].rolling(window=7, min_periods=7).mean()
  df["btc_sma_30"] = df["btc_price"].rolling(window=30, min_periods=30).mean()
  df["btc_sma_90"] = df["btc_price"].rolling(window=90, min_periods=90).mean()

  # 3. Rolling Volatility (Explicit ddof=1 sample std, annualized for 24/7 crypto markets)
  ANNUALIZATION_FACTOR = np.sqrt(365)
  df["btc_volatility_7d"] = (
      df["btc_log_return_1d"]
      .rolling(window=7, min_periods=7)
      .std(ddof=1)
      * ANNUALIZATION_FACTOR
  )
  df["btc_volatility_30d"] = (
      df["btc_log_return_1d"]
      .rolling(window=30, min_periods=30)
      .std(ddof=1)
      * ANNUALIZATION_FACTOR
  )

  # 4. Cross-Asset Ratios (Relative Valuation)
  if "gold_spot" in df.columns:
    df["btc_gold_ratio"] = df["btc_price"] / df["gold_spot"]

  if "nasdaq_composite" in df.columns:
    df["btc_nasdaq_ratio"] = df["btc_price"] / df["nasdaq_composite"]

  # 5. Warmup Governance Flag (1 when all rolling windows are fully warmed up, 0 during initial NaN rows)
  df["warmup_complete"] = df["btc_sma_90"].notna().astype(int)

  # Pipeline Validation Assertions
  assert len(df) == 3321, f"Row count changed unexpectedly: {len(df)}"
  assert df.shape[1] == 60, (
      f"Expected 60 columns (49 base + 11 engineered), got {df.shape[1]}"
  )

  # Save finalized Feature Store artifact
  output_path.parent.mkdir(parents=True, exist_ok=True)
  df.to_csv(output_path, index=False, encoding="utf-8")

  # Verify encoding compliance (no BOM)
  with open(output_path, "rb") as f:
    assert f.read(3) != b"\xef\xbb\xbf", (
        "Output CSV contains a byte order mark (BOM)!"
    )

  print(f"Feature Store successfully generated and saved to: {output_path}")
  print(f"Final Feature Store shape: {df.shape[0]:,} rows, {df.shape[1]} columns")

  return df


if __name__ == "__main__":
  engineer_features(INPUT_PATH, OUTPUT_PATH)