"""Unit tests for the ForecastModel interface.

These tests verify that the interface contract is correctly defined
and that subclasses must implement all abstract methods.
"""

from typing import Any, Dict, Optional

import pandas as pd
import pytest

from app.ai import ForecastModel


# ============================================================
# TEST FIXTURES
# ============================================================
@pytest.fixture
def sample_training_data() -> pd.DataFrame:
    """Create sample training data."""
    return pd.DataFrame(
        {
            "ds": pd.date_range("2024-01-01", periods=100, freq="D"),
            "y": [50000 + i * 100 for i in range(100)],
            "cpi": [3.2] * 100,
            "interest_rate": [4.5] * 100,
            "m2_growth": [2.8] * 100,
            "dxy": [102.5] * 100,
            "treasury_yield": [4.2] * 100,
            "volume": [25_000_000_000] * 100,
            "volatility": [0.15] * 100,
            "dominance": [52.5] * 100,
            "active_addresses": [850_000] * 100,
            "price_lag_7d": [50_000] * 100,
        }
    )


@pytest.fixture
def sample_future_data() -> pd.DataFrame:
    """Create sample future data for prediction."""
    return pd.DataFrame(
        {
            "ds": pd.date_range("2024-04-10", periods=7, freq="D"),
            "cpi": [3.2] * 7,
            "interest_rate": [4.5] * 7,
            "m2_growth": [2.8] * 7,
            "dxy": [102.5] * 7,
            "treasury_yield": [4.2] * 7,
            "volume": [25_000_000_000] * 7,
            "volatility": [0.15] * 7,
            "dominance": [52.5] * 7,
            "active_addresses": [850_000] * 7,
            "price_lag_7d": [50_000] * 7,
        }
    )


# ============================================================
# INTERFACE CONTRACT TESTS
# ============================================================
class TestForecastModelInterface:
    """Tests for the ForecastModel abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that ForecastModel cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ForecastModel()  # type: ignore

    def test_abstract_methods_are_defined(self) -> None:
        """Test that all required abstract methods exist."""
        abstract_methods = ForecastModel.__abstractmethods__

        expected_methods = {
            "train",
            "predict",
            "get_metrics",
            "get_name",
            "get_version",
            "save",
            "load",
        }

        assert abstract_methods == expected_methods

    def test_subclass_must_implement_all_methods(self) -> None:
        """Test that a subclass missing methods cannot be instantiated."""

        class IncompleteModel(ForecastModel):
            """Incomplete subclass — only implements one method."""

            def train(
                self,
                data: pd.DataFrame,
                warm_start: bool = False,
                previous_model_path: Optional[str] = None,
            ) -> Dict[str, float]:
                return {}

        with pytest.raises(TypeError):
            IncompleteModel()  # type: ignore

    def test_complete_subclass_can_be_instantiated(self) -> None:
        """Test that a complete subclass can be instantiated."""

        class CompleteModel(ForecastModel):
            """Complete subclass implementing all abstract methods."""

            def train(
                self,
                data: pd.DataFrame,
                warm_start: bool = False,
                previous_model_path: Optional[str] = None,
            ) -> Dict[str, float]:
                self.is_trained = True
                self.metrics = {"mae": 0.05, "rmse": 0.08}
                return self.metrics

            def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
                return pd.DataFrame(
                    {
                        "ds": future_data["ds"],
                        "yhat": [60000.0] * len(future_data),
                        "yhat_lower": [59000.0] * len(future_data),
                        "yhat_upper": [61000.0] * len(future_data),
                    }
                )

            def get_metrics(self) -> Dict[str, float]:
                return self.metrics

            def get_name(self) -> str:
                return "complete"

            def get_version(self) -> str:
                return self.version

            def save(self, path: str) -> None:
                pass

            def load(self, path: str) -> None:
                self.is_trained = True

        model = CompleteModel()
        assert model.get_name() == "complete"
        assert model.get_version() == "1.0.0"
        assert model.is_model_trained() is False


# ============================================================
# BEHAVIORAL TESTS (using a fake implementation)
# ============================================================
class TestForecastModelBehavior:
    """Tests for ForecastModel behavior via a fake implementation."""

    class FakeModel(ForecastModel):
        """Fake model for testing."""

        def train(
            self,
            data: pd.DataFrame,
            warm_start: bool = False,
            previous_model_path: Optional[str] = None,
        ) -> Dict[str, float]:
            self.is_trained = True
            self.metrics = {
                "mae": 0.05,
                "rmse": 0.08,
                "mape": 7.2,
                "directional_accuracy": 62.5,
            }
            return self.metrics

        def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
            if not self.is_trained:
                raise RuntimeError("Model not trained")
            return pd.DataFrame(
                {
                    "ds": future_data["ds"],
                    "yhat": [60000.0] * len(future_data),
                    "yhat_lower": [59000.0] * len(future_data),
                    "yhat_upper": [61000.0] * len(future_data),
                }
            )

        def get_metrics(self) -> Dict[str, float]:
            return self.metrics

        def get_name(self) -> str:
            return "fake"

        def get_version(self) -> str:
            return self.version

        def save(self, path: str) -> None:
            if not self.is_trained:
                raise RuntimeError("Cannot save untrained model")

        def load(self, path: str) -> None:
            self.is_trained = True

    def test_initial_state_is_untrained(self) -> None:
        """Test that a new model is not trained."""
        model = self.FakeModel()
        assert model.is_model_trained() is False
        assert model.get_metrics() == {}

    def test_train_sets_trained_state(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test that training sets the trained state."""
        model = self.FakeModel()
        metrics = model.train(sample_training_data)

        assert model.is_model_trained() is True
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "mape" in metrics

    def test_predict_before_training_raises(
        self, sample_future_data: pd.DataFrame
    ) -> None:
        """Test that prediction before training raises an error."""
        model = self.FakeModel()

        with pytest.raises(RuntimeError):
            model.predict(sample_future_data)

    def test_predict_after_training(
        self,
        sample_training_data: pd.DataFrame,
        sample_future_data: pd.DataFrame,
    ) -> None:
        """Test that prediction works after training."""
        model = self.FakeModel()
        model.train(sample_training_data)

        predictions = model.predict(sample_future_data)

        assert len(predictions) == len(sample_future_data)
        assert "ds" in predictions.columns
        assert "yhat" in predictions.columns
        assert "yhat_lower" in predictions.columns
        assert "yhat_upper" in predictions.columns

    def test_save_untrained_model_raises(self) -> None:
        """Test that saving an untrained model raises an error."""
        model = self.FakeModel()

        with pytest.raises(RuntimeError):
            model.save("/tmp/fake_model.pkl")

    def test_load_sets_trained_state(self) -> None:
        """Test that loading a model sets the trained state."""
        model = self.FakeModel()
        model.load("/tmp/fake_model.pkl")

        assert model.is_model_trained() is True

    def test_repr_format(self) -> None:
        """Test the __repr__ format."""
        model = self.FakeModel()
        repr_str = repr(model)

        assert "FakeModel" in repr_str
        assert "name='fake'" in repr_str
        assert "version='1.0.0'" in repr_str
        assert "trained=False" in repr_str