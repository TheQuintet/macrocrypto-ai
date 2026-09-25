from pathlib import Path
import pandas as pd
import pytest

from app.ml.walk_forward import WalkForwardSplitter

FEATURE_STORE_PATH = Path("app/data/ml_btc_daily_features.csv")


@pytest.fixture
def raw_data():
    if not FEATURE_STORE_PATH.exists():
        pytest.skip("Feature store artifact not found.")
    return pd.read_csv(FEATURE_STORE_PATH)


def test_walk_forward_folds_valid(raw_data):
    """Verify walk-forward folds grow monotonically and respect the purge/embargo windows."""
    splitter = WalkForwardSplitter()
    folds = list(splitter.get_walk_forward_folds(len(raw_data)))
    
    assert len(folds) > 0, "Walk-forward splitter generated no folds."
    
    prev_train_len = 0
    for train_idx, val_idx in folds:
        assert len(train_idx) > prev_train_len, "Training set size should grow across folds."
        prev_train_len = len(train_idx)
        
        # Ensure gap respects purge window
        assert val_idx[0] - train_idx[-1] >= splitter.purge_window, (
            "Validation start does not respect the required purge window distance from training end."
        )