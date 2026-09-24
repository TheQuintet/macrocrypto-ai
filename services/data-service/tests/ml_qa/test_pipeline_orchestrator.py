from pathlib import Path
import pandas as pd
import pytest

from app.ml.pipeline_orchestrator import build_and_export_ml_datasets
from app.ml.scaler_config import ScalerConfig


@pytest.fixture(scope="module")
def processed_partitions(tmp_path_factory):
    """Executes the orchestrator to generate real processed partitions and artifacts."""
    output_dir = tmp_path_factory.mktemp("processed_artifacts")
    artifacts = build_and_export_ml_datasets(output_dir=output_dir)
    
    train_df = pd.read_parquet(artifacts["train_path"])
    val_df = pd.read_parquet(artifacts["val_path"])
    test_df = pd.read_parquet(artifacts["test_path"])
    frontier_df = pd.read_parquet(artifacts["frontier_path"])
    
    return train_df, val_df, test_df, frontier_df


def test_pipeline_export_and_integrity(processed_partitions):
    """Validates pipeline artifact exports, row counts, and feature integrity."""
    train_df, val_df, test_df, live_frontier_df = processed_partitions
    config = ScalerConfig()

    # Determine scaled features dynamically using ScalerConfig rules
    def get_scaled_features(df: pd.DataFrame) -> list[str]:
        numeric_cols = df.select_dtypes(include=["number"]).columns
        scaled = []
        for col in numeric_cols:
            if col == config.target_column or col == config.date_column:
                continue
            if col in config.explicit_exclusions:
                continue
            if any(col.endswith(suffix) for suffix in config.exclude_suffixes):
                continue
            scaled.append(col)
        return scaled

    scaled_features = get_scaled_features(train_df)

    # 1. Assert zero NaN values exist strictly across scaled feature columns
    for name, df in [("train", train_df), ("val", val_df), ("test", test_df)]:
        assert df[scaled_features].isnull().sum().sum() == 0, f"Partition '{name}' contains unexpected NaN values in scaled features!"

    # 2. Verify live frontier target is NaN (unrealized future price)
    assert live_frontier_df["target_next_price"].isna().all(), "Live frontier target should be NaN."

    # 3. Verify total supervised rows match expectations (3,132 rows total after splits & purge window)
    total_supervised = len(train_df) + len(val_df) + len(test_df)
    assert total_supervised == 3132, f"Expected 3,132 supervised rows, but found {total_supervised}."

    # 4. Verify live frontier isolation
    assert len(live_frontier_df) == 1, f"Expected 1 live frontier row, but found {len(live_frontier_df)}."