from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from app.ml.feature_scaler import FeatureScaler
from app.ml.scaler_config import ScalerConfig
from app.ml.target_generator import TargetGenerator

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture(scope="module")
def prepared_dataset():
    """Loads the raw feature store, drops warmup rows, and applies Stage 6 target generation."""
    if not FEATURE_STORE_PATH.exists():
        pytest.skip("Feature store artifact not found at expected path.")
    df = pd.read_csv(FEATURE_STORE_PATH)
    
    if "warmup_complete" in df.columns:
        df = df[df["warmup_complete"] == 1].reset_index(drop=True)

    generator = TargetGenerator(price_column="btc_price")
    return generator.generate_target(df)


def test_scaler_exclusions(prepared_dataset):
    """Verifies that timestamps, dates, targets, binary flags, and explicit exclusions
    are correctly omitted from feature scaling.
    """
    scaler = FeatureScaler()
    temp_features = [col for col in prepared_dataset.select_dtypes(include=["number"]).columns if not scaler._should_exclude(col)]
    clean_data = prepared_dataset.dropna(subset=temp_features)
    scaler.fit(clean_data)

    for col in scaler.feature_columns:
        assert not col.endswith("_timestamp")
        assert not col.endswith("_is_missing")
        assert not col.endswith("_is_imputed")
        assert col != "observation_date"
        assert col != "target_next_price"
        assert col != "warmup_complete"
        assert col != "high_yield_spread"

    assert "btc_price" in scaler.feature_columns
    assert "active_addresses" in scaler.feature_columns
    assert "btc_sma_90" in scaler.feature_columns
    assert "dxy" in scaler.feature_columns


def test_unfitted_scaler_error(prepared_dataset):
    """Ensures calling transform() before fit() raises a ValueError."""
    scaler = FeatureScaler()
    with pytest.raises(ValueError, match="must be fitted"):
        scaler.transform(prepared_dataset)


def test_no_nan_or_inf_after_scaling(prepared_dataset):
    """Ensure that RobustScaler transformation never introduces NaN or Inf values."""
    scaler = FeatureScaler()
    temp_features = [col for col in prepared_dataset.select_dtypes(include=["number"]).columns if not scaler._should_exclude(col)]
    clean_data = prepared_dataset.dropna(subset=temp_features).copy()
    
    scaler.fit(clean_data)
    transformed = scaler.transform(clean_data)

    for col in scaler.feature_columns:
        assert not transformed[col].isna().any(), f"Found NaN values in scaled column: {col}"
        assert not np.isinf(transformed[col]).any(), f"Found Inf values in scaled column: {col}"


def test_validation_uses_train_statistics(prepared_dataset):
    """Prove that validation partitioning is transformed strictly using training statistics."""
    scaler = FeatureScaler()
    temp_features = [col for col in prepared_dataset.select_dtypes(include=["number"]).columns if not scaler._should_exclude(col)]
    clean_data = prepared_dataset.dropna(subset=temp_features).reset_index(drop=True)
    
    train_df = clean_data.iloc[:100].copy()
    val_df = clean_data.iloc[100:150].copy()
    
    scaler.fit(train_df)
    transformed_val = scaler.transform(val_df)
    feature_col = scaler.feature_columns[0]
    
    train_col_data = train_df[feature_col]
    median_train = np.median(train_col_data)
    
    # Use nanpercentile to match scikit-learn's internal robustness
    q25, q75 = np.nanpercentile(train_col_data, [25, 75])
    iqr_train = q75 - q25
    
    # Match sklearn behavior: if IQR is 0, scale defaults to 1.0 to avoid division errors
    if iqr_train == 0:
        iqr_train = 1.0
        
    expected_val = (val_df[feature_col] - median_train) / iqr_train
        
    np.testing.assert_allclose(
        transformed_val[feature_col].values,
        expected_val.values,
        rtol=1e-5,
        atol=1e-5,
        err_msg="Validation set was not transformed using training statistics!"
    )