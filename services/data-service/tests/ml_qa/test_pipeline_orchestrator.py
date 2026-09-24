from pathlib import Path
import joblib
import pandas as pd
import pytest

from app.ml.pipeline_orchestrator import (
    FEATURE_STORE_PATH,
    build_and_export_ml_datasets,
)


@pytest.fixture
def temp_output_dir(tmp_path):
  """Provides a temporary directory for pipeline export artifacts during testing."""
  return tmp_path / "processed"


def test_pipeline_orchestrator_execution(temp_output_dir):
  """End-to-end test verifying that the orchestrator successfully generates

  all expected Parquet and Joblib artifacts from the raw feature store.
  """
  if not FEATURE_STORE_PATH.exists():
    pytest.skip("Feature store artifact not found at expected path.")

  # Run the orchestrator with the temporary output directory
  artifacts = build_and_export_ml_datasets(
      csv_path=FEATURE_STORE_PATH, output_dir=temp_output_dir
  )

  # 1. Verify artifact paths are returned correctly
  assert artifacts["train_path"].exists()
  assert artifacts["val_path"].exists()
  assert artifacts["test_path"].exists()
  assert artifacts["scaler_path"].exists()

  # 2. Verify Parquet partitions can be loaded back and contain expected columns
  train_df = pd.read_parquet(artifacts["train_path"])
  val_df = pd.read_parquet(artifacts["val_path"])
  test_df = pd.read_parquet(artifacts["test_path"])

  assert not train_df.empty
  assert not val_df.empty
  assert not test_df.empty
  assert "target_next_price" in train_df.columns
  assert "observation_date" in train_df.columns

  # 3. Verify fitted scaler can be loaded back successfully
  scaler = joblib.load(artifacts["scaler_path"])
  assert scaler.is_fitted
  assert len(scaler.feature_columns) > 0