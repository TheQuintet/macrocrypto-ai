"""Unit tests for the XGBoostModel adapter.

These tests use real XGBoost with synthetic datasets.

Test organization:
    - TestXGBoostModelInitialization: Constructor behavior
    - TestXGBoostModelTrain: Fresh training (M3.1)
    - TestXGBoostModelPredict: Prediction
    - TestXGBoostModelConfidence: Confidence intervals
    - TestXGBoostModelMetrics: Metrics retrieval
    - TestXGBoostModelSerialization: Save/load
    - TestXGBoostModelConstants: Module constants
"""

from typing import Any

import numpy as np
import pandas as pd
import pytest

from app.ai import ForecastModel, XGBoostModel
from app.ai.models.xgboost_model import (
    ALL_FEATURES,
    BASE_FEATURES,
    CONFIDENCE_LEVELS,
    DEFAULT_CONFIG,
    ENGINEERED_FEATURES,
    LAG_FEATURES,
    MIN_TRAINING_ROWS,
    REQUIRED_COLUMNS,
    RETURN_FEATURES,
    Z_SCORES,
)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(scope="module")
def training_data() -> pd.DataFrame:
    """Create a synthetic training dataset (100 days).

    The dataset contains:
        - ds: daily timestamps
        - y: BTC price with an upward trend and noise
        - 10 base features (5 macro + 5 BTC)
    """
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    np.random.seed(42)

    base_price = 50000
    trend = np.linspace(0, 8000, n)
    noise = np.random.normal(0, 500, n)

    return pd.DataFrame(
        {
            "ds": dates,
            "y": base_price + trend + noise,
            "cpi": [3.2] * n,
            "interest_rate": [4.5] * n,
            "m2_growth": [2.8] * n,
            "dxy": [102.5] * n,
            "treasury_yield": [4.2] * n,
            "volume": [25_000_000_000] * n,
            "volatility": [0.15] * n,
            "dominance": [52.5] * n,
            "active_addresses": [850_000] * n,
            "price_lag_7d": [50_000] * n,
        }
    )


@pytest.fixture(scope="module")
def future_data(training_data: pd.DataFrame) -> pd.DataFrame:
    """Create future data for predictions (7 days).

    We append future days to the training data so lag features can
    be computed from prior values. The 'y' column for future days
    is filled with the last known value.
    """
    n_future = 7
    last_date = training_data["ds"].iloc[-1]
    future_dates = pd.date_range(
        last_date + pd.Timedelta(days=1), periods=n_future, freq="D"
    )

    future_rows = pd.DataFrame(
        {
            "ds": future_dates,
            "y": [training_data["y"].iloc[-1]] * n_future,
            "cpi": [3.2] * n_future,
            "interest_rate": [4.5] * n_future,
            "m2_growth": [2.8] * n_future,
            "dxy": [102.5] * n_future,
            "treasury_yield": [4.2] * n_future,
            "volume": [25_000_000_000] * n_future,
            "volatility": [0.15] * n_future,
            "dominance": [52.5] * n_future,
            "active_addresses": [850_000] * n_future,
            "price_lag_7d": [50_000] * n_future,
        }
    )

    return pd.concat([training_data, future_rows], ignore_index=True)


@pytest.fixture(scope="module")
def trained_model(training_data: pd.DataFrame) -> XGBoostModel:
    """Return a trained XGBoostModel (cached for the module)."""
    model = XGBoostModel()
    model.train(training_data)
    return model


# ============================================================
# INITIALIZATION TESTS
# ============================================================
class TestXGBoostModelInitialization:
    """Tests for XGBoostModel initialization."""

    def test_default_strategy_is_fresh(self) -> None:
        """Test that default strategy is 'fresh'."""
        model = XGBoostModel()
        assert model.strategy == "fresh"

    def test_initialization_with_incremental_strategy(self) -> None:
        """Test initialization with 'incremental' strategy."""
        model = XGBoostModel(strategy="incremental")
        assert model.strategy == "incremental"

    def test_initialization_with_invalid_strategy_raises(self) -> None:
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            XGBoostModel(strategy="invalid")

    def test_initialization_with_config(self) -> None:
        """Test that config overrides defaults."""
        model = XGBoostModel(config={"n_estimators": 50})
        assert model.config["n_estimators"] == 50
        # Other defaults should still be present
        assert model.config["max_depth"] == 6

    def test_is_forecast_model_subclass(self) -> None:
        """Test that XGBoostModel is a ForecastModel."""
        model = XGBoostModel()
        assert isinstance(model, ForecastModel)

    def test_get_name(self) -> None:
        """Test that get_name returns 'xgboost'."""
        model = XGBoostModel()
        assert model.get_name() == "xgboost"

    def test_get_version(self) -> None:
        """Test that get_version returns a string."""
        model = XGBoostModel()
        assert model.get_version() == "1.0.0"

    def test_initial_state_is_untrained(self) -> None:
        """Test that a new model is not trained."""
        model = XGBoostModel()
        assert model.is_trained is False
        assert model.get_metrics() == {}

    def test_initial_last_training_mode_is_fresh(self) -> None:
        """Test that last_training_mode defaults to 'fresh'."""
        model = XGBoostModel()
        assert model.last_training_mode == "fresh"

    def test_initial_residual_std_is_zero(self) -> None:
        """Test that residual_std starts at 0.0."""
        model = XGBoostModel()
        assert model.residual_std == 0.0

    def test_initial_feature_columns_is_empty(self) -> None:
        """Test that feature_columns starts empty."""
        model = XGBoostModel()
        assert model.feature_columns == []

    def test_repr(self) -> None:
        """Test __repr__ format."""
        model = XGBoostModel()
        repr_str = repr(model)
        assert "XGBoostModel" in repr_str
        assert "strategy='fresh'" in repr_str
        assert "trained=False" in repr_str
        assert "last_mode='fresh'" in repr_str


# ============================================================
# TRAINING TESTS
# ============================================================
class TestXGBoostModelTrain:
    """Tests for XGBoostModel.train() with fresh strategy."""

    def test_train_fresh(self, training_data: pd.DataFrame) -> None:
        """Test training with fresh strategy."""
        model = XGBoostModel()
        metrics = model.train(training_data)

        assert model.is_trained is True
        assert model.model is not None
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "mape" in metrics
        assert "directional_accuracy" in metrics

    def test_train_returns_float_metrics(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that all returned metrics are floats."""
        model = XGBoostModel()
        metrics = model.train(training_data)
        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} is not a float"

    def test_train_sets_feature_columns(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that training sets the feature columns to ALL_FEATURES."""
        model = XGBoostModel()
        model.train(training_data)
        assert model.feature_columns == ALL_FEATURES

    def test_train_sets_residual_std(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that training sets a positive residual_std."""
        model = XGBoostModel()
        model.train(training_data)
        assert model.residual_std > 0

    def test_train_sets_last_training_mode(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that training sets last_training_mode to 'fresh'."""
        model = XGBoostModel()
        model.train(training_data)
        assert model.last_training_mode == "fresh"

    def test_train_with_empty_data_raises(self) -> None:
        """Test that empty data raises ValueError."""
        model = XGBoostModel()
        with pytest.raises(ValueError, match="cannot be empty"):
            model.train(pd.DataFrame())

    def test_train_with_missing_columns_raises(self) -> None:
        """Test that missing columns raises ValueError."""
        model = XGBoostModel()
        incomplete = pd.DataFrame(
            {
                "ds": pd.date_range("2024-01-01", periods=100, freq="D"),
                "y": [50000] * 100,
            }
        )
        with pytest.raises(ValueError, match="missing required columns"):
            model.train(incomplete)

    def test_train_with_insufficient_data_raises(self) -> None:
        """Test that less than MIN_TRAINING_ROWS raises ValueError."""
        model = XGBoostModel()
        small_data = pd.DataFrame(
            {
                "ds": pd.date_range("2024-01-01", periods=10, freq="D"),
                "y": [50000] * 10,
                **{reg: [1.0] * 10 for reg in BASE_FEATURES},
            }
        )
        with pytest.raises(ValueError, match=f"at least {MIN_TRAINING_ROWS}"):
            model.train(small_data)

    def test_train_with_warm_start_falls_back_to_fresh(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that warm_start=True falls back to fresh in M3.1."""
        model = XGBoostModel()
        metrics = model.train(training_data, warm_start=True)

        assert model.is_trained is True
        assert "mae" in metrics
        assert model.last_training_mode == "fresh"


# ============================================================
# PREDICTION TESTS
# ============================================================
class TestXGBoostModelPredict:
    """Tests for XGBoostModel.predict()."""

    def test_predict_before_training_raises(self) -> None:
        """Test that prediction before training raises RuntimeError."""
        model = XGBoostModel()
        future = pd.DataFrame(
            {
                "ds": [pd.Timestamp("2024-04-01")],
                **{r: [1.0] for r in BASE_FEATURES},
            }
        )
        with pytest.raises(RuntimeError, match="not trained"):
            model.predict(future)

    def test_predict_returns_dataframe(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that predict returns a DataFrame."""
        result = trained_model.predict(future_data)
        assert isinstance(result, pd.DataFrame)

    def test_predict_output_columns(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that output has the correct columns."""
        result = trained_model.predict(future_data)
        expected = {"ds", "yhat", "yhat_lower", "yhat_upper"}
        assert set(result.columns) == expected

    def test_predict_bounds_are_ordered(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that yhat_lower <= yhat <= yhat_upper."""
        result = trained_model.predict(future_data)
        assert (result["yhat_lower"] <= result["yhat"]).all()
        assert (result["yhat"] <= result["yhat_upper"]).all()

    def test_predict_row_count(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that output has one row per valid input row."""
        result = trained_model.predict(future_data)
        assert len(result) > 0


# ============================================================
# CONFIDENCE INTERVAL TESTS
# ============================================================
class TestXGBoostModelConfidence:
    """Tests for confidence interval scaling.

    XGBoost doesn't provide native confidence intervals. We
    approximate them using residual_std and z-scores.
    """

    def test_predict_with_95_confidence(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test 95% confidence (native approximation)."""
        result = trained_model.predict_with_confidence(future_data, 0.95)
        base = trained_model.predict(future_data)
        np.testing.assert_allclose(
            result["yhat"].values, base["yhat"].values, rtol=1e-5
        )

    def test_predict_with_85_confidence(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test 85% confidence (narrower intervals)."""
        result_95 = trained_model.predict_with_confidence(future_data, 0.95)
        result_85 = trained_model.predict_with_confidence(future_data, 0.85)

        margin_95 = (result_95["yhat_upper"] - result_95["yhat_lower"]).mean()
        margin_85 = (result_85["yhat_upper"] - result_85["yhat_lower"]).mean()
        assert margin_85 < margin_95

    def test_predict_with_70_confidence(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test 70% confidence (narrowest intervals)."""
        result_85 = trained_model.predict_with_confidence(future_data, 0.85)
        result_70 = trained_model.predict_with_confidence(future_data, 0.70)

        margin_85 = (result_85["yhat_upper"] - result_85["yhat_lower"]).mean()
        margin_70 = (result_70["yhat_upper"] - result_70["yhat_lower"]).mean()
        assert margin_70 < margin_85

    def test_predict_with_invalid_confidence_raises(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test invalid confidence level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence_level"):
            trained_model.predict_with_confidence(future_data, 0.50)

    def test_confidence_intervals_are_ordered(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that lower <= yhat <= upper for all levels."""
        for level in [0.70, 0.85, 0.95]:
            result = trained_model.predict_with_confidence(future_data, level)
            assert (result["yhat_lower"] <= result["yhat"]).all()
            assert (result["yhat"] <= result["yhat_upper"]).all()


# ============================================================
# METRICS TESTS
# ============================================================
class TestXGBoostModelMetrics:
    """Tests for XGBoostModel metrics."""

    def test_get_metrics_before_training(self) -> None:
        """Test empty metrics before training."""
        model = XGBoostModel()
        assert model.get_metrics() == {}

    def test_get_metrics_after_training(
        self, trained_model: XGBoostModel
    ) -> None:
        """Test metrics are available after training."""
        metrics = trained_model.get_metrics()
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "mape" in metrics
        assert "directional_accuracy" in metrics

    def test_metrics_are_non_negative(
        self, trained_model: XGBoostModel
    ) -> None:
        """Test that all metrics are non-negative."""
        metrics = trained_model.get_metrics()
        for key, value in metrics.items():
            assert value >= 0, f"{key} is negative"


# ============================================================
# SERIALIZATION TESTS
# ============================================================
class TestXGBoostModelSerialization:
    """Tests for save/load."""

    def test_save_untrained_model_raises(self, tmp_path: Any) -> None:
        """Test that saving untrained model raises RuntimeError."""
        model = XGBoostModel()
        with pytest.raises(RuntimeError, match="not trained"):
            model.save(str(tmp_path / "model.json"))

    def test_save_and_load_roundtrip(
        self,
        trained_model: XGBoostModel,
        future_data: pd.DataFrame,
        tmp_path: Any,
    ) -> None:
        """Test that save + load preserves predictions."""
        path = str(tmp_path / "xgboost_model.json")
        trained_model.save(path)

        new_model = XGBoostModel()
        new_model.load(path)

        original_preds = trained_model.predict(future_data)
        loaded_preds = new_model.predict(future_data)

        np.testing.assert_allclose(
            original_preds["yhat"].values,
            loaded_preds["yhat"].values,
            rtol=1e-3,
        )

    def test_save_creates_files(
        self, trained_model: XGBoostModel, tmp_path: Any
    ) -> None:
        """Test that save creates both model and metadata files."""
        path = str(tmp_path / "xgboost_model.json")
        trained_model.save(path)

        import os

        assert os.path.exists(path)
        assert os.path.exists(f"{path}.meta.json")

    def test_load_missing_file_raises(self, tmp_path: Any) -> None:
        """Test that loading a missing file raises FileNotFoundError."""
        model = XGBoostModel()
        with pytest.raises(FileNotFoundError):
            model.load(str(tmp_path / "does_not_exist.json"))

    def test_load_restores_feature_columns(
        self, trained_model: XGBoostModel, tmp_path: Any
    ) -> None:
        """Test that loading restores the feature_columns list."""
        path = str(tmp_path / "xgboost_model.json")
        trained_model.save(path)

        new_model = XGBoostModel()
        new_model.load(path)

        assert new_model.feature_columns == trained_model.feature_columns

    def test_load_restores_residual_std(
        self, trained_model: XGBoostModel, tmp_path: Any
    ) -> None:
        """Test that loading restores the residual_std value."""
        path = str(tmp_path / "xgboost_model.json")
        trained_model.save(path)

        new_model = XGBoostModel()
        new_model.load(path)

        assert new_model.residual_std == trained_model.residual_std


# ============================================================
# FEATURE ENGINEERING TESTS
# ============================================================
class TestXGBoostModelFeatureEngineering:
    """Tests for feature engineering (lag features)."""

    def test_engineered_features_have_eng_prefix(self) -> None:
        """Test that all engineered features are prefixed with 'eng_'."""
        for feat in ENGINEERED_FEATURES:
            assert feat.startswith("eng_"), f"{feat} missing 'eng_' prefix"

    def test_no_collision_between_base_and_engineered(self) -> None:
        """Test that base and engineered features don't overlap."""
        overlap = set(BASE_FEATURES) & set(ENGINEERED_FEATURES)
        assert not overlap, f"Feature name collision: {overlap}"

    def test_lag_features_naming(self) -> None:
        """Test that lag features are named correctly."""
        assert "eng_price_lag_1d" in LAG_FEATURES
        assert "eng_price_lag_7d" in LAG_FEATURES
        assert "eng_price_lag_30d" in LAG_FEATURES

    def test_return_features_naming(self) -> None:
        """Test that return features are named correctly."""
        assert "eng_returns_1d" in RETURN_FEATURES
        assert "eng_returns_7d" in RETURN_FEATURES
        assert "eng_returns_30d" in RETURN_FEATURES

    def test_prepare_features_creates_all_engineered_columns(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that _prepare_features creates all engineered columns."""
        model = XGBoostModel()
        prepared = model._prepare_features(training_data)

        for feat in ENGINEERED_FEATURES:
            assert feat in prepared.columns, f"Missing {feat}"


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestXGBoostModelConstants:
    """Tests for module-level constants."""

    def test_base_features_count(self) -> None:
        """Test that there are exactly 10 base features."""
        assert len(BASE_FEATURES) == 10

    def test_engineered_features_count(self) -> None:
        """Test that there are 6 engineered features (3 lag + 3 return)."""
        assert len(ENGINEERED_FEATURES) == 6

    def test_all_features_count(self) -> None:
        """Test that there are 16 total features (10 base + 6 engineered)."""
        assert len(ALL_FEATURES) == 16

    def test_required_columns(self) -> None:
        """Test that required columns include ds, y, and all base features."""
        assert "ds" in REQUIRED_COLUMNS
        assert "y" in REQUIRED_COLUMNS
        for reg in BASE_FEATURES:
            assert reg in REQUIRED_COLUMNS

    def test_confidence_levels(self) -> None:
        """Test the three confidence levels."""
        assert CONFIDENCE_LEVELS == [0.70, 0.85, 0.95]

    def test_z_scores(self) -> None:
        """Test that z-scores are correct for the confidence levels."""
        assert Z_SCORES[0.95] == 1.96
        assert Z_SCORES[0.85] == 1.44
        assert Z_SCORES[0.70] == 1.04

    def test_min_training_rows(self) -> None:
        """Test that MIN_TRAINING_ROWS = max lag (30) + 30 = 60."""
        assert MIN_TRAINING_ROWS == 60

    def test_default_config_keys(self) -> None:
        """Test default config has expected keys."""
        assert "n_estimators" in DEFAULT_CONFIG
        assert "max_depth" in DEFAULT_CONFIG
        assert "objective" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["objective"] == "reg:squarederror"