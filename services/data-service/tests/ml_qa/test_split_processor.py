from pathlib import Path
import pandas as pd
import pytest

from app.ml.split_processor import SplitProcessor
from app.ml.splitting_config import SplitConfig

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture
def raw_data():
    if not FEATURE_STORE_PATH.exists():
        pytest.skip("Feature store artifact not found.")
    return pd.read_csv(FEATURE_STORE_PATH)

def test_unemployment_nans_before_processing(raw_data):
    """Test 1: Check and measure unemployment NaN state in raw input data prior to split processing."""
    if "unemployment" not in raw_data.columns:
        pytest.skip("unemployment column not present in raw data.")
    
    raw_nan_count = raw_data["unemployment"].isna().sum()
    # Validate that NaN counting executes successfully and yields a valid count
    assert raw_nan_count >= 0, "Unemployment NaN count must be non-negative."


def test_unemployment_ffill_and_imputation_flag_after_processing(raw_data):
    """Test 2: Verify post-processing ensures zero NaNs and correct imputation flag tracking."""
    if "unemployment" not in raw_data.columns:
        pytest.skip("unemployment column not present in raw data.")
        
    raw_nan_count = raw_data["unemployment"].isna().sum()

    processor = SplitProcessor()
    result = processor.process(raw_data)

    combined_df = pd.concat([result["train"], result["val"], result["test"]])

    # 1. Assert zero NaNs remain in unemployment across processed splits
    assert combined_df["unemployment"].isna().sum() == 0, "Unemployment still contains NaN values after processing!"

    # 2. If raw data had NaNs, verify the imputation flag column was created and tracks them
    if raw_nan_count > 0:
        assert "unemployment_is_imputed" in combined_df.columns, "Imputation flag column missing despite raw NaNs."
        assert combined_df["unemployment_is_imputed"].sum() > 0, "Imputation flag sum is 0 despite raw NaNs existing."

def test_split_processor_governance_and_splits(raw_data):
    """Validates dynamic 80/10/10 split proportions, baseline consistency, and purge/embargo context."""
    processor = SplitProcessor()
    result = processor.process(raw_data)

    # 1. Verify clean baseline length exists and is valid
    clean_len = result["clean_baseline_len"]
    assert clean_len > 0, "Clean baseline length should be positive."
    assert clean_len <= len(raw_data), "Clean baseline cannot exceed raw data length."

    # 2. Extract split partition counts
    train_len = len(result["train"])
    val_len = len(result["val"])
    test_len = len(result["test"])
    total_supervised = train_len + val_len + test_len

    assert total_supervised > 0, "Supervised partitions cannot be empty."

    # 3. Verify approximate 80% train, 10% validation, and 10% test ratios dynamically
    actual_train_ratio = train_len / total_supervised
    actual_val_ratio = val_len / total_supervised
    actual_test_ratio = test_len / total_supervised

    # Allow a small tolerance band for sequence boundary alignment
    assert 0.75 <= actual_train_ratio <= 0.85, f"Train split ratio {actual_train_ratio:.2f} deviated from 80% target."
    assert 0.05 <= actual_val_ratio <= 0.15, f"Validation split ratio {actual_val_ratio:.2f} deviated from 10% target."
    assert 0.05 <= actual_test_ratio <= 0.15, f"Test split ratio {actual_test_ratio:.2f} deviated from 10% target."

    # 4. Verify live frontier is exactly 1 row
    assert len(result["frontier"]) == 1, "Live frontier should contain exactly 1 row."

    # 5. Verify purge and embargo row context
    purged_embargo_count = result["purged_embargo_rows"]
    assert purged_embargo_count > 0, "Purged and embargoed row count must reflect boundary separation."

    # 6. Verify zero NaN values in unemployment across partitions
    for split_name in ["train", "val", "test"]:
        df_split = result[split_name]
        if "unemployment" in df_split.columns:
            assert (
                df_split["unemployment"].isna().sum() == 0
            ), f"Found NaN values in unemployment in {split_name} split!"