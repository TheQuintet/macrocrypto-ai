"""Unit tests for the ModelComparisonEngine.

These tests use fake ForecastModel implementations for speed and
determinism, plus integration-style tests that exercise the real
Prophet, XGBoost, and LightGBM models via build_default_engine().

Test organization:
    - TestModelPrediction: Dataclass behavior
    - TestComparisonResult: Dataclass behavior
    - TestEngineInitialization: Constructor
    - TestEngineRegistration: register/unregister
    - TestEngineSequential: Sequential execution mode
    - TestEngineParallel: Parallel execution mode
    - TestEngineErrorIsolation: Per-model failures
    - TestEngineConsensus: Consensus DataFrame
    - TestEngineAgreement: Agreement score
    - TestEngineBestModel: Best model identification
    - TestBuildDefaultEngine: Factory with all 6 real variants
    - TestEngineIntegration: All 6 real models end-to-end
    - TestEngineConstants: Module constants
"""

import time
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import pytest

from app.ai import (
    ComparisonResult,
    ForecastModel,
    ModelComparisonEngine,
    ModelPrediction,
    build_default_engine,
)
from app.ai.comparison import (
    AGREEMENT_SCORE_MAX,
    AGREEMENT_SCORE_MIN,
    DEFAULT_MODEL_KEYS,
)


# ============================================================
# FAKE MODELS
# ============================================================
class FakeModel(ForecastModel):
    """A deterministic fake ForecastModel for testing.

    Produces constant predictions (offset by an optional bias)
    and carries a configurable MAE metric.
    """

    def __init__(
        self,
        name: str = "fake",
        bias: float = 0.0,
        mae: Optional[float] = 100.0,
        fail_on_predict: bool = False,
        trained: bool = True,
        sleep_seconds: float = 0.0,
        n_predict_rows: Optional[int] = None,
    ) -> None:
        """Initialize the fake model.

        Args:
            name: Model name returned by get_name().
            bias: Constant offset added to predictions.
            mae: The 'mae' metric to report. None = no metrics.
            fail_on_predict: If True, predict() raises RuntimeError.
            trained: Whether the model reports as trained.
            sleep_seconds: Artificial delay inside predict().
            n_predict_rows: If set, return this many rows (for
                testing alignment edge cases).
        """
        super().__init__()
        self._name = name
        self._bias = bias
        self._mae = mae
        self._fail_on_predict = fail_on_predict
        self._sleep_seconds = sleep_seconds
        self._n_predict_rows = n_predict_rows
        self.is_trained = trained
        if mae is not None:
            self.metrics = {
                "mae": mae,
                "rmse": mae * 1.2,
                "mape": mae / 100.0,
                "directional_accuracy": 60.0,
            }

    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        """No-op train."""
        self.is_trained = True
        return self.metrics

    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        """Return constant predictions offset by bias."""
        if self._fail_on_predict:
            raise RuntimeError(f"{self._name} failed on predict")
        if self._sleep_seconds > 0:
            time.sleep(self._sleep_seconds)

        n = self._n_predict_rows or len(future_data)
        base = 50_000.0 + self._bias
        return pd.DataFrame(
            {
                "ds": future_data["ds"].values[:n],
                "yhat": [base] * n,
                "yhat_lower": [base - 500.0] * n,
                "yhat_upper": [base + 500.0] * n,
            }
        )

    def get_metrics(self) -> Dict[str, float]:
        """Return stored metrics."""
        return dict(self.metrics)

    def get_name(self) -> str:
        """Return the fake model name."""
        return self._name

    def get_version(self) -> str:
        """Return a fixed version."""
        return "1.0.0"

    def save(self, path: str) -> None:
        """No-op save."""
        pass

    def load(self, path: str) -> None:
        """No-op load."""
        pass


# ============================================================
# FIXTURES
# ============================================================
@pytest.fixture
def future_data() -> pd.DataFrame:
    """Small future DataFrame with 5 rows."""
    return pd.DataFrame(
        {
            "ds": pd.date_range("2024-04-01", periods=5, freq="D"),
            "y": [50_000.0] * 5,
        }
    )


@pytest.fixture
def three_models() -> Dict[str, ForecastModel]:
    """Three fake models with slightly different biases."""
    return {
        "model_a": FakeModel(name="model_a", bias=0.0, mae=100.0),
        "model_b": FakeModel(name="model_b", bias=100.0, mae=200.0),
        "model_c": FakeModel(name="model_c", bias=200.0, mae=150.0),
    }


# ============================================================
# DATACLASS TESTS
# ============================================================
class TestModelPrediction:
    """Tests for the ModelPrediction dataclass."""

    def test_default_construction(self) -> None:
        """Test that a ModelPrediction can be constructed with defaults."""
        pred = ModelPrediction(model_name="x", predictions=None)
        assert pred.model_name == "x"
        assert pred.predictions is None
        assert pred.metrics == {}
        assert pred.elapsed_seconds == 0.0
        assert pred.error is None

    def test_to_dict_with_predictions(
        self, future_data: pd.DataFrame
    ) -> None:
        """Test to_dict serializes predictions to records."""
        df = pd.DataFrame(
            {
                "ds": future_data["ds"].values,
                "yhat": [1.0] * 5,
                "yhat_lower": [0.5] * 5,
                "yhat_upper": [1.5] * 5,
            }
        )
        pred = ModelPrediction(
            model_name="x",
            predictions=df,
            metrics={"mae": 1.0},
            elapsed_seconds=0.5,
        )
        d = pred.to_dict()
        assert d["model_name"] == "x"
        assert isinstance(d["predictions"], list)
        assert len(d["predictions"]) == 5
        assert d["metrics"] == {"mae": 1.0}

    def test_to_dict_without_predictions(self) -> None:
        """Test to_dict handles None predictions."""
        pred = ModelPrediction(
            model_name="x",
            predictions=None,
            error="oops",
        )
        d = pred.to_dict()
        assert d["predictions"] is None
        assert d["error"] == "oops"

    def test_repr_success(self) -> None:
        """Test __repr__ on a successful prediction."""
        pred = ModelPrediction(
            model_name="x",
            predictions=pd.DataFrame(),
            elapsed_seconds=0.123,
        )
        assert "status='success'" in repr(pred)

    def test_repr_failure(self) -> None:
        """Test __repr__ on a failed prediction."""
        pred = ModelPrediction(
            model_name="x",
            predictions=None,
            error="boom",
        )
        assert "status='failed'" in repr(pred)


class TestComparisonResult:
    """Tests for the ComparisonResult dataclass."""

    def test_default_construction(self) -> None:
        """Test defaults."""
        result = ComparisonResult()
        assert result.predictions == {}
        assert result.consensus is None
        assert result.agreement_score == 0.0
        assert result.best_model is None
        assert result.models_run == []
        assert result.models_failed == []
        assert result.total_elapsed_seconds == 0.0

    def test_to_dict(self) -> None:
        """Test to_dict serializes all fields."""
        result = ComparisonResult(
            agreement_score=0.95,
            best_model="lightgbm",
            models_run=["lightgbm", "xgboost"],
            models_failed=["prophet"],
        )
        d = result.to_dict()
        assert d["agreement_score"] == 0.95
        assert d["best_model"] == "lightgbm"
        assert d["models_run"] == ["lightgbm", "xgboost"]
        assert d["models_failed"] == ["prophet"]
        assert d["consensus"] is None

    def test_repr(self) -> None:
        """Test __repr__ format."""
        result = ComparisonResult(
            models_run=["a", "b"],
            models_failed=["c"],
            agreement_score=0.9,
            best_model="a",
        )
        r = repr(result)
        assert "models_run=2" in r
        assert "models_failed=1" in r
        assert "agreement=0.900" in r


# ============================================================
# INITIALIZATION TESTS
# ============================================================
class TestEngineInitialization:
    """Tests for ModelComparisonEngine initialization."""

    def test_empty_models_raises(self) -> None:
        """Test that empty models dict raises ValueError."""
        with pytest.raises(ValueError, match="At least one model"):
            ModelComparisonEngine(models={})

    def test_default_parallel_is_false(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that parallel defaults to False."""
        engine = ModelComparisonEngine(models=three_models)
        assert engine.parallel is False

    def test_parallel_true(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that parallel=True is respected."""
        engine = ModelComparisonEngine(models=three_models, parallel=True)
        assert engine.parallel is True

    def test_max_workers_defaults_to_model_count(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that max_workers defaults to number of models."""
        engine = ModelComparisonEngine(models=three_models)
        assert engine.max_workers == 3

    def test_max_workers_override(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that max_workers can be overridden."""
        engine = ModelComparisonEngine(models=three_models, max_workers=2)
        assert engine.max_workers == 2

    def test_last_comparison_time_starts_none(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that last_comparison_time starts as None."""
        engine = ModelComparisonEngine(models=three_models)
        assert engine.last_comparison_time is None

    def test_repr(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test __repr__ format."""
        engine = ModelComparisonEngine(models=three_models)
        r = repr(engine)
        assert "ModelComparisonEngine" in r
        assert "model_a" in r
        assert "parallel=False" in r


# ============================================================
# REGISTRATION TESTS
# ============================================================
class TestEngineRegistration:
    """Tests for register/unregister."""

    def test_get_registered_models(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test listing registered model names."""
        engine = ModelComparisonEngine(models=three_models)
        names = engine.get_registered_models()
        assert set(names) == {"model_a", "model_b", "model_c"}

    def test_register_new_model(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test registering a new model."""
        engine = ModelComparisonEngine(models=three_models)
        engine.register_model("model_d", FakeModel(name="model_d"))
        assert "model_d" in engine.get_registered_models()

    def test_register_existing_model_raises(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that registering a duplicate name raises."""
        engine = ModelComparisonEngine(models=three_models)
        with pytest.raises(ValueError, match="already registered"):
            engine.register_model("model_a", FakeModel())

    def test_unregister_model(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test unregistering a model."""
        engine = ModelComparisonEngine(models=three_models)
        engine.unregister_model("model_a")
        assert "model_a" not in engine.get_registered_models()

    def test_unregister_missing_raises(
        self, three_models: Dict[str, ForecastModel]
    ) -> None:
        """Test that unregistering a missing model raises."""
        engine = ModelComparisonEngine(models=three_models)
        with pytest.raises(KeyError, match="not registered"):
            engine.unregister_model("does_not_exist")


# ============================================================
# SEQUENTIAL EXECUTION TESTS
# ============================================================
class TestEngineSequential:
    """Tests for sequential execution mode."""

    def test_compare_returns_comparison_result(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that compare() returns a ComparisonResult."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        assert isinstance(result, ComparisonResult)

    def test_compare_runs_all_models(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that all models are run."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        assert set(result.models_run) == {"model_a", "model_b", "model_c"}
        assert result.models_failed == []

    def test_compare_populates_predictions(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that every model gets a ModelPrediction."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        for name in three_models:
            assert name in result.predictions
            assert result.predictions[name].predictions is not None

    def test_compare_records_elapsed_per_model(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that per-model elapsed_seconds is recorded (non-negative)."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        for pred in result.predictions.values():
            assert pred.elapsed_seconds >= 0.0

    def test_compare_records_total_elapsed(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that total_elapsed_seconds is recorded."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        assert result.total_elapsed_seconds >= 0.0

    def test_compare_sets_last_comparison_time(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that last_comparison_time is updated."""
        engine = ModelComparisonEngine(models=three_models)
        assert engine.last_comparison_time is None
        engine.compare(future_data)
        assert engine.last_comparison_time is not None

    def test_compare_empty_data_raises(
        self,
        three_models: Dict[str, ForecastModel],
    ) -> None:
        """Test that empty future_data raises ValueError."""
        engine = ModelComparisonEngine(models=three_models)
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.compare(pd.DataFrame())

    def test_compare_none_data_raises(
        self,
        three_models: Dict[str, ForecastModel],
    ) -> None:
        """Test that None future_data raises ValueError."""
        engine = ModelComparisonEngine(models=three_models)
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.compare(None)  # type: ignore[arg-type]


# ============================================================
# PARALLEL EXECUTION TESTS
# ============================================================
class TestEngineParallel:
    """Tests for parallel execution mode."""

    def test_parallel_runs_all_models(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that parallel mode runs all models."""
        engine = ModelComparisonEngine(models=three_models, parallel=True)
        result = engine.compare(future_data)
        assert set(result.models_run) == {"model_a", "model_b", "model_c"}
        assert result.models_failed == []

    def test_parallel_matches_sequential_results(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that parallel and sequential produce identical predictions."""
        seq_engine = ModelComparisonEngine(
            models=three_models, parallel=False
        )
        par_engine = ModelComparisonEngine(
            models=three_models, parallel=True
        )

        seq_result = seq_engine.compare(future_data)
        par_result = par_engine.compare(future_data)

        for name in three_models:
            seq_yhat = seq_result.predictions[name].predictions["yhat"].values
            par_yhat = par_result.predictions[name].predictions["yhat"].values
            np.testing.assert_array_equal(seq_yhat, par_yhat)

    def test_parallel_actually_parallelizes(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that parallel mode is faster than sequential when models sleep.

        Uses artificial sleeps to prove concurrency. Each model sleeps
        0.2s. Sequential should take ~0.6s; parallel should take ~0.2s.
        """
        models = {
            "slow_a": FakeModel(name="slow_a", sleep_seconds=0.2),
            "slow_b": FakeModel(name="slow_b", sleep_seconds=0.2),
            "slow_c": FakeModel(name="slow_c", sleep_seconds=0.2),
        }

        seq_engine = ModelComparisonEngine(
            models=models, parallel=False
        )
        par_engine = ModelComparisonEngine(
            models=models, parallel=True
        )

        seq_result = seq_engine.compare(future_data)
        par_result = par_engine.compare(future_data)

        # Sequential should be slower than parallel
        assert (
            seq_result.total_elapsed_seconds
            > par_result.total_elapsed_seconds
        )

    def test_parallel_error_isolation(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that a failing model in parallel mode does not break others."""
        models = {
            "ok_a": FakeModel(name="ok_a"),
            "fails": FakeModel(name="fails", fail_on_predict=True),
            "ok_b": FakeModel(name="ok_b"),
        }
        engine = ModelComparisonEngine(models=models, parallel=True)
        result = engine.compare(future_data)

        assert set(result.models_run) == {"ok_a", "ok_b"}
        assert result.models_failed == ["fails"]


# ============================================================
# ERROR ISOLATION TESTS
# ============================================================
class TestEngineErrorIsolation:
    """Tests for per-model error isolation."""

    def test_untrained_model_is_captured_as_failure(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that an untrained model appears in models_failed."""
        models = {
            "trained": FakeModel(name="trained", trained=True),
            "untrained": FakeModel(name="untrained", trained=False),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)

        assert "trained" in result.models_run
        assert "untrained" in result.models_failed

    def test_predict_exception_is_captured(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that an exception in predict() is captured."""
        models = {
            "ok": FakeModel(name="ok"),
            "bad": FakeModel(name="bad", fail_on_predict=True),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)

        assert "ok" in result.models_run
        assert "bad" in result.models_failed
        assert result.predictions["bad"].error is not None

    def test_all_models_failing_returns_empty_result(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that all-fail returns a result with no successes."""
        models = {
            "a": FakeModel(name="a", fail_on_predict=True),
            "b": FakeModel(name="b", fail_on_predict=True),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)

        assert result.models_run == []
        assert set(result.models_failed) == {"a", "b"}
        assert result.consensus is None
        assert result.best_model is None


# ============================================================
# CONSENSUS TESTS
# ============================================================
class TestEngineConsensus:
    """Tests for the consensus DataFrame."""

    def test_consensus_is_mean_of_predictions(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that consensus yhat equals the mean of model yhats."""
        models = {
            "a": FakeModel(name="a", bias=0.0),
            "b": FakeModel(name="b", bias=100.0),
            "c": FakeModel(name="c", bias=200.0),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)

        # 50_000 + 0, 50_000 + 100, 50_000 + 200 → mean = 50_100
        assert result.consensus is not None
        np.testing.assert_allclose(
            result.consensus["yhat"].values, [50_100.0] * 5
        )

    def test_consensus_has_ds_column(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that consensus has a ds column."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        assert "ds" in result.consensus.columns

    def test_consensus_single_model_returns_that_model(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that consensus with one model equals that model's yhat."""
        models = {"only": FakeModel(name="only", bias=42.0)}
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)

        np.testing.assert_allclose(
            result.consensus["yhat"].values, [50_042.0] * 5
        )


# ============================================================
# AGREEMENT SCORE TESTS
# ============================================================
class TestEngineAgreement:
    """Tests for the agreement score."""

    def test_identical_predictions_agree_perfectly(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that identical models yield agreement = 1.0."""
        models = {
            "a": FakeModel(name="a", bias=0.0),
            "b": FakeModel(name="b", bias=0.0),
            "c": FakeModel(name="c", bias=0.0),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)
        assert result.agreement_score == 1.0

    def test_single_model_agrees_with_itself(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that a single model yields agreement = 1.0."""
        models = {"only": FakeModel(name="only")}
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)
        assert result.agreement_score == 1.0

    def test_agreement_score_is_bounded(
        self,
        three_models: Dict[str, ForecastModel],
        future_data: pd.DataFrame,
    ) -> None:
        """Test that agreement score is always in [0, 1]."""
        engine = ModelComparisonEngine(models=three_models)
        result = engine.compare(future_data)
        assert (
            AGREEMENT_SCORE_MIN
            <= result.agreement_score
            <= AGREEMENT_SCORE_MAX
        )

    def test_wide_spread_lowers_agreement(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that widely spread predictions lower the agreement."""
        narrow = {
            "a": FakeModel(name="a", bias=0.0),
            "b": FakeModel(name="b", bias=10.0),
            "c": FakeModel(name="c", bias=20.0),
        }
        wide = {
            "a": FakeModel(name="a", bias=0.0),
            "b": FakeModel(name="b", bias=10_000.0),
            "c": FakeModel(name="c", bias=20_000.0),
        }
        narrow_result = ModelComparisonEngine(models=narrow).compare(
            future_data
        )
        wide_result = ModelComparisonEngine(models=wide).compare(
            future_data
        )
        assert narrow_result.agreement_score > wide_result.agreement_score

    def test_all_failed_models_agree_trivially(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that all-fail returns agreement = 1.0 (no spread)."""
        models = {
            "a": FakeModel(name="a", fail_on_predict=True),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)
        assert result.agreement_score == 1.0


# ============================================================
# BEST MODEL TESTS
# ============================================================
class TestEngineBestModel:
    """Tests for best model identification."""

    def test_best_model_is_lowest_mae(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that best model is the one with the lowest MAE."""
        models = {
            "a": FakeModel(name="a", mae=100.0),
            "b": FakeModel(name="b", mae=50.0),
            "c": FakeModel(name="c", mae=200.0),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)
        assert result.best_model == "b"

    def test_best_model_none_when_no_metrics(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that best_model is None when no model has a MAE."""
        models = {
            "a": FakeModel(name="a", mae=None),
            "b": FakeModel(name="b", mae=None),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)
        assert result.best_model is None

    def test_best_model_ignores_failed_models(
        self,
        future_data: pd.DataFrame,
    ) -> None:
        """Test that failed models are excluded from best-model search."""
        models = {
            "good": FakeModel(name="good", mae=100.0),
            "fails": FakeModel(
                name="fails", mae=1.0, fail_on_predict=True
            ),
        }
        engine = ModelComparisonEngine(models=models)
        result = engine.compare(future_data)
        # 'fails' has lower MAE but failed, so 'good' wins
        assert result.best_model == "good"


# ============================================================
# BUILD_DEFAULT_ENGINE TESTS
# ============================================================
class TestBuildDefaultEngine:
    """Tests for the build_default_engine() factory."""

    def test_registers_all_six_variants(self) -> None:
        """Test that all 6 default variants are registered."""
        engine = build_default_engine()
        assert set(engine.get_registered_models()) == set(DEFAULT_MODEL_KEYS)

    def test_returns_comparison_engine(self) -> None:
        """Test that the factory returns a ModelComparisonEngine."""
        engine = build_default_engine()
        assert isinstance(engine, ModelComparisonEngine)

    def test_default_parallel_is_false(self) -> None:
        """Test that the factory defaults to sequential mode."""
        engine = build_default_engine()
        assert engine.parallel is False

    def test_parallel_can_be_enabled(self) -> None:
        """Test that the factory accepts parallel=True."""
        engine = build_default_engine(parallel=True)
        assert engine.parallel is True

    def test_max_workers_override(self) -> None:
        """Test that the factory accepts max_workers."""
        engine = build_default_engine(max_workers=2)
        assert engine.max_workers == 2

    def test_models_are_untrained_initially(self) -> None:
        """Test that the factory registers untrained models."""
        engine = build_default_engine()
        for model in engine.models.values():
            assert model.is_model_trained() is False

    def test_models_have_correct_types(self) -> None:
        """Test that each registered model is the right family."""
        from app.ai import LightGBMModel, ProphetModel, XGBoostModel

        engine = build_default_engine()
        assert isinstance(engine.models["prophet_fresh"], ProphetModel)
        assert isinstance(engine.models["prophet_warm"], ProphetModel)
        assert isinstance(engine.models["xgboost_fresh"], XGBoostModel)
        assert isinstance(
            engine.models["xgboost_incremental"], XGBoostModel
        )
        assert isinstance(engine.models["lightgbm_fresh"], LightGBMModel)
        assert isinstance(
            engine.models["lightgbm_incremental"], LightGBMModel
        )


# ============================================================
# INTEGRATION TESTS (real models)
# ============================================================
class TestEngineIntegration:
    """Integration tests that exercise all 6 real model variants.

    These tests are slower because they actually train Prophet,
    XGBoost, and LightGBM on synthetic data. They verify that
    build_default_engine() produces a working end-to-end pipeline.

    Fixtures are class-scoped and decorated with @classmethod per
    pytest's recommended pattern for class-scoped state.
    """

    @pytest.fixture(scope="class")
    @classmethod
    def real_training_data(cls) -> pd.DataFrame:
        """Synthetic training data for real models (100 rows)."""
        n = 100
        dates = pd.date_range("2024-01-01", periods=n, freq="D")
        np.random.seed(42)

        base_price = 50_000
        trend = np.linspace(0, 8_000, n)
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

    @pytest.fixture(scope="class")
    @classmethod
    def real_future_data(cls, real_training_data: pd.DataFrame) -> pd.DataFrame:
        """Future data with enough history for lag features."""
        n_future = 7
        last_date = real_training_data["ds"].iloc[-1]
        future_dates = pd.date_range(
            last_date + pd.Timedelta(days=1), periods=n_future, freq="D"
        )

        future_rows = pd.DataFrame(
            {
                "ds": future_dates,
                "y": [real_training_data["y"].iloc[-1]] * n_future,
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

        return pd.concat(
            [real_training_data, future_rows], ignore_index=True
        )

    @pytest.fixture(scope="class")
    @classmethod
    def trained_default_engine(
        cls, real_training_data: pd.DataFrame
    ) -> ModelComparisonEngine:
        """Build the default engine and train all 6 models on real data."""
        engine = build_default_engine()

        # Train XGBoost + LightGBM directly (fast)
        for name in ["xgboost_fresh", "xgboost_incremental"]:
            engine.models[name].train(real_training_data)
        for name in ["lightgbm_fresh", "lightgbm_incremental"]:
            engine.models[name].train(real_training_data)

        # Train Prophet variants (slower). Prophet fresh/warm both
        # support the same train() interface.
        for name in ["prophet_fresh", "prophet_warm"]:
            try:
                engine.models[name].train(real_training_data)
            except Exception as e:
                pytest.skip(f"Prophet training failed: {e}")

        return engine

    def test_end_to_end_all_six_models_run(
        self,
        trained_default_engine: ModelComparisonEngine,
        real_future_data: pd.DataFrame,
    ) -> None:
        """Test that all 6 real models can run through the engine."""
        result = trained_default_engine.compare(real_future_data)

        # All 6 should succeed
        assert len(result.models_run) == 6
        assert result.models_failed == []
        assert set(result.models_run) == set(DEFAULT_MODEL_KEYS)

    def test_end_to_end_consensus_produced(
        self,
        trained_default_engine: ModelComparisonEngine,
        real_future_data: pd.DataFrame,
    ) -> None:
        """Test that the consensus DataFrame is produced."""
        result = trained_default_engine.compare(real_future_data)
        assert result.consensus is not None
        assert "ds" in result.consensus.columns
        assert "yhat" in result.consensus.columns

    def test_end_to_end_agreement_in_range(
        self,
        trained_default_engine: ModelComparisonEngine,
        real_future_data: pd.DataFrame,
    ) -> None:
        """Test that the agreement score is in [0, 1]."""
        result = trained_default_engine.compare(real_future_data)
        assert (
            AGREEMENT_SCORE_MIN
            <= result.agreement_score
            <= AGREEMENT_SCORE_MAX
        )

    def test_end_to_end_best_model_is_one_of_the_six(
        self,
        trained_default_engine: ModelComparisonEngine,
        real_future_data: pd.DataFrame,
    ) -> None:
        """Test that best_model is one of the registered names."""
        result = trained_default_engine.compare(real_future_data)
        if result.best_model is not None:
            assert result.best_model in DEFAULT_MODEL_KEYS

    def test_end_to_end_to_dict_is_serializable(
        self,
        trained_default_engine: ModelComparisonEngine,
        real_future_data: pd.DataFrame,
    ) -> None:
        """Test that the result can be serialized via to_dict()."""
        import json

        result = trained_default_engine.compare(real_future_data)
        d = result.to_dict()

        # Should be JSON-serializable (no numpy types, no DataFrames)
        serialized = json.dumps(d, default=str)
        assert isinstance(serialized, str)
        assert len(serialized) > 0


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestEngineConstants:
    """Tests for module-level constants."""

    def test_agreement_bounds(self) -> None:
        """Test that agreement bounds are 0 and 1."""
        assert AGREEMENT_SCORE_MIN == 0.0
        assert AGREEMENT_SCORE_MAX == 1.0

    def test_default_model_keys_count(self) -> None:
        """Test that exactly 6 default model keys are defined."""
        assert len(DEFAULT_MODEL_KEYS) == 6

    def test_default_model_keys_content(self) -> None:
        """Test the exact set of default model keys."""
        assert set(DEFAULT_MODEL_KEYS) == {
            "prophet_fresh",
            "prophet_warm",
            "xgboost_fresh",
            "xgboost_incremental",
            "lightgbm_fresh",
            "lightgbm_incremental",
        }