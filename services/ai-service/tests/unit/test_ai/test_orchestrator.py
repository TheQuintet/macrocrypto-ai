"""Unit tests for the RetrainingOrchestrator.

These tests verify the orchestrator's behavior via fake models and
fake dependencies. The orchestrator is model-agnostic — it only
depends on the ForecastModel interface.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pandas as pd
import pytest

from app.ai import ForecastModel, RetrainResult, RetrainingOrchestrator


# ============================================================
# FIXTURES
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
        }
    )


class FakeModel(ForecastModel):
    """Fake model for testing the orchestrator."""

    def __init__(
        self,
        name: str = "fake",
        should_fail: bool = False,
        metrics: Optional[Dict[str, float]] = None,
    ) -> None:
        """Initialize the fake model."""
        super().__init__()
        self._name = name
        self._should_fail = should_fail
        self._metrics = metrics or {
            "mae": 0.05,
            "rmse": 0.08,
            "mape": 7.2,
            "directional_accuracy": 62.5,
        }
        self.train_called = False
        self.save_called = False
        self.train_warm_start = False

    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        """Train the fake model."""
        self.train_called = True
        self.train_warm_start = warm_start

        if self._should_fail:
            raise RuntimeError(f"Fake failure for {self._name}")

        self.is_trained = True
        self.metrics = self._metrics
        return self._metrics

    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        """Predict using the fake model."""
        return pd.DataFrame(
            {
                "ds": future_data["ds"],
                "yhat": [60000.0] * len(future_data),
                "yhat_lower": [59000.0] * len(future_data),
                "yhat_upper": [61000.0] * len(future_data),
            }
        )

    def get_metrics(self) -> Dict[str, float]:
        """Return metrics."""
        return self.metrics

    def get_name(self) -> str:
        """Return model name."""
        return self._name

    def get_version(self) -> str:
        """Return model version."""
        return self.version

    def save(self, path: str) -> None:
        """Save the fake model."""
        self.save_called = True

    def load(self, path: str) -> None:
        """Load the fake model."""
        self.is_trained = True


@pytest.fixture
def fake_mlflow_tracker() -> MagicMock:
    """Create a fake MLflow tracker."""
    tracker = MagicMock()
    tracker.log_metrics = MagicMock()
    return tracker


@pytest.fixture
def fake_event_publisher() -> MagicMock:
    """Create a fake event publisher."""
    publisher = MagicMock()
    publisher.publish = MagicMock()
    return publisher


# ============================================================
# INITIALIZATION TESTS
# ============================================================
class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""

    def test_initialization_with_single_model(self) -> None:
        """Test orchestrator with one model."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        assert orchestrator.get_registered_models() == ["model1"]
        assert orchestrator.get_last_retrain_time() is None

    def test_initialization_with_multiple_models(self) -> None:
        """Test orchestrator with multiple models."""
        models = {
            "model1": FakeModel(name="model1"),
            "model2": FakeModel(name="model2"),
        }
        orchestrator = RetrainingOrchestrator(models=models)

        assert sorted(orchestrator.get_registered_models()) == [
            "model1",
            "model2",
        ]

    def test_initialization_with_empty_models_raises(self) -> None:
        """Test that empty models raises ValueError."""
        with pytest.raises(ValueError, match="At least one model"):
            RetrainingOrchestrator(models={})

    def test_initialization_with_optional_dependencies(self) -> None:
        """Test orchestrator with MLflow tracker and event publisher."""
        model = FakeModel(name="model1")
        tracker = MagicMock()
        publisher = MagicMock()

        orchestrator = RetrainingOrchestrator(
            models={"model1": model},
            mlflow_tracker=tracker,
            event_publisher=publisher,
            model_save_dir="/tmp/models",
        )

        assert orchestrator.mlflow_tracker is tracker
        assert orchestrator.event_publisher is publisher
        assert orchestrator.model_save_dir == "/tmp/models"


# ============================================================
# RETRAIN ALL TESTS
# ============================================================
class TestRetrainAll:
    """Tests for retrain_all()."""

    def test_retrain_all_success(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test retraining all models successfully."""
        model1 = FakeModel(name="model1")
        model2 = FakeModel(name="model2")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model1, "model2": model2}
        )

        results = orchestrator.retrain_all(sample_training_data)

        assert len(results) == 2
        assert results["model1"]["status"] == "success"
        assert results["model2"]["status"] == "success"
        assert model1.train_called is True
        assert model2.train_called is True
        assert model1.save_called is True
        assert model2.save_called is True

    def test_retrain_all_with_one_failure(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test that one failure doesn't stop other models."""
        model1 = FakeModel(name="model1")
        model2 = FakeModel(name="model2", should_fail=True)
        model3 = FakeModel(name="model3")

        orchestrator = RetrainingOrchestrator(
            models={
                "model1": model1,
                "model2": model2,
                "model3": model3,
            }
        )

        results = orchestrator.retrain_all(sample_training_data)

        assert len(results) == 3
        assert results["model1"]["status"] == "success"
        assert results["model2"]["status"] == "failed"
        assert results["model3"]["status"] == "success"

    def test_retrain_all_with_empty_data_raises(self) -> None:
        """Test that empty data raises ValueError."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        with pytest.raises(ValueError, match="Training data cannot be empty"):
            orchestrator.retrain_all(pd.DataFrame())

    def test_retrain_all_updates_last_retrain_time(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test that last_retrain_time is updated."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        assert orchestrator.get_last_retrain_time() is None

        orchestrator.retrain_all(sample_training_data)

        assert orchestrator.get_last_retrain_time() is not None

    def test_retrain_all_tracks_history(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test that retrain history is tracked."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        orchestrator.retrain_all(sample_training_data)
        orchestrator.retrain_all(sample_training_data)

        history = orchestrator.get_retrain_history()
        assert len(history) == 2

    def test_retrain_all_with_warm_start(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test that warm_start is passed to models."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        orchestrator.retrain_all(sample_training_data, warm_start=True)

        assert model.train_warm_start is True


# ============================================================
# RETRAIN SINGLE TESTS
# ============================================================
class TestRetrainModel:
    """Tests for retrain_model()."""

    def test_retrain_single_model(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test retraining a single model."""
        model1 = FakeModel(name="model1")
        model2 = FakeModel(name="model2")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model1, "model2": model2}
        )

        result = orchestrator.retrain_model(
            "model1", sample_training_data
        )

        assert result["status"] == "success"
        assert model1.train_called is True
        assert model2.train_called is False  # Not retrained

    def test_retrain_unknown_model_raises(
        self, sample_training_data: pd.DataFrame
    ) -> None:
        """Test that unknown model raises KeyError."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        with pytest.raises(KeyError, match="not registered"):
            orchestrator.retrain_model("unknown", sample_training_data)


# ============================================================
# MLFLOW LOGGING TESTS
# ============================================================
class TestMLflowLogging:
    """Tests for MLflow logging."""

    def test_mlflow_logs_metrics_on_success(
        self,
        sample_training_data: pd.DataFrame,
        fake_mlflow_tracker: MagicMock,
    ) -> None:
        """Test that MLflow logs metrics on success."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model},
            mlflow_tracker=fake_mlflow_tracker,
        )

        orchestrator.retrain_all(sample_training_data)

        fake_mlflow_tracker.log_metrics.assert_called_once()
        call_args = fake_mlflow_tracker.log_metrics.call_args
        assert call_args[0][0] == "model1"

    def test_mlflow_not_logged_on_failure(
        self,
        sample_training_data: pd.DataFrame,
        fake_mlflow_tracker: MagicMock,
    ) -> None:
        """Test that MLflow is not logged when training fails."""
        model = FakeModel(name="model1", should_fail=True)
        orchestrator = RetrainingOrchestrator(
            models={"model1": model},
            mlflow_tracker=fake_mlflow_tracker,
        )

        orchestrator.retrain_all(sample_training_data)

        fake_mlflow_tracker.log_metrics.assert_not_called()

    def test_mlflow_failure_does_not_stop_orchestrator(
        self,
        sample_training_data: pd.DataFrame,
        fake_mlflow_tracker: MagicMock,
    ) -> None:
        """Test that MLflow failure doesn't stop the orchestrator."""
        fake_mlflow_tracker.log_metrics.side_effect = RuntimeError(
            "MLflow down"
        )
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model},
            mlflow_tracker=fake_mlflow_tracker,
        )

        results = orchestrator.retrain_all(sample_training_data)

        assert results["model1"]["status"] == "success"


# ============================================================
# EVENT PUBLISHING TESTS
# ============================================================
class TestEventPublishing:
    """Tests for event publishing."""

    def test_event_published_on_success(
        self,
        sample_training_data: pd.DataFrame,
        fake_event_publisher: MagicMock,
    ) -> None:
        """Test that ModelsRetrained event is published."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model},
            event_publisher=fake_event_publisher,
        )

        orchestrator.retrain_all(sample_training_data)

        fake_event_publisher.publish.assert_called_once()
        call_args = fake_event_publisher.publish.call_args
        event = call_args[0][0]
        assert event["event_type"] == "ModelsRetrained"
        assert event["source"] == "ai-service"
        assert "model1" in event["data"]["models"]

    def test_event_publisher_failure_does_not_stop(
        self,
        sample_training_data: pd.DataFrame,
        fake_event_publisher: MagicMock,
    ) -> None:
        """Test that event publisher failure doesn't stop orchestrator."""
        fake_event_publisher.publish.side_effect = RuntimeError(
            "RabbitMQ down"
        )
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model},
            event_publisher=fake_event_publisher,
        )

        results = orchestrator.retrain_all(sample_training_data)

        assert results["model1"]["status"] == "success"


# ============================================================
# MODEL REGISTRATION TESTS
# ============================================================
class TestModelRegistration:
    """Tests for register_model() and unregister_model()."""

    def test_register_new_model(self) -> None:
        """Test registering a new model."""
        model1 = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model1})

        model2 = FakeModel(name="model2")
        orchestrator.register_model("model2", model2)

        assert "model2" in orchestrator.get_registered_models()

    def test_register_duplicate_raises(self) -> None:
        """Test that registering a duplicate model raises."""
        model1 = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model1})

        with pytest.raises(ValueError, match="already registered"):
            orchestrator.register_model("model1", FakeModel())

    def test_unregister_model(self) -> None:
        """Test unregistering a model."""
        model1 = FakeModel(name="model1")
        model2 = FakeModel(name="model2")
        orchestrator = RetrainingOrchestrator(
            models={"model1": model1, "model2": model2}
        )

        orchestrator.unregister_model("model1")

        assert "model1" not in orchestrator.get_registered_models()
        assert "model2" in orchestrator.get_registered_models()

    def test_unregister_unknown_raises(self) -> None:
        """Test that unregistering unknown model raises."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        with pytest.raises(KeyError, match="not registered"):
            orchestrator.unregister_model("unknown")


# ============================================================
# RETRAIN RESULT TESTS
# ============================================================
class TestRetrainResult:
    """Tests for RetrainResult class."""

    def test_retrain_result_to_dict(self) -> None:
        """Test RetrainResult.to_dict()."""
        result = RetrainResult(
            model_name="model1",
            status="success",
            metrics={"mae": 0.05},
            duration_seconds=1.5,
        )

        d = result.to_dict()
        assert d["model_name"] == "model1"
        assert d["status"] == "success"
        assert d["metrics"] == {"mae": 0.05}
        assert d["duration_seconds"] == 1.5
        assert d["error"] is None

    def test_retrain_result_repr(self) -> None:
        """Test RetrainResult.__repr__()."""
        result = RetrainResult(
            model_name="model1", status="success"
        )
        assert "model1" in repr(result)
        assert "success" in repr(result)


# ============================================================
# REPR TEST
# ============================================================
class TestOrchestratorRepr:
    """Tests for orchestrator __repr__."""

    def test_repr_format(self) -> None:
        """Test __repr__ format."""
        model = FakeModel(name="model1")
        orchestrator = RetrainingOrchestrator(models={"model1": model})

        repr_str = repr(orchestrator)

        assert "RetrainingOrchestrator" in repr_str
        assert "model1" in repr_str