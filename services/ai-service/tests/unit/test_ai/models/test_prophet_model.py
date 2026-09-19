"""Unit tests for the ProphetModel adapter.

These tests use real Prophet with small datasets. They are marked
with @pytest.mark.slow since Prophet training is not instant.
"""

from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from app.ai import ForecastModel, ProphetModel
from app.ai.models.prophet_model import (
    CONFIDENCE_LEVELS,
    DEFAULT_CONFIG,
    REGRESSORS,
    REQUIRED_COLUMNS,
)


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture(scope="module")
def training_data() -> pd.DataFrame:
    """Create a small training dataset for Prophet tests.

    Uses 60 days of synthetic data with a slight upward trend.
    """
    n = 60
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    np.random.seed(42)

    base_price = 50000
    trend = np.linspace(0, 5000, n)
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
def future_data() -> pd.DataFrame:
    """Create future data for predictions (7 days)."""
    n = 7
    dates = pd.date_range("2024-03-01", periods=n, freq="D")

    return pd.DataFrame(
        {
            "ds": dates,
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
def trained_model(training_data: pd.DataFrame) -> ProphetModel:
    """Return a trained ProphetModel (cached for the module)."""
    model = ProphetModel()
    model.train(training_data)
    return model


# ============================================================
# INITIALIZATION TESTS
# ============================================================
class TestProphetModelInitialization:
    """Tests for ProphetModel initialization."""

    def test_default_strategy_is_fresh(self) -> None:
        """Test that default strategy is 'fresh'."""
        model = ProphetModel()
        assert model.strategy == "fresh"

    def test_initialization_with_warm_strategy(self) -> None:
        """Test initialization with 'warm' strategy."""
        model = ProphetModel(strategy="warm")
        assert model.strategy == "warm"

    def test_initialization_with_invalid_strategy_raises(self) -> None:
        """Test that invalid strategy raises ValueError."""
        with pytest.raises(ValueError, match="Invalid strategy"):
            ProphetModel(strategy="invalid")

    def test_initialization_with_config(self) -> None:
        """Test that config overrides defaults."""
        model = ProphetModel(config={"changepoint_prior_scale": 0.1})
        assert model.config["changepoint_prior_scale"] == 0.1
        # Other defaults should still be present
        assert model.config["seasonality_mode"] == "multiplicative"

    def test_is_forecast_model_subclass(self) -> None:
        """Test that ProphetModel is a ForecastModel."""
        model = ProphetModel()
        assert isinstance(model, ForecastModel)

    def test_get_name(self) -> None:
        """Test that get_name returns 'prophet'."""
        model = ProphetModel()
        assert model.get_name() == "prophet"

    def test_get_version(self) -> None:
        """Test that get_version returns a string."""
        model = ProphetModel()
        assert model.get_version() == "1.0.0"

    def test_initial_state_is_untrained(self) -> None:
        """Test that a new model is not trained."""
        model = ProphetModel()
        assert model.is_trained is False
        assert model.get_metrics() == {}

    def test_repr(self) -> None:
        """Test __repr__ format."""
        model = ProphetModel()
        repr_str = repr(model)
        assert "ProphetModel" in repr_str
        assert "strategy='fresh'" in repr_str
        assert "trained=False" in repr_str


# ============================================================
# TRAINING TESTS
# ============================================================
@pytest.mark.slow
class TestProphetModelTrain:
    """Tests for ProphetModel.train()."""

    def test_train_fresh(self, training_data: pd.DataFrame) -> None:
        """Test training with fresh strategy."""
        model = ProphetModel()
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
        model = ProphetModel()
        metrics = model.train(training_data)

        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} is not a float"

    def test_train_with_empty_data_raises(self) -> None:
        """Test that empty data raises ValueError."""
        model = ProphetModel()
        with pytest.raises(ValueError, match="cannot be empty"):
            model.train(pd.DataFrame())

    def test_train_with_missing_columns_raises(self) -> None:
        """Test that missing columns raises ValueError."""
        model = ProphetModel()
        incomplete = pd.DataFrame(
            {"ds": pd.date_range("2024-01-01", periods=50, freq="D"),
             "y": [50000] * 50}
        )
        with pytest.raises(ValueError, match="missing required columns"):
            model.train(incomplete)

    def test_train_with_insufficient_data_raises(self) -> None:
        """Test that less than 30 rows raises ValueError."""
        model = ProphetModel()
        small_data = pd.DataFrame(
            {
                "ds": pd.date_range("2024-01-01", periods=10, freq="D"),
                "y": [50000] * 10,
                **{reg: [1.0] * 10 for reg in REGRESSORS},
            }
        )
        with pytest.raises(ValueError, match="at least 30 rows"):
            model.train(small_data)

    def test_train_with_warm_start_flag(
        self, training_data: pd.DataFrame
    ) -> None:
        """Test that warm_start flag is accepted (falls back to fresh in M2.1)."""
        model = ProphetModel()
        metrics = model.train(training_data, warm_start=True)

        # Should still succeed with fresh training
        assert model.is_trained is True
        assert "mae" in metrics


# ============================================================
# PREDICTION TESTS
# ============================================================
@pytest.mark.slow
class TestProphetModelPredict:
    """Tests for ProphetModel.predict()."""

    def test_predict_before_training_raises(self) -> None:
        """Test that prediction before training raises RuntimeError."""
        model = ProphetModel()
        future = pd.DataFrame(
            {"ds": [pd.Timestamp("2024-04-01")], **{r: [1.0] for r in REGRESSORS}}
        )
        with pytest.raises(RuntimeError, match="not trained"):
            model.predict(future)

    def test_predict_returns_dataframe(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that predict returns a DataFrame."""
        result = trained_model.predict(future_data)
        assert isinstance(result, pd.DataFrame)

    def test_predict_output_columns(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that output has the correct columns."""
        result = trained_model.predict(future_data)
        expected_columns = {"ds", "yhat", "yhat_lower", "yhat_upper"}
        assert set(result.columns) == expected_columns

    def test_predict_row_count(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that output has one row per input row."""
        result = trained_model.predict(future_data)
        assert len(result) == len(future_data)

    def test_predict_bounds_are_ordered(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that yhat_lower <= yhat <= yhat_upper."""
        result = trained_model.predict(future_data)
        assert (result["yhat_lower"] <= result["yhat"]).all()
        assert (result["yhat"] <= result["yhat_upper"]).all()


# ============================================================
# CONFIDENCE INTERVAL TESTS
# ============================================================
@pytest.mark.slow
class TestProphetModelConfidence:
    """Tests for confidence interval scaling.

    Note: Prophet's uncertainty bounds are computed via Monte Carlo
    sampling, so yhat_lower and yhat_upper are non-deterministic
    across separate predict() calls. Only yhat is deterministic.
    """

    def test_predict_with_95_confidence(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test 95% confidence (native Prophet)."""
        result = trained_model.predict_with_confidence(future_data, 0.95)
        base = trained_model.predict(future_data)

        # yhat is deterministic across calls
        np.testing.assert_allclose(
            result["yhat"].values,
            base["yhat"].values,
            rtol=1e-5,
        )

        # Bounds exist and are ordered
        assert (result["yhat_lower"] <= result["yhat"]).all()
        assert (result["yhat"] <= result["yhat_upper"]).all()

    def test_predict_with_85_confidence(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test 85% confidence (narrower intervals)."""
        result_95 = trained_model.predict_with_confidence(future_data, 0.95)
        result_85 = trained_model.predict_with_confidence(future_data, 0.85)

        # Compare margins within the same call context.
        # Note: Since bounds are non-deterministic, we verify that
        # the 85% interval is narrower on average, not per-row.
        margin_95 = (result_95["yhat_upper"] - result_95["yhat_lower"]).mean()
        margin_85 = (result_85["yhat_upper"] - result_85["yhat_lower"]).mean()

        assert margin_85 < margin_95

    def test_predict_with_70_confidence(
        self,
        trained_model: ProphetModel,
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
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
    ) -> None:
        """Test invalid confidence level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence_level"):
            trained_model.predict_with_confidence(future_data, 0.50)

    def test_confidence_intervals_are_ordered(
        self,
        trained_model: ProphetModel,
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
@pytest.mark.slow
class TestProphetModelMetrics:
    """Tests for ProphetModel metrics."""

    def test_get_metrics_before_training(self) -> None:
        """Test empty metrics before training."""
        model = ProphetModel()
        assert model.get_metrics() == {}

    def test_get_metrics_after_training(
        self,
        trained_model: ProphetModel,
    ) -> None:
        """Test metrics are available after training."""
        metrics = trained_model.get_metrics()
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "mape" in metrics
        assert "directional_accuracy" in metrics

    def test_metrics_are_non_negative(
        self,
        trained_model: ProphetModel,
    ) -> None:
        """Test that all metrics are non-negative."""
        metrics = trained_model.get_metrics()
        for key, value in metrics.items():
            assert value >= 0, f"{key} is negative"


# ============================================================
# SERIALIZATION TESTS
# ============================================================
@pytest.mark.slow
class TestProphetModelSerialization:
    """Tests for save/load."""

    def test_save_untrained_model_raises(self, tmp_path: Any) -> None:
        """Test that saving untrained model raises RuntimeError."""
        model = ProphetModel()
        with pytest.raises(RuntimeError, match="not trained"):
            model.save(str(tmp_path / "model.json"))

    def test_save_and_load_roundtrip(
        self,
        trained_model: ProphetModel,
        future_data: pd.DataFrame,
        tmp_path: Any,
    ) -> None:
        """Test that save + load preserves predictions."""
        path = str(tmp_path / "prophet_model.json")

        # Save
        trained_model.save(path)

        # Load into new instance
        new_model = ProphetModel()
        new_model.load(path)

        # Compare predictions
        original_preds = trained_model.predict(future_data)
        loaded_preds = new_model.predict(future_data)

        np.testing.assert_allclose(
            original_preds["yhat"].values,
            loaded_preds["yhat"].values,
            rtol=1e-5,
        )

    def test_save_creates_file(
        self,
        trained_model: ProphetModel,
        tmp_path: Any,
    ) -> None:
        """Test that save creates a file on disk."""
        import os

        path = str(tmp_path / "prophet_model.json")
        trained_model.save(path)
        assert os.path.exists(path)

    def test_load_missing_file_raises(self, tmp_path: Any) -> None:
        """Test that loading a missing file raises FileNotFoundError."""
        model = ProphetModel()
        with pytest.raises(FileNotFoundError):
            model.load(str(tmp_path / "does_not_exist.json"))


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestProphetModelConstants:
    """Tests for module-level constants."""

    def test_regressors_count(self) -> None:
        """Test that there are exactly 10 regressors."""
        assert len(REGRESSORS) == 10

    def test_required_columns(self) -> None:
        """Test that required columns include ds, y, and all regressors."""
        assert "ds" in REQUIRED_COLUMNS
        assert "y" in REQUIRED_COLUMNS
        for reg in REGRESSORS:
            assert reg in REQUIRED_COLUMNS

    def test_confidence_levels(self) -> None:
        """Test the three confidence levels."""
        assert CONFIDENCE_LEVELS == [0.70, 0.85, 0.95]

    def test_default_config_keys(self) -> None:
        """Test default config has expected keys."""
        assert "changepoint_prior_scale" in DEFAULT_CONFIG
        assert "seasonality_mode" in DEFAULT_CONFIG
        assert DEFAULT_CONFIG["seasonality_mode"] == "multiplicative"