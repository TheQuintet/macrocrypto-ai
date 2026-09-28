from pathlib import Path

import pandas as pd
import pytest

from app.ai.models.feature_utils import CONSTANT_FEATURE_COLUMNS_ATTR
from app.utils.feature_loader import FeatureLoader


@pytest.fixture
def partition_dir(tmp_path: Path) -> Path:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    train = pd.DataFrame(
        {
            "observation_date": dates,
            "target_next_price": [10.0, 11.0, 12.0, 13.0],
            "constant_feature": [1, 1, 1, 1],
            "variable_feature": [2, 3, 4, 5],
        }
    )
    validation = pd.DataFrame(
        {
            "observation_date": dates,
            "target_next_price": [14.0, 15.0, 16.0, 17.0],
            "constant_feature": [9, 8, 7, 6],
            "variable_feature": [2, 3, 4, 5],
        }
    )
    for name, frame in (("train", train), ("val", validation)):
        frame.to_parquet(tmp_path / f"{name}_scaled.parquet", index=False)
    return tmp_path


def test_constant_features_are_removed_using_training_partition(
    partition_dir: Path,
) -> None:
    loader = FeatureLoader(shared_dir=str(partition_dir))

    train = loader.load_partition("train")
    validation = loader.load_partition("val")

    assert "constant_feature" not in train.columns
    assert "constant_feature" not in validation.columns
    assert "variable_feature" in train.columns
    assert "variable_feature" in validation.columns
    assert "observation_date" in train.columns
    assert "target_next_price" in train.columns
    assert train.attrs[CONSTANT_FEATURE_COLUMNS_ATTR] == ["constant_feature"]
    assert validation.attrs[CONSTANT_FEATURE_COLUMNS_ATTR] == [
        "constant_feature"
    ]


def test_validation_load_derives_constants_from_training_partition(
    partition_dir: Path,
) -> None:
    validation = FeatureLoader(shared_dir=str(partition_dir)).load_partition(
        "val"
    )

    assert "constant_feature" not in validation.columns
    assert validation.attrs[CONSTANT_FEATURE_COLUMNS_ATTR] == [
        "constant_feature"
    ]


def test_non_training_partition_requires_training_partition(
    tmp_path: Path,
) -> None:
    pd.DataFrame(
        {
            "observation_date": pd.date_range("2024-01-01", periods=2),
            "feature": [1, 2],
        }
    ).to_parquet(tmp_path / "val_scaled.parquet", index=False)

    with pytest.raises(FileNotFoundError, match="Training partition is required"):
        FeatureLoader(shared_dir=str(tmp_path)).load_partition("val")
