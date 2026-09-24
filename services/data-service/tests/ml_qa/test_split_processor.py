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


def test_split_processor_governance_and_splits(raw_data):
    """Validates exact Stage 6 row counts, clean baseline (3,230),

    targeted unemployment ffill, and partitioned supervised rows (3,132).
    """
    processor = SplitProcessor()
    result = processor.process(raw_data)

    # 1. Verify Clean Baseline length (3,321 - 89 warmup - 2 active_addresses = 3,230)
    assert (
        result["clean_baseline_len"] == 3230
    ), f"Expected 3,230 clean baseline rows, got {result['clean_baseline_len']}"

    # 2. Verify partition sums equal supervised split count (3,132)
    total_split_rows = (
        len(result["train"]) + len(result["val"]) + len(result["test"])
    )
    assert (
        total_split_rows == 3132
    ), f"Expected 3,132 total supervised split rows, got {total_split_rows}"

    # 3. Verify individual split shapes and expected counts
    assert len(result["train"]) == 2583
    assert len(result["val"]) == 322
    assert len(result["test"]) == 227

    # 4. Verify live frontier is exactly 1 row
    assert len(result["frontier"]) == 1

    # 5. Verify purged/embargoed boundary row count matches expected (97 rows)
    assert (
        result["purged_embargo_rows"] == 97
    ), f"Expected 97 purged/embargoed rows, got {result['purged_embargo_rows']}"

    # 6. Verify zero NaN values in unemployment across partitions
    for split_name in ["train", "val", "test"]:
        df_split = result[split_name]
        if "unemployment" in df_split.columns:
            assert (
                df_split["unemployment"].isna().sum() == 0
            ), f"Found NaN values in unemployment in {split_name} split!"