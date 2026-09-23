from pathlib import Path
import numpy as np
import pandas as pd

INPUT_PATH = Path("app/data/ml_btc_daily_cleaned.csv")
OUTPUT_PATH = Path("app/data/ml_btc_daily_features.csv")


def engineer_features(input_path: Path, output_path: Path) -> pd.DataFrame:
  """Loads the cleaned SSOT dataset and appends technical indicators,

  log returns, volatility metrics, and cross-asset ratios while preserving
  all original macro features, timestamps, and staleness trackers.
  """
  print(f"Loading cleaned dataset from {input_path}...")
  if not input_path.exists():
    raise FileNotFoundError(f"Cleaned dataset not found at {input_path}")

  df = pd.read_csv(input_path)

  # Ensure proper datetime parsing and strict chronological sorting
  df["observation_date"] = pd.to_datetime(df["observation_date"], utc=True)
  df = df.sort_values("observation_date").reset_index(drop=True)

  print("Computing technical indicators and momentum features...")

  # 1. Multi-horizon Log Returns (Captures short/medium term momentum)
  df["btc_log_return_1d"] = np.log(df["btc_price"] / df["btc_price"].shift(1))
  df["btc_log_return_7d"] = np.log(df["btc_price"] / df["btc_price"].shift(7))
  df["btc_log_return_30d"] = np.log(df["btc_price"] / df["btc_price"].shift(30))

  # 2. Moving Averages (Trend Indicators)
  df["btc_sma_7"] = df["btc_price"].rolling(window=7, min_periods=7).mean()
  df["btc_sma_30"] = df["btc_price"].rolling(window=30, min_periods=30).mean()
  df["btc_sma_90"] = df["btc_price"].rolling(window=90, min_periods=90).mean()

  # 3. Rolling Volatility (Risk Metrics)
  df["btc_volatility_7d"] = df["btc_log_return_1d"].rolling(window=7).std()
  df["btc_volatility_30d"] = df["btc_log_return_1d"].rolling(window=30).std()

  # 4. Cross-Asset Ratios (Relative Valuation)
  if "gold_spot" in df.columns:
    df["btc_gold_ratio"] = df["btc_price"] / df["gold_spot"]

  if "nasdaq_composite" in df.columns:
    df["btc_nasdaq_ratio"] = df["btc_price"] / df["nasdaq_composite"]

  # Save finalized Feature Store artifact
  output_path.parent.mkdir(parents=True, exist_ok=True)
  df.to_csv(output_path, index=False, encoding="utf-8")

  print(f"Feature Store successfully generated and saved to: {output_path}")
  print(f"Final Feature Store shape: {df.shape[0]:,} rows, {df.shape[1]} columns")

  return df


if __name__ == "__main__":
  engineer_features(INPUT_PATH, OUTPUT_PATH)