"""Unit tests for the PredictionGenerator.

These tests use a fake ForecastModel and a mocked repository, so
no real database or model is needed. They verify:
    - Happy-path flow: fetch → build → predict → save
    - Missing/untrained model → error in result
    - Empty history → error in result
    - Insufficient history → error in result
    - Empty predictions from model → error in result
    - Future frame construction (24 rows, hourly, forward-filled)
    - PredictionRow conversion (correct field mapping)
    - GenerationResult serialization

Test organization:
    - TestGenerationResult: dataclass behavior
    - TestGeneratorInitialization: constructor validation
    - TestGeneratorFutureFrame: _build_future_frame logic
    - TestGeneratorRowConversion: _predictions_to_rows logic
    - TestGeneratorGenerate: end-to-end generate() with mocks
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pandas as pd
import pytest

from app.ai.base import ForecastModel
from app.prediction.generator import (
    DEFAULT_CONFIDENCE,
    MIN_HISTORY_ROWS,
    GenerationResult,
    PredictionGenerator,
)


# ============================================================
# FAKE MODEL
# ============================================================
class FakeModel(ForecastModel):
    """Deterministic ForecastModel for generator tests."""

    def __init__(
        self,
        name: str = "fake",
        trained: bool = True,
        return_empty: bool = False,
        fail_on_predict: bool = False,
    ) -> None:
        super().__init__()
        self._name = name
        self._return_empty = return_empty
        self._fail_on_predict = fail_on_predict
        self.is_trained = trained

    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        self.is_trained = True
        return {"mae": 100.0}

    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        if self._fail_on_predict:
            raise RuntimeError(f"{self._name} predict failed")
        if self._return_empty:
            return pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"])

        n = len(future_data)
        base = 50_000.0
        return pd.DataFrame(
            {
                "ds": future_data["ds"].values[:n],
                "yhat": [base] * n,
                "yhat_lower": [base - 500.0] * n,
                "yhat_upper": [base + 500.0] * n,
            }
        )

    def get_metrics(self) -> Dict[str, float]:
        return {"mae": 100.0}

    def get_name(self) -> str:
        return self._name

    def get_version(self) -> str:
        return "1.0.0"

    def save(self, path: str) -> None:
        pass

    def load(self, path: str) -> None:
        self.is_trained = True


# ============================================================
# FIXTURES
# ============================================================
def _make_history(rows: int = 100) -> pd.DataFrame:
    """Build a synthetic history frame with all 10 regressors."""
    n = rows
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    np.random.seed(42)
    y = 50_000 + np.linspace(0, 500, n) + np.random.normal(0, 50, n)

    return pd.DataFrame(
        {
            "ds": dates,
            "y": y,
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


@pytest.fixture
def history() -> pd.DataFrame:
    return _make_history(100)


@pytest.fixture
def mock_repository(history: pd.DataFrame) -> MagicMock:
    """Mocked PredictionRepository."""
    repo = MagicMock()
    repo.fetch_training_frame = AsyncMock(return_value=history)
    repo.save_predictions = AsyncMock(return_value=24)
    return repo


# ============================================================
# GENERATION RESULT TESTS
# ============================================================
class TestGenerationResult:
    """Tests for the GenerationResult dataclass."""

    def test_default_construction(self) -> None:
        """Test that a result can be constructed with defaults."""
        now = datetime.now(timezone.utc)
        r = GenerationResult(
            horizon="24h",
            model_name="prophet",
            prediction_time=now,
        )
        assert r.horizon == "24h"
        assert r.model_name == "prophet"
        assert r.rows_generated == 0
        assert r.rows_saved == 0
        assert r.confidence == DEFAULT_CONFIDENCE
        assert r.elapsed_seconds == 0.0
        assert r.predictions is None
        assert r.error is None
        assert r.succeeded is True

    def test_succeeded_false_when_error_set(self) -> None:
        """Test that succeeded is False when an error is present."""
        r = GenerationResult(
            horizon="24h",
            model_name="prophet",
            prediction_time=datetime.now(timezone.utc),
            error="boom",
        )
        assert r.succeeded is False

    def test_to_dict(self) -> None:
        """Test that to_dict returns expected keys."""
        now = datetime.now(timezone.utc)
        r = GenerationResult(
            horizon="24h",
            model_name="prophet",
            prediction_time=now,
            rows_generated=24,
            rows_saved=24,
            elapsed_seconds=1.5,
        )
        d = r.to_dict()
        assert d["horizon"] == "24h"
        assert d["rows_generated"] == 24
        assert d["rows_saved"] == 24
        assert d["succeeded"] is True
        assert d["predictions"] is None

    def test_to_dict_with_predictions(self, history: pd.DataFrame) -> None:
        """Test that predictions DataFrame is serialized to records."""
        now = datetime.now(timezone.utc)
        df = pd.DataFrame(
            {
                "ds": history["ds"].head(3).values,
                "yhat": [1.0, 2.0, 3.0],
                "yhat_lower": [0.5, 1.5, 2.5],
                "yhat_upper": [1.5, 2.5, 3.5],
            }
        )
        r = GenerationResult(
            horizon="24h",
            model_name="prophet",
            prediction_time=now,
            predictions=df,
        )
        d = r.to_dict()
        assert isinstance(d["predictions"], list)
        assert len(d["predictions"]) == 3

    def test_repr(self) -> None:
        """Test __repr__ format."""
        now = datetime.now(timezone.utc)
        r = GenerationResult(
            horizon="24h",
            model_name="prophet",
            prediction_time=now,
            rows_saved=24,
        )
        assert "horizon='24h'" in repr(r)
        assert "rows_saved=24" in repr(r)
        assert "status='ok'" in repr(r)


# ============================================================
# INITIALIZATION TESTS
# ============================================================
class TestGeneratorInitialization:
    """Tests for PredictionGenerator initialization."""

    def test_default_construction(self) -> None:
        """Test that the generator constructs with valid defaults."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
        )
        assert g.horizon == "24h"
        assert g.horizon_hours == 24
        assert g.confidence == DEFAULT_CONFIDENCE

    def test_invalid_confidence_raises(self) -> None:
        """Test that an invalid confidence level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence"):
            PredictionGenerator(
                model=FakeModel(),
                repository=MagicMock(),
                confidence=0.50,
            )

    def test_invalid_horizon_hours_raises(self) -> None:
        """Test that non-positive horizon_hours raises ValueError."""
        with pytest.raises(ValueError, match="horizon_hours must be positive"):
            PredictionGenerator(
                model=FakeModel(),
                repository=MagicMock(),
                horizon_hours=0,
            )

    def test_repr(self) -> None:
        """Test __repr__ format."""
        g = PredictionGenerator(
            model=FakeModel(name="test_model"),
            repository=MagicMock(),
        )
        r = repr(g)
        assert "PredictionGenerator" in r
        assert "model='test_model'" in r
        assert "horizon='24h'" in r


# ============================================================
# FUTURE FRAME TESTS
# ============================================================
class TestGeneratorFutureFrame:
    """Tests for _build_future_frame()."""

    def test_creates_correct_number_of_rows(self, history: pd.DataFrame) -> None:
        """Test that 24 hourly rows are produced for a 24h horizon."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
            horizon_hours=24,
        )
        future = g._build_future_frame(history)
        assert len(future) == 24

    def test_starts_after_last_timestamp(self, history: pd.DataFrame) -> None:
        """Test that the first future row is 1 hour after the last history."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
            horizon_hours=24,
        )
        future = g._build_future_frame(history)
        last_history_ds = pd.to_datetime(history["ds"]).max()
        first_future_ds = pd.to_datetime(future["ds"]).iloc[0]
        assert first_future_ds == last_history_ds + timedelta(hours=1)

    def test_hourly_frequency(self, history: pd.DataFrame) -> None:
        """Test that future timestamps are hourly."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
            horizon_hours=24,
        )
        future = g._build_future_frame(history)
        diffs = pd.to_datetime(future["ds"]).diff().dropna()
        assert all(d == timedelta(hours=1) for d in diffs)

    def test_preserves_regressor_columns(self, history: pd.DataFrame) -> None:
        """Test that all regressor columns are present in the future frame."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
            horizon_hours=24,
        )
        future = g._build_future_frame(history)
        for col in (
            "cpi",
            "interest_rate",
            "m2_growth",
            "dxy",
            "treasury_yield",
            "volume",
            "volatility",
            "dominance",
            "active_addresses",
            "price_lag_7d",
        ):
            assert col in future.columns

    def test_forward_fills_regressor_values(self, history: pd.DataFrame) -> None:
        """Test that regressor values are carried over from the last row."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
            horizon_hours=24,
        )
        future = g._build_future_frame(history)
        assert (future["cpi"] == history["cpi"].iloc[-1]).all()
        assert (future["interest_rate"] == history["interest_rate"].iloc[-1]).all()

    def test_raises_on_missing_ds(self) -> None:
        """Test that a frame without 'ds' raises ValueError."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
        )
        bad_history = pd.DataFrame({"y": [1.0, 2.0]})
        with pytest.raises(ValueError, match="missing the 'ds' column"):
            g._build_future_frame(bad_history)

    def test_raises_on_empty_history(self) -> None:
        """Test that empty history raises ValueError."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
        )
        with pytest.raises(ValueError, match="empty history"):
            g._build_future_frame(pd.DataFrame(columns=["ds", "y"]))


# ============================================================
# ROW CONVERSION TESTS
# ============================================================
class TestGeneratorRowConversion:
    """Tests for _predictions_to_rows()."""

    def _make_predictions(self, n: int = 3) -> pd.DataFrame:
        dates = pd.date_range("2024-04-01", periods=n, freq="h")
        return pd.DataFrame(
            {
                "ds": dates,
                "yhat": [50_000.0 + i for i in range(n)],
                "yhat_lower": [49_000.0 + i for i in range(n)],
                "yhat_upper": [51_000.0 + i for i in range(n)],
            }
        )

    def test_converts_all_rows(self) -> None:
        """Test that all prediction rows are converted."""
        g = PredictionGenerator(
            model=FakeModel(name="prophet"),
            repository=MagicMock(),
            horizon="24h",
            confidence=0.85,
        )
        now = datetime.now(timezone.utc)
        rows = g._predictions_to_rows(self._make_predictions(3), now)
        assert len(rows) == 3

    def test_field_mapping(self) -> None:
        """Test that prediction columns map to the right PredictionRow fields."""
        g = PredictionGenerator(
            model=FakeModel(name="prophet"),
            repository=MagicMock(),
            horizon="24h",
            confidence=0.85,
        )
        now = datetime.now(timezone.utc)
        rows = g._predictions_to_rows(self._make_predictions(1), now)
        row = rows[0]
        assert row.horizon == "24h"
        assert row.model_name == "prophet"
        assert row.confidence == 0.85
        assert row.predicted_price == 50_000.0
        assert row.lower_bound == 49_000.0
        assert row.upper_bound == 51_000.0

    def test_missing_columns_raises(self) -> None:
        """Test that missing prediction columns raise ValueError."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=MagicMock(),
        )
        bad = pd.DataFrame({"ds": [pd.Timestamp("2024-04-01")], "yhat": [1.0]})
        with pytest.raises(ValueError, match="missing required columns"):
            g._predictions_to_rows(bad, datetime.now(timezone.utc))


# ============================================================
# GENERATE END-TO-END TESTS
# ============================================================
class TestGeneratorGenerate:
    """Tests for the full generate() flow."""

    @pytest.mark.asyncio
    async def test_happy_path(
        self,
        mock_repository: MagicMock,
        history: pd.DataFrame,
    ) -> None:
        """Test the happy path: fetch, predict, save."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
            horizon="24h",
            horizon_hours=24,
        )
        result = await g.generate()

        assert result.succeeded is True
        assert result.rows_generated == 24
        assert result.rows_saved == 24
        assert result.error is None
        assert result.elapsed_seconds >= 0.0

    @pytest.mark.asyncio
    async def test_calls_repository_methods(
        self,
        mock_repository: MagicMock,
        history: pd.DataFrame,
    ) -> None:
        """Test that the repository is called the expected number of times."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
        )
        await g.generate()

        mock_repository.fetch_training_frame.assert_called_once()
        mock_repository.save_predictions.assert_called_once()

    @pytest.mark.asyncio
    async def test_untrained_model_yields_error(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that an untrained model produces an error result."""
        g = PredictionGenerator(
            model=FakeModel(trained=False),
            repository=mock_repository,
        )
        result = await g.generate()

        assert result.succeeded is False
        assert result.error is not None
        assert "not trained" in result.error

    @pytest.mark.asyncio
    async def test_empty_history_yields_error(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that empty history produces an error result."""
        mock_repository.fetch_training_frame = AsyncMock(
            return_value=pd.DataFrame()
        )
        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
        )
        result = await g.generate()

        assert result.succeeded is False
        assert "No history" in result.error

    @pytest.mark.asyncio
    async def test_insufficient_history_yields_error(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that too few history rows produces an error result."""
        small = _make_history(MIN_HISTORY_ROWS - 1)
        mock_repository.fetch_training_frame = AsyncMock(return_value=small)
        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
        )
        result = await g.generate()

        assert result.succeeded is False
        assert "Insufficient history" in result.error

    @pytest.mark.asyncio
    async def test_empty_predictions_yields_error(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that empty predictions from the model produce an error."""
        g = PredictionGenerator(
            model=FakeModel(return_empty=True),
            repository=mock_repository,
        )
        result = await g.generate()

        assert result.succeeded is False
        assert "empty predictions" in result.error.lower()

    @pytest.mark.asyncio
    async def test_model_predict_exception_yields_error(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that a model exception is captured in the result."""
        g = PredictionGenerator(
            model=FakeModel(fail_on_predict=True),
            repository=mock_repository,
        )
        result = await g.generate()

        assert result.succeeded is False
        assert "predict failed" in result.error

    @pytest.mark.asyncio
    async def test_result_has_predictions_dataframe(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that the result carries the raw predictions DataFrame."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
        )
        result = await g.generate()

        assert result.predictions is not None
        assert len(result.predictions) == 24
        assert set(result.predictions.columns) == {
            "ds",
            "yhat",
            "yhat_lower",
            "yhat_upper",
        }

    @pytest.mark.asyncio
    async def test_prediction_time_consistent_across_rows(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that all saved rows share one prediction_time."""
        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
        )
        await g.generate()

        saved_rows = mock_repository.save_predictions.call_args[0][0]
        assert len(saved_rows) == 24
        prediction_times = {r.prediction_time for r in saved_rows}
        assert len(prediction_times) == 1

    @pytest.mark.asyncio
    async def test_to_dict_is_serializable(
        self,
        mock_repository: MagicMock,
    ) -> None:
        """Test that the result can be serialized via to_dict()."""
        import json

        g = PredictionGenerator(
            model=FakeModel(),
            repository=mock_repository,
        )
        result = await g.generate()
        d = result.to_dict()

        serialized = json.dumps(d, default=str)
        assert isinstance(serialized, str)
        assert len(serialized) > 0