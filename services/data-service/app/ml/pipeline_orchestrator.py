from pathlib import Path
import joblib
import pandas as pd

from app.ml.feature_scaler import FeatureScaler
from app.ml.scaler_config import ScalerConfig
from app.ml.split_processor import SplitProcessor


def build_and_export_ml_datasets(
    output_dir: Path = Path("app/data/processed"),
    scaler_config: ScalerConfig = None,
) -> dict:
    """Orchestrates Stages 6, 7, and 8 of the ML pipeline:
    1. Loads raw feature store data.
    2. Drops warmup rows and isolates live frontier.
    3. Executes SplitProcessor (Governance, Target Gen, Walk-Forward Split).
    4. Executes FeatureScaler (Fit on train, transform val/test/frontier).
    5. Serializes partitions, live frontier, and fitted scaler artifacts.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[Pipeline Orchestrator] Output directory ready: {output_dir}")

    # 1. Load Raw Feature Store
    feature_path = Path("app/data/ml_btc_daily_features.csv")
    if not feature_path.exists():
        raise FileNotFoundError(f"Feature store not found at {feature_path}")

    print(f"[Pipeline Orchestrator] Loading raw features from {feature_path}...")
    raw_df = pd.read_csv(feature_path)
    print(f"[Pipeline Orchestrator] Initial raw shape: {raw_df.shape}")

    # Drop warmup rows before splitting & scaling
    if "warmup_complete" in raw_df.columns:
        initial_len = len(raw_df)
        raw_df = raw_df[raw_df["warmup_complete"] == 1].reset_index(drop=True)
        print(f"[Pipeline Orchestrator] Dropped {initial_len - len(raw_df)} warmup rows. Remaining: {len(raw_df)}")

    # 2. Stage 6: SplitProcessor Execution
    print("[Pipeline Orchestrator] Executing SplitProcessor (Governance, Target Gen, Splits)...")
    split_processor = SplitProcessor()
    split_result = split_processor.process(raw_df)

    train_df = split_result["train"]
    val_df = split_result["val"]
    test_df = split_result["test"]
    frontier_df = split_result["frontier"]

    print(f"  -> Train partition rows: {len(train_df)}")
    print(f"  -> Validation partition rows: {len(val_df)}")
    print(f"  -> Test partition rows: {len(test_df)}")
    print(f"  -> Live frontier rows: {len(frontier_df)}")

    # 3. Stage 7: Feature Scaling & Transformation
    config = scaler_config or ScalerConfig()
    print(f"[Pipeline Orchestrator] Initializing FeatureScaler with type: '{config.scaler_type}'...")
    scaler = FeatureScaler(config=config)
    
    print("[Pipeline Orchestrator] Fitting scaler on train partition and transforming...")
    scaled_train = scaler.fit_transform(train_df)
    
    print("[Pipeline Orchestrator] Transforming validation partition...")
    scaled_val = scaler.transform(val_df)
    
    print("[Pipeline Orchestrator] Transforming test partition...")
    scaled_test = scaler.transform(test_df)
    
    if not frontier_df.empty:
        print("[Pipeline Orchestrator] Transforming live frontier partition...")
        scaled_frontier = scaler.transform(frontier_df)
    else:
        print("[Pipeline Orchestrator] Frontier DataFrame is empty, skipping transformation.")
        scaled_frontier = frontier_df

    print(f"[Pipeline Orchestrator] Scaling complete. Total features scaled: {len(scaler.feature_columns)}")


# 4. Stage 8: Artifact Serialization
    train_path = output_dir / "train_scaled.parquet"
    val_path = output_dir / "val_scaled.parquet"
    test_path = output_dir / "test_scaled.parquet"
    frontier_path = output_dir / "live_frontier_scaled.parquet"  
    scaler_path = output_dir / "feature_scaler.pkl"

    # Define datasets to clean and persist
    datasets_to_persist = {
        "train": scaled_train,
        "val": scaled_val,
        "test": scaled_test,
        "frontier": scaled_frontier
    }

    print("[Pipeline Orchestrator] Pruning timestamp metadata and serializing datasets...")
    for name, df in datasets_to_persist.items():
        if df.empty:
            continue
        # 👉 Drop timestamp metadata columns before persisting
        timestamp_cols = [c for c in df.columns if c.endswith("_timestamp")]
        if timestamp_cols:
            df.drop(columns=timestamp_cols, inplace=True)
            print(f"[Prep] Dropped {len(timestamp_cols)} timestamp columns from {name} partition.")

    # Serialize to Parquet
    scaled_train.to_parquet(train_path, index=False)
    scaled_val.to_parquet(val_path, index=False)
    scaled_test.to_parquet(test_path, index=False)
    scaled_frontier.to_parquet(frontier_path, index=False)
    joblib.dump(scaler, scaler_path)

    print(f"[Pipeline Orchestrator] Successfully exported datasets and scaler to {output_dir}")

    return {
        "train_path": str(train_path),
        "val_path": str(val_path),
        "test_path": str(test_path),
        "frontier_path": str(frontier_path),
        "scaler_path": str(scaler_path),
    }


if __name__ == "__main__":
    build_and_export_ml_datasets()