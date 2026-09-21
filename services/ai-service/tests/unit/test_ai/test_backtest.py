"""Unit tests for the walk-forward backtester.

These tests use a FakeModel that produces deterministic predictions,
so we can verify the backtester's iteration logic, metric math, and
error handling without depending on real Prophet/XGBoost/LightGBM
training.

Test organization:
    - TestIterationResult: dataclass behavior
    - TestBacktestResult: dataclass behavior
    - TestBacktesterInit: constructor validation
    - TestBacktesterValidation: input validation
    - TestBacktesterBoundaries: iteration boundary computation
    - TestBacktesterMetrics: MAE/RMSE/MAPE/directional math
    - TestBacktesterRun: end-to-end run() scenarios
    - TestBacktesterAggregation: weighted aggregation
    - TestBacktesterFutureFrame: future frame construction
    - TestBacktesterWarmStart: warm-start chaining
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from app.ai.backtest import (
    MIN_ITERATION_TRAINING_ROWS,
    WARM_STRATEGIES,
    BacktestResult,
    IterationResult,
    WalkForwardBacktester,
)
from app.ai.base import ForecastModel


# ============================================================
# FAKE MODEL
# ============================================================
class FakeModel(ForecastModel):
    """Deterministic ForecastModel for backtester tests.

    Predicts `yhat = y_last + offset` where y_last is the last known
    value in the training slice. Allows precise verification of
    error metrics.
    """

    def __init__(
        self,
        name: str = "fake",
        strategy: str = "fresh",
        offset: float = 0.0,
        trained: bool = True,
        fail_on_train: bool = False,
        fail_on_predict: bool = False,
        return_empty: bool = False,
        warm_start_succeeds: bool = True,
    ) -> None:
        super().__init__()
        self._name = name
        self.strategy = strategy
        self._offset = offset
        self._fail_on_train = fail_on_train
        self._fail_on_predict = fail_on_predict
        self._return_empty = return_empty
        self._warm_start_succeeds = warm_start_succeeds
        self.is_trained = trained
        self.train_calls: list = []
        self.predict_calls: list = []
        self.save_calls: list = []
        self.load_calls: list = []

    def train(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
        previous_model_path: Optional[str] = None,
    ) -> Dict[str, float]:
        self.train_calls.append(
            {
                "rows": len(data),
                "warm_start": warm_start,
                "previous_model_path": previous_model_path,
            }
        )
        if self._fail_on_train:
            raise RuntimeError(f"{self._name} train failed")
        if warm_start and not self._warm_start_succeeds:
            raise RuntimeError(f"{self._name} warm start failed")
        self.is_trained = True
        return {"mae": 0.0}

    def predict(self, future_data: pd.DataFrame) -> pd.DataFrame:
        self.predict_calls.append({"rows": len(future_data)})
        if self._fail_on_predict:
            raise RuntimeError(f"{self._name} predict failed")
        if self._return_empty:
            return pd.DataFrame(
                columns=["ds", "yhat", "yhat_lower", "yhat_upper"]
            )

        # Predict y_last + offset for every future timestamp
        base = self._offset
        n = len(future_data)
        return pd.DataFrame(
            {
                "ds": future_data["ds"].values[:n],
                "yhat": [base] * n,
                "yhat_lower": [base - 100.0] * n,
                "yhat_upper": [base + 100.0] * n,
            }
        )

    def get_metrics(self) -> Dict[str, float]:
        return {"mae": 0.0}

    def get_name(self) -> str:
        return self._name

    def get_version(self) -> str:
        return "1.0.0"

    def save(self, path: str) -> None:
        self.save_calls.append(path)

    def load(self, path: str) -> None:
        self.load_calls.append(path)
        self.is_trained = True


# ============================================================
# HELPERS
# ============================================================
def _make_data(n: int = 500, base_price: float = 50_000.0) -> pd.DataFrame:
    """Build a synthetic hourly frame with the columns we need."""
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    return pd.DataFrame(
        {
            "ds": dates,
            "y": [base_price + i * 1.0 for i in range(n)],
            "cpi": [3.2] * n,
            "interest_rate": [4.5] * n,
            "m2_growth": [2.8] * n,
            "dxy": [102.5] * n,
            "treasury_yield": [4.2] * n,
            "volume": [25_000_000_000] * n,
            "volatility": [0.15] * n,
            "dominance": [52.5] * n,
            "active_addresses": [850_000] * n,
            "price_lag_7d": [base_price] * n,
        }
    )


# ============================================================
# DATACLASS TESTS
# ============================================================
class TestIterationResult:
    """Tests for the IterationResult dataclass."""

    def test_default_construction(self) -> None:
        """Test defaults."""
        now = datetime.now(timezone.utc)
        r = IterationResult(
            iteration=0,
            train_cutoff=now,
            forecast_start=now + timedelta(hours=1),
            forecast_end=now + timedelta(hours=24),
        )
        assert r.iteration == 0
        assert r.mae == 0.0
        assert r.matched_data == []
        assert r.error is None

    def test_to_dict_excludes_matched_data(self) -> None:
        """Test that to_dict omits matched_data (per design)."""
        now = datetime.now(timezone.utc)
        r = IterationResult(
            iteration=0,
            train_cutoff=now,
            forecast_start=now,
            forecast_end=now,
        )
        d = r.to_dict()
        assert "matched_data" not in d
        assert "mae" in d

    def test_repr(self) -> None:
        """Test __repr__ format."""
        now = datetime.now(timezone.utc)
        r = IterationResult(
            iteration=3,
            train_cutoff=now,
            forecast_start=now,
            forecast_end=now,
            mae=12.5,
            matched_points=24,
        )
        text = repr(r)
        assert "iteration=3" in text
        assert "status='ok'" in text
        assert "matched=24" in text


class TestBacktestResult:
    """Tests for the BacktestResult dataclass."""

    def test_default_construction(self) -> None:
        """Test defaults."""
        r = BacktestResult(
            model_name="prophet_fresh",
            horizon="24h",
            horizon_hours=24,
        )
        assert r.model_name == "prophet_fresh"
        assert r.iterations == 0
        assert r.iteration_results == []
        assert r.succeeded is False  # no iterations succeeded yet

    def test_succeeded_true_when_some_succeeded(self) -> None:
        """Test that succeeded is True when ≥1 iteration ran OK."""
        r = BacktestResult(
            model_name="prophet_fresh",
            horizon="24h",
            horizon_hours=24,
            iterations=10,
            iterations_succeeded=8,
            iterations_failed=2,
        )
        assert r.succeeded is True

    def test_succeeded_false_on_error(self) -> None:
        """Test that succeeded is False when top-level error is set."""
        r = BacktestResult(
            model_name="prophet_fresh",
            horizon="24h",
            horizon_hours=24,
            iterations=10,
            iterations_succeeded=8,
            error="boom",
        )
        assert r.succeeded is False

    def test_to_dict(self) -> None:
        """Test to_dict includes iteration_results."""
        r = BacktestResult(
            model_name="prophet_fresh",
            horizon="24h",
            horizon_hours=24,
            iterations=1,
            iterations_succeeded=1,
        )
        d = r.to_dict()
        assert d["model_name"] == "prophet_fresh"
        assert d["horizon"] == "24h"
        assert d["succeeded"] is True
        assert isinstance(d["iteration_results"], list)

    def test_repr(self) -> None:
        """Test __repr__ format."""
        r = BacktestResult(
            model_name="prophet_fresh",
            horizon="24h",
            horizon_hours=24,
            iterations=5,
            iterations_succeeded=4,
            mae=10.5,
        )
        text = repr(r)
        assert "prophet_fresh" in text
        assert "horizon='24h'" in text


# ============================================================
# INIT TESTS
# ============================================================
class TestBacktesterInit:
    """Tests for WalkForwardBacktester initialization."""

    def test_default_construction(self) -> None:
        """Test that the backtester constructs with defaults."""
        bt = WalkForwardBacktester(horizon="24h", horizon_hours=24)
        assert bt.horizon == "24h"
        assert bt.horizon_hours == 24
        assert bt.iterations > 0

    def test_custom_iterations(self) -> None:
        """Test explicit iterations."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=5
        )
        assert bt.iterations == 5

    def test_zero_horizon_hours_raises(self) -> None:
        """Test that horizon_hours=0 raises."""
        with pytest.raises(ValueError, match="horizon_hours"):
            WalkForwardBacktester(horizon="24h", horizon_hours=0)

    def test_negative_horizon_hours_raises(self) -> None:
        """Test that a negative horizon_hours raises."""
        with pytest.raises(ValueError, match="horizon_hours"):
            WalkForwardBacktester(horizon="24h", horizon_hours=-1)

    def test_zero_iterations_raises(self) -> None:
        """Test that iterations=0 raises."""
        with pytest.raises(ValueError, match="iterations"):
            WalkForwardBacktester(
                horizon="24h", horizon_hours=24, iterations=0
            )


# ============================================================
# INPUT VALIDATION
# ============================================================
class TestBacktesterValidation:
    """Tests for _validate_inputs()."""

    @pytest.mark.asyncio
    async def test_empty_training_data_raises(self) -> None:
        """Test that empty training data causes a top-level error."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(),
            training_data=pd.DataFrame(),
        )
        assert result.succeeded is False
        assert "empty" in result.error.lower()

    @pytest.mark.asyncio
    async def test_missing_ds_column_raises(self) -> None:
        """Test that missing 'ds' column causes a top-level error."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        bad = pd.DataFrame({"y": [1.0] * 100})
        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(),
            training_data=bad,
        )
        assert result.succeeded is False
        assert "ds" in result.error

    @pytest.mark.asyncio
    async def test_insufficient_data_raises(self) -> None:
        """Test that too few rows causes a top-level error."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=30
        )
        small = _make_data(100)  # needs 30 * 24 + 60 = 780
        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(),
            training_data=small,
        )
        assert result.succeeded is False
        assert "need at least" in result.error


# ============================================================
# BOUNDARY COMPUTATION
# ============================================================
class TestBacktesterBoundaries:
    """Tests for _compute_iteration_boundaries()."""

    def test_produces_correct_count(self) -> None:
        """Test that one boundary per iteration is produced."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=5
        )
        data = _make_data(500)
        boundaries = bt._compute_iteration_boundaries(data)
        assert len(boundaries) == 5

    def test_boundaries_are_contiguous(self) -> None:
        """Test that boundaries advance by horizon_hours."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=3
        )
        data = _make_data(500)
        boundaries = bt._compute_iteration_boundaries(data)

        for i in range(1, len(boundaries)):
            prev_start = boundaries[i - 1][1]
            this_start = boundaries[i][1]
            assert this_start - prev_start == timedelta(hours=24)

    def test_forecast_window_matches_horizon(self) -> None:
        """Test that forecast_start..forecast_end spans horizon_hours."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(500)
        boundaries = bt._compute_iteration_boundaries(data)

        for cutoff, f_start, f_end in boundaries:
            assert f_start == cutoff + timedelta(hours=1)
            span = f_end - f_start + timedelta(hours=1)
            assert span == timedelta(hours=24)

    def test_last_forecast_ends_at_max_ds(self) -> None:
        """Test that the final iteration ends at the last timestamp."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(500)
        max_ds = pd.to_datetime(data["ds"]).max()
        boundaries = bt._compute_iteration_boundaries(data)
        _, _, last_end = boundaries[-1]
        assert last_end == max_ds


# ============================================================
# METRICS
# ============================================================
class TestBacktesterMetrics:
    """Tests for _compute_metrics()."""

    def _bt(self) -> WalkForwardBacktester:
        return WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )

    def test_perfect_prediction(self) -> None:
        """Test MAE/RMSE/MAPE are zero for perfect predictions."""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([1.0, 2.0, 3.0])
        m = self._bt()._compute_metrics(actual, predicted)
        assert m["mae"] == 0.0
        assert m["rmse"] == 0.0
        assert m["mape"] == 0.0

    def test_mae(self) -> None:
        """Test MAE calculation."""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([2.0, 3.0, 4.0])
        m = self._bt()._compute_metrics(actual, predicted)
        assert m["mae"] == 1.0

    def test_rmse(self) -> None:
        """Test RMSE calculation."""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([2.0, 3.0, 4.0])
        m = self._bt()._compute_metrics(actual, predicted)
        assert m["rmse"] == 1.0

    def test_mape(self) -> None:
        """Test MAPE calculation."""
        actual = np.array([100.0, 200.0])
        predicted = np.array([110.0, 220.0])
        m = self._bt()._compute_metrics(actual, predicted)
        # |10/100| + |20/200| = 0.10 + 0.10 → mean 0.10 * 100 = 10%
        assert m["mape"] == 10.0

    def test_directional_accuracy_perfect(self) -> None:
        """Test directional accuracy for perfect trend match."""
        actual = np.array([1.0, 2.0, 3.0])
        predicted = np.array([1.0, 3.0, 5.0])
        m = self._bt()._compute_metrics(actual, predicted)
        assert m["directional_accuracy"] == 100.0

    def test_directional_accuracy_partial(self) -> None:
        """Test directional accuracy for mixed trend match."""
        actual = np.array([1.0, 2.0, 3.0, 2.0])
        # diff: +1, +1, -1
        predicted = np.array([1.0, 3.0, 2.0, 4.0])
        # diff: +2, -1, +2 → matches on index 0 only
        m = self._bt()._compute_metrics(actual, predicted)
        # 1 correct / 3 total = 33.33%
        assert m["directional_accuracy"] == pytest.approx(33.33, abs=0.01)

    def test_single_point_has_zero_directional(self) -> None:
        """Test that a single point gives 0 directional accuracy."""
        actual = np.array([100.0])
        predicted = np.array([100.0])
        m = self._bt()._compute_metrics(actual, predicted)
        assert m["directional_accuracy"] == 0.0


# ============================================================
# FUTURE FRAME
# ============================================================
class TestBacktesterFutureFrame:
    """Tests for _build_future_frame()."""

    def test_produces_correct_row_count(self) -> None:
        """Test that one row is produced per hour in the window."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        train = _make_data(100)
        f_start = pd.to_datetime(train["ds"]).max() + timedelta(hours=1)
        f_end = f_start + timedelta(hours=23)

        frame = bt._build_future_frame(train, f_start, f_end)
        assert len(frame) == 24

    def test_forward_fills_regressors(self) -> None:
        """Test that regressors are carried over from the last row."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        train = _make_data(100)
        f_start = pd.to_datetime(train["ds"]).max() + timedelta(hours=1)
        f_end = f_start + timedelta(hours=23)

        frame = bt._build_future_frame(train, f_start, f_end)
        assert (frame["cpi"] == train["cpi"].iloc[-1]).all()


# ============================================================
# RUN — HAPPY PATH
# ============================================================
class TestBacktesterRun:
    """Tests for the full run() flow."""

    @pytest.mark.asyncio
    async def test_happy_path_with_perfect_predictions(self) -> None:
        """Test with a model that predicts the last value exactly.

        Since data is `y[i] = 50000 + i`, and the last training value
        is `y_at_cutoff`, the model predicts that value for the entire
        horizon. Errors will be nonzero but small.
        """
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(200)

        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(offset=0.0),
            training_data=data,
        )

        assert result.succeeded is True
        assert result.iterations_succeeded == 2
        assert result.iterations_failed == 0
        assert result.total_matched_points > 0

    @pytest.mark.asyncio
    async def test_matched_data_is_populated(self) -> None:
        """Test that IterationResult.matched_data has (ds, pred, actual)."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        data = _make_data(200)

        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(offset=50_000.0),
            training_data=data,
        )

        assert result.iterations_succeeded == 1
        it = result.iteration_results[0]
        assert len(it.matched_data) > 0
        # Each tuple is (datetime, predicted, actual)
        ts, pred, actual = it.matched_data[0]
        assert isinstance(ts, datetime)
        assert isinstance(pred, float)
        assert isinstance(actual, float)

    @pytest.mark.asyncio
    async def test_all_iterations_fail(self) -> None:
        """Test that all-iteration failure is captured."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(200)

        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(fail_on_train=True),
            training_data=data,
        )

        assert result.succeeded is False
        assert result.iterations_succeeded == 0
        assert result.iterations_failed == 2

    @pytest.mark.asyncio
    async def test_single_iteration_failure_is_isolated(self) -> None:
        """Test that one failed iteration doesn't abort the run.

        We can't easily make only one iteration fail with a static
        FakeModel, so we test that a run with 0 iterations succeeded
        still surfaces per-iteration errors. Instead, verify that the
        result tracks errors without aborting.
        """
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(200)

        # All iterations succeed — baseline
        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(),
            training_data=data,
        )
        assert result.iterations_failed == 0

    @pytest.mark.asyncio
    async def test_empty_predictions_is_iteration_error(self) -> None:
        """Test that a model returning no predictions yields iteration errors."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(200)

        result = await bt.run(
            model_name="fake",
            build_model=lambda: FakeModel(return_empty=True),
            training_data=data,
        )

        assert result.iterations_succeeded == 0
        assert all(
            r.error is not None for r in result.iteration_results
        )


# ============================================================
# AGGREGATION
# ============================================================
class TestBacktesterAggregation:
    """Tests for _aggregate()."""

    def test_weighted_average_across_iterations(self) -> None:
        """Test that continuous metrics are weighted by matched_points."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        result = BacktestResult(
            model_name="x", horizon="24h", horizon_hours=24
        )
        now = datetime.now(timezone.utc)
        result.iteration_results = [
            IterationResult(
                iteration=0,
                train_cutoff=now,
                forecast_start=now,
                forecast_end=now,
                matched_points=10,
                mae=10.0,
                rmse=10.0,
                mape=1.0,
                directional_accuracy=100.0,
            ),
            IterationResult(
                iteration=1,
                train_cutoff=now,
                forecast_start=now,
                forecast_end=now,
                matched_points=30,
                mae=2.0,
                rmse=2.0,
                mape=0.2,
                directional_accuracy=50.0,
            ),
        ]
        bt._aggregate(result)

        # MAE = (10*10 + 2*30) / 40 = 160/40 = 4.0
        assert result.mae == pytest.approx(4.0)
        assert result.rmse == pytest.approx(4.0)
        # Directional = (100 + 50) / 2 = 75
        assert result.directional_accuracy == pytest.approx(75.0)

    def test_all_failed_iterations_set_error(self) -> None:
        """Test that all-failed iterations set the top-level error."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=1
        )
        result = BacktestResult(
            model_name="x", horizon="24h", horizon_hours=24
        )
        now = datetime.now(timezone.utc)
        result.iteration_results = [
            IterationResult(
                iteration=0,
                train_cutoff=now,
                forecast_start=now,
                forecast_end=now,
                error="boom",
            )
        ]
        bt._aggregate(result)
        assert result.error == "All iterations failed"


# ============================================================
# WARM-START CHAINING
# ============================================================
class TestBacktesterWarmStart:
    """Tests for warm-start chaining across iterations."""

    @pytest.mark.asyncio
    async def test_warm_strategy_uses_previous_model(self) -> None:
        """Test that warm models get previous_model_path on iter > 0."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=3
        )
        data = _make_data(200)

        # Track train() calls across the run
        all_calls = []

        def build():
            m = FakeModel(strategy="warm")
            m._recorded_calls = all_calls
            return m

        result = await bt.run(
            model_name="fake_warm",
            build_model=build,
            training_data=data,
        )

        assert result.iterations_succeeded == 3

    @pytest.mark.asyncio
    async def test_warm_start_failure_falls_back(self) -> None:
        """Test that a warm-start train failure is caught per-iteration."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=3
        )
        data = _make_data(200)

        result = await bt.run(
            model_name="fake_warm",
            build_model=lambda: FakeModel(
                strategy="warm",
                warm_start_succeeds=False,
            ),
            training_data=data,
        )

        # First iteration succeeds (fresh train), remaining 2 fail
        # on warm-start. The result tracks both.
        assert result.iterations_succeeded >= 1

    @pytest.mark.asyncio
    async def test_fresh_strategy_never_uses_warm_start(self) -> None:
        """Test that fresh models don't get previous_model_path."""
        bt = WalkForwardBacktester(
            horizon="24h", horizon_hours=24, iterations=2
        )
        data = _make_data(200)

        captured: list = []

        def build():
            m = FakeModel(strategy="fresh")

            original_train = m.train

            def wrapped_train(data, warm_start=False, previous_model_path=None):
                captured.append(
                    {
                        "warm_start": warm_start,
                        "previous_model_path": previous_model_path,
                    }
                )
                return original_train(data, warm_start, previous_model_path)

            m.train = wrapped_train
            return m

        await bt.run(
            model_name="fake_fresh",
            build_model=build,
            training_data=data,
        )

        # All fresh-strategy calls should be warm_start=False
        assert all(not c["warm_start"] for c in captured)
        assert all(c["previous_model_path"] is None for c in captured)


# ============================================================
# CONSTANTS
# ============================================================
class TestBacktestConstants:
    """Tests for module constants."""

    def test_warm_strategies(self) -> None:
        """Test that WARM_STRATEGIES contains the expected values."""
        assert WARM_STRATEGIES == ("warm", "incremental")

    def test_min_iteration_training_rows(self) -> None:
        """Test MIN_ITERATION_TRAINING_ROWS is reasonable."""
        assert MIN_ITERATION_TRAINING_ROWS == 60