from pathlib import Path
import joblib
import pandas as pd

from app.ml.feature_scaler import FeatureScaler
from app.ml.scaler_config import ScalerConfig
from app.ml.splitting_config import SplitConfig
from app.ml.target_generator import TargetGenerator
from app.ml.walk_forward import WalkForwardSplitter

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")
OUTPUT_DIR = Path("app/data/processed")


def build_and_export_ml_datasets(
    csv_path: Path = FEATURE_STORE_PATH, output_dir: Path = OUTPUT_DIR
):
  """Executes Stages 6 through 8 (Target Alignment, Walk-Forward Splitting,

  Feature Scaling, and ML-Ready Dataset Packaging) and persists artifacts to disk.
  """
  output_dir.mkdir(parents=True, exist_ok=True)

  print(f"[Pipeline] Loading raw feature store from {csv_path}...")
  if not csv_path.exists():
    raise FileNotFoundError(f"Feature store artifact not found at {csv_path}")

  df = pd.read_csv(csv_path)

  # 1. Target Generation (Stage 6)
  print("[Stage 6] Generating target alignment (y_t = Price_{t+1})...")
  target_gen = TargetGenerator(price_column="btc_price")
  df_with_target = target_gen.generate_target(df)

  # 2. Walk-Forward Splitting (Stage 6)
  print("[Stage 6] Computing chronological walk-forward splits...")
  split_config = SplitConfig(
      train_ratio=0.80, val_ratio=0.10, test_ratio=0.10, purge_window=90
  )
  splitter = WalkForwardSplitter(config=split_config)
  bounds = splitter.split_indices(len(df_with_target))

  train_start, train_end = bounds["train"]
  val_start, val_end = bounds["val"]
  test_start, test_end = bounds["test"]

  train_df = df_with_target.iloc[train_start:train_end]
  val_df = df_with_target.iloc[val_start:val_end]
  test_df = df_with_target.iloc[test_start:test_end]

  # 3. Train-Exclusive Feature Scaling (Stage 7)
  print(
      "[Stage 7] Fitting FeatureScaler exclusively on training partition"
      " (zero leakage)..."
  )
  scaler_config = ScalerConfig(scaler_type="robust")
  scaler = FeatureScaler(config=scaler_config)

  scaled_train = scaler.fit_transform(train_df)
  scaled_val = scaler.transform(val_df)
  scaled_test = scaler.transform(test_df)

  # 4. Persistence & Packaging (Stage 8)
  train_path = output_dir / "train_scaled.parquet"
  val_path = output_dir / "val_scaled.parquet"
  test_path = output_dir / "test_scaled.parquet"
  scaler_path = output_dir / "feature_scaler.pkl"

  print(f"[Stage 8] Exporting training partition to {train_path}...")
  scaled_train.to_parquet(train_path, index=False)

  print(f"[Stage 8] Exporting validation partition to {val_path}...")
  scaled_val.to_parquet(val_path, index=False)

  print(f"[Stage 8] Exporting test partition to {test_path}...")
  scaled_test.to_parquet(test_path, index=False)

  print(f"[Stage 8] Serializing fitted FeatureScaler to {scaler_path}...")
  joblib.dump(scaler, scaler_path)

  print("[Stage 8] Pipeline completed successfully! All ML-ready artifacts saved.")
  return {
      "train_path": train_path,
      "val_path": val_path,
      "test_path": test_path,
      "scaler_path": scaler_path,
      "feature_columns": scaler.feature_columns,
  }


if __name__ == "__main__":
  build_and_export_ml_datasets()