"""Unit tests for the scheduler jobs module.

These tests mock the Prophet model, the repository, the generator,
and the backtester to isolate the job orchestration logic.

Test organization:
    - TestDailyRetrainJob: daily retrain of all 6 models
    - TestDailyBacktestJob: daily walk-forward backtest of all 12 (T5.2)
    - TestHourlyPredictionJob: 24h job happy path + failure paths
    - TestDaily7dPredictionJob: 7d job happy path + failure paths
    - TestBacktestVariantSpecs: variant registry + factory helper
    - TestJobConstants: module constants
"""

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.ai.backtest import BacktestResult, IterationResult
from app.prediction.generator import GenerationResult
from app.scheduler.jobs import (
    BACKTEST_VARIANTS,
    JOB_DAILY_7D_PREDICTION,
    JOB_DAILY_BACKTEST,
    JOB_DAILY_RETRAIN,
    JOB_HOURLY_PREDICTION,
    _result_to_rows,
    _variant_factory,
    daily_7d_prediction_job,
    daily_backtest_job,
    daily_retrain_job,
    hourly_prediction_job,
)


# ============================================================
# HELPERS
# ============================================================
def _make_generation_result(
    horizon: str = "24h",
    succeeded: bool = True,
    rows_generated: int = 24,
    rows_saved: int = 24,
    error: str = None,
) -> GenerationResult:
    """Build a GenerationResult for tests."""
    return GenerationResult(
        horizon=horizon,
        model_name="prophet",
        prediction_time=datetime.now(timezone.utc),
        rows_generated=rows_generated,
        rows_saved=rows_saved,
        confidence=0.85,
        elapsed_seconds=0.5,
        error=error if not succeeded else None,
    )


def _make_trained_model() -> MagicMock:
    """Build a mocked ProphetModel that reports as trained."""
    model = MagicMock()
    model.load = MagicMock()
    model.is_model_trained = MagicMock(return_value=True)
    model.get_name = MagicMock(return_value="prophet")
    return model


def _session_scope_mock() -> MagicMock:
    """Build an async context manager mock for session_scope()."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=MagicMock())
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _make_training_frame(n: int = 100) -> pd.DataFrame:
    """Build a synthetic training frame for the retrain/backtest jobs."""
    dates = pd.date_range("2024-01-01", periods=n, freq="h")
    return pd.DataFrame(
        {
            "ds": dates,
            "y": np.linspace(50_000, 51_000, n),
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


def _all_success_results() -> Dict[str, Dict[str, Any]]:
    """Build a retrain result dict with all 6 models succeeding."""
    names = [
        "prophet_fresh",
        "prophet_warm",
        "xgboost_fresh",
        "xgboost_incremental",
        "lightgbm_fresh",
        "lightgbm_incremental",
    ]
    return {
        name: {
            "model_name": name,
            "status": "success",
            "metrics": {"mae": 100.0},
            "error": None,
            "duration_seconds": 0.1,
        }
        for name in names
    }


def _make_backtest_result(succeeded: bool = True) -> BacktestResult:
    """Build a BacktestResult for tests."""
    result = BacktestResult(
        model_name="prophet_fresh",
        horizon="24h",
        horizon_hours=24,
        iterations=2,
        iterations_succeeded=2 if succeeded else 0,
        iterations_failed=0 if succeeded else 2,
        total_matched_points=48 if succeeded else 0,
        mae=100.0 if succeeded else 0.0,
        rmse=120.0 if succeeded else 0.0,
        mape=1.5 if succeeded else 0.0,
        directional_accuracy=60.0 if succeeded else 0.0,
        elapsed_seconds=0.5,
        error=None if succeeded else "All iterations failed",
    )
    if succeeded:
        now = datetime.now(timezone.utc)
        for i in range(2):
            it = IterationResult(
                iteration=i,
                train_cutoff=now,
                forecast_start=now,
                forecast_end=now,
                matched_points=24,
                mae=100.0,
                rmse=120.0,
                mape=1.5,
                directional_accuracy=60.0,
                matched_data=[
                    (
                        datetime.fromtimestamp(
                            now.timestamp() + h * 3600, tz=timezone.utc
                        ),
                        50_000.0 + h,
                        50_100.0 + h,
                    )
                    for h in range(24)
                ],
            )
            result.iteration_results.append(it)
    return result


# ============================================================
# DAILY RETRAIN JOB
# ============================================================
class TestDailyRetrainJob:
    """Tests for daily_retrain_job()."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        """Test that a successful retrain returns a summary dict."""
        frame = _make_training_frame(100)

        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=frame)

        mock_orchestrator = MagicMock()
        mock_orchestrator.retrain_all = MagicMock(
            return_value=_all_success_results()
        )

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.RetrainingOrchestrator",
            return_value=mock_orchestrator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            result = await daily_retrain_job()

        assert result["models_retrained"] == 6
        assert result["models_succeeded"] == 6
        assert result["models_failed"] == 0
        assert "elapsed_seconds" in result

    @pytest.mark.asyncio
    async def test_raises_when_training_frame_empty(self) -> None:
        """Test that an empty training frame raises RuntimeError."""
        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(
            return_value=pd.DataFrame()
        )

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="empty or unavailable"):
                await daily_retrain_job()

    @pytest.mark.asyncio
    async def test_raises_when_training_frame_none(self) -> None:
        """Test that a None training frame raises RuntimeError."""
        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=None)

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="empty or unavailable"):
                await daily_retrain_job()

    @pytest.mark.asyncio
    async def test_raises_when_insufficient_rows(self) -> None:
        """Test that too few training rows raises RuntimeError."""
        small = _make_training_frame(30)  # below 60-row floor

        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=small)

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="insufficient"):
                await daily_retrain_job()

    @pytest.mark.asyncio
    async def test_raises_when_some_models_fail(self) -> None:
        """Test that partial retrain failure raises RuntimeError."""
        frame = _make_training_frame(100)

        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=frame)

        # 5 succeed, 1 fails
        results = _all_success_results()
        results["xgboost_fresh"]["status"] = "failed"
        results["xgboost_fresh"]["error"] = "boom"

        mock_orchestrator = MagicMock()
        mock_orchestrator.retrain_all = MagicMock(return_value=results)

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.RetrainingOrchestrator",
            return_value=mock_orchestrator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="1 model"):
                await daily_retrain_job()

    @pytest.mark.asyncio
    async def test_uses_settings_model_save_dir(self) -> None:
        """Test that the orchestrator is constructed with model_save_dir."""
        from app.config import settings

        frame = _make_training_frame(100)

        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=frame)

        mock_orchestrator = MagicMock()
        mock_orchestrator.retrain_all = MagicMock(
            return_value=_all_success_results()
        )

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.RetrainingOrchestrator",
            return_value=mock_orchestrator,
        ) as mock_orch_class, patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_retrain_job()

        call_kwargs = mock_orch_class.call_args.kwargs
        assert call_kwargs["model_save_dir"] == settings.model_save_dir
        # All 6 models registered
        assert len(call_kwargs["models"]) == 6

    @pytest.mark.asyncio
    async def test_fetches_90_days_of_history(self) -> None:
        """Test that the retrain job fetches 2160 hours of history."""
        frame = _make_training_frame(100)

        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=frame)

        mock_orchestrator = MagicMock()
        mock_orchestrator.retrain_all = MagicMock(
            return_value=_all_success_results()
        )

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.RetrainingOrchestrator",
            return_value=mock_orchestrator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_retrain_job()

        # Verify fetch_training_frame was called with hours=2160
        call_kwargs = mock_repo.fetch_training_frame.call_args.kwargs
        assert call_kwargs["hours"] == 2160

    @pytest.mark.asyncio
    async def test_registers_all_six_models(self) -> None:
        """Test that the orchestrator receives all 6 model variants."""
        frame = _make_training_frame(100)

        mock_repo = MagicMock()
        mock_repo.fetch_training_frame = AsyncMock(return_value=frame)

        mock_orchestrator = MagicMock()
        mock_orchestrator.retrain_all = MagicMock(
            return_value=_all_success_results()
        )

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_repo,
        ), patch(
            "app.scheduler.jobs.RetrainingOrchestrator",
            return_value=mock_orchestrator,
        ) as mock_orch_class, patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_retrain_job()

        call_kwargs = mock_orch_class.call_args.kwargs
        expected_names = {
            "prophet_fresh",
            "prophet_warm",
            "xgboost_fresh",
            "xgboost_incremental",
            "lightgbm_fresh",
            "lightgbm_incremental",
        }
        assert set(call_kwargs["models"].keys()) == expected_names


# ============================================================
# DAILY BACKTEST JOB
# ============================================================
class TestDailyBacktestJob:
    """Tests for daily_backtest_job()."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        """Test that a successful backtest run returns a summary."""
        # 30 iterations * 168 hours + 60 = 5100 rows needed
        frame = _make_training_frame(6000)

        mock_pred_repo = MagicMock()
        mock_pred_repo.fetch_training_frame = AsyncMock(return_value=frame)

        mock_perf_repo = MagicMock()
        mock_perf_repo.save_performance_rows = AsyncMock(return_value=48)

        mock_bt = MagicMock()
        mock_bt.run = AsyncMock(return_value=_make_backtest_result(True))

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_pred_repo,
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.WalkForwardBacktester",
            return_value=mock_bt,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            result = await daily_backtest_job()

        assert result["variants_attempted"] == len(BACKTEST_VARIANTS)
        assert result["variants_succeeded"] == len(BACKTEST_VARIANTS)
        assert result["variants_failed"] == 0
        assert result["total_rows_written"] > 0

    @pytest.mark.asyncio
    async def test_raises_when_empty_data(self) -> None:
        """Test that empty training data raises."""
        mock_pred_repo = MagicMock()
        mock_pred_repo.fetch_training_frame = AsyncMock(
            return_value=pd.DataFrame()
        )

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_pred_repo,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="empty or unavailable"):
                await daily_backtest_job()

    @pytest.mark.asyncio
    async def test_raises_when_insufficient_data(self) -> None:
        """Test that too few rows raises."""
        small = _make_training_frame(100)

        mock_pred_repo = MagicMock()
        mock_pred_repo.fetch_training_frame = AsyncMock(return_value=small)

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_pred_repo,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="insufficient"):
                await daily_backtest_job()

    @pytest.mark.asyncio
    async def test_raises_when_all_variants_fail(self) -> None:
        """Test that all-variant failure raises."""
        frame = _make_training_frame(6000)

        mock_pred_repo = MagicMock()
        mock_pred_repo.fetch_training_frame = AsyncMock(return_value=frame)

        mock_perf_repo = MagicMock()
        mock_perf_repo.save_performance_rows = AsyncMock(return_value=0)

        mock_bt = MagicMock()
        mock_bt.run = AsyncMock(return_value=_make_backtest_result(False))

        with patch(
            "app.scheduler.jobs.PredictionRepository",
            return_value=mock_pred_repo,
        ), patch(
            "app.scheduler.jobs.PerformanceRepository",
            return_value=mock_perf_repo,
        ), patch(
            "app.scheduler.jobs.WalkForwardBacktester",
            return_value=mock_bt,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="All .* variants failed"):
                await daily_backtest_job()


# ============================================================
# BACKTEST VARIANT SPECS
# ============================================================
class TestBacktestVariantSpecs:
    """Tests for BACKTEST_VARIANTS and _variant_factory()."""

    def test_twelve_variants(self) -> None:
        """Test that there are 12 (6 models × 2 horizons) variants."""
        assert len(BACKTEST_VARIANTS) == 12

    def test_six_unique_models(self) -> None:
        """Test that the 6 model names appear twice (once per horizon)."""
        names = [v[0] for v in BACKTEST_VARIANTS]
        assert len(set(names)) == 6
        for name in set(names):
            assert names.count(name) == 2

    def test_two_horizons(self) -> None:
        """Test that every variant uses 24h or 7d."""
        horizons = {v[1] for v in BACKTEST_VARIANTS}
        assert horizons == {"24h", "7d"}

    def test_horizon_hours_consistent(self) -> None:
        """Test that horizon='24h' → 24 and horizon='7d' → 168."""
        for _, horizon, hours in BACKTEST_VARIANTS:
            if horizon == "24h":
                assert hours == 24
            else:
                assert hours == 168

    def test_variant_factory_returns_callable(self) -> None:
        """Test that _variant_factory returns a zero-arg callable."""
        for name, _, _ in BACKTEST_VARIANTS:
            factory = _variant_factory(name)
            model = factory()
            assert model is not None
            assert hasattr(model, "train")

    def test_variant_factory_unknown_raises(self) -> None:
        """Test that an unknown name raises ValueError."""
        with pytest.raises(ValueError, match="Unknown variant"):
            _variant_factory("bogus_model")

    def test_result_to_rows_produces_one_row_per_point(self) -> None:
        """Test that _result_to_rows yields one row per matched point."""
        result = _make_backtest_result(True)
        rows = _result_to_rows(result)
        # 2 iterations × 24 matched points = 48 rows
        assert len(rows) == 48

    def test_result_to_rows_skips_failed_iterations(self) -> None:
        """Test that failed iterations produce no rows."""
        result = _make_backtest_result(True)
        # Manually break one iteration
        result.iteration_results[0].error = "boom"
        rows = _result_to_rows(result)
        # Only iteration 1's 24 points remain
        assert len(rows) == 24

    def test_result_to_rows_repeats_iteration_metrics(self) -> None:
        """Test that metrics are repeated on every row of an iteration."""
        result = _make_backtest_result(True)
        rows = _result_to_rows(result)
        # All rows from iteration 0 have the same mae
        for row in rows[:24]:
            assert row.mae == 100.0


# ============================================================
# HOURLY 24H PREDICTION JOB
# ============================================================
class TestHourlyPredictionJob:
    """Tests for hourly_prediction_job()."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        """Test that a successful generation returns a summary dict."""
        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(
                horizon="24h", succeeded=True
            )
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            result = await hourly_prediction_job()

        assert result["horizon"] == "24h"
        assert result["model_name"] == "prophet"
        assert result["rows_generated"] == 24
        assert result["rows_saved"] == 24
        assert result["succeeded"] is True

    @pytest.mark.asyncio
    async def test_loads_model_from_settings(self) -> None:
        """Test that the job loads the model from settings.prophet_24h_model_path."""
        from app.config import settings

        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(succeeded=True)
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await hourly_prediction_job()

        mock_model.load.assert_called_once_with(
            settings.prophet_24h_model_path
        )

    @pytest.mark.asyncio
    async def test_raises_when_model_not_trained(self) -> None:
        """Test that a model not marked as trained raises RuntimeError."""
        mock_model = MagicMock()
        mock_model.load = MagicMock()
        mock_model.is_model_trained = MagicMock(return_value=False)

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ):
            with pytest.raises(RuntimeError, match="not marked as trained"):
                await hourly_prediction_job()

    @pytest.mark.asyncio
    async def test_raises_when_generation_fails(self) -> None:
        """Test that a failed generation raises RuntimeError."""
        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(
                succeeded=False, error="no data"
            )
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="no data"):
                await hourly_prediction_job()

    @pytest.mark.asyncio
    async def test_propagates_model_load_error(self) -> None:
        """Test that a FileNotFoundError from model.load propagates."""
        mock_model = MagicMock()
        mock_model.load = MagicMock(
            side_effect=FileNotFoundError("missing model")
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ):
            with pytest.raises(FileNotFoundError, match="missing model"):
                await hourly_prediction_job()


# ============================================================
# DAILY 7D PREDICTION JOB
# ============================================================
class TestDaily7dPredictionJob:
    """Tests for daily_7d_prediction_job()."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        """Test that a successful 7d generation returns a summary dict."""
        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(
                horizon="7d",
                succeeded=True,
                rows_generated=7,
                rows_saved=7,
            )
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            result = await daily_7d_prediction_job()

        assert result["horizon"] == "7d"
        assert result["model_name"] == "prophet"
        assert result["rows_generated"] == 7
        assert result["rows_saved"] == 7
        assert result["succeeded"] is True

    @pytest.mark.asyncio
    async def test_loads_model_from_settings(self) -> None:
        """Test that the 7d job loads from settings.prophet_7d_model_path."""
        from app.config import settings

        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(horizon="7d", succeeded=True)
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_7d_prediction_job()

        mock_model.load.assert_called_once_with(
            settings.prophet_7d_model_path
        )

    @pytest.mark.asyncio
    async def test_raises_when_model_not_trained(self) -> None:
        """Test that an untrained model raises RuntimeError."""
        mock_model = MagicMock()
        mock_model.load = MagicMock()
        mock_model.is_model_trained = MagicMock(return_value=False)

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ):
            with pytest.raises(RuntimeError, match="not marked as trained"):
                await daily_7d_prediction_job()

    @pytest.mark.asyncio
    async def test_raises_when_generation_fails(self) -> None:
        """Test that a failed 7d generation raises RuntimeError."""
        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(
                horizon="7d",
                succeeded=False,
                error="insufficient data",
            )
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ), patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            with pytest.raises(RuntimeError, match="insufficient data"):
                await daily_7d_prediction_job()

    @pytest.mark.asyncio
    async def test_propagates_model_load_error(self) -> None:
        """Test that a FileNotFoundError from model.load propagates."""
        mock_model = MagicMock()
        mock_model.load = MagicMock(
            side_effect=FileNotFoundError("missing 7d model")
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ):
            with pytest.raises(FileNotFoundError, match="missing 7d model"):
                await daily_7d_prediction_job()

    @pytest.mark.asyncio
    async def test_uses_7d_horizon_and_confidence(self) -> None:
        """Test that PredictionGenerator is constructed with 7d params."""
        mock_model = _make_trained_model()

        mock_generator = MagicMock()
        mock_generator.generate = AsyncMock(
            return_value=_make_generation_result(horizon="7d", succeeded=True)
        )

        with patch(
            "app.scheduler.jobs.ProphetModel", return_value=mock_model
        ), patch(
            "app.scheduler.jobs.PredictionGenerator",
            return_value=mock_generator,
        ) as mock_gen_class, patch(
            "app.scheduler.jobs.session_scope",
            return_value=_session_scope_mock(),
        ):
            await daily_7d_prediction_job()

        call_kwargs = mock_gen_class.call_args.kwargs
        assert call_kwargs["horizon"] == "7d"
        assert call_kwargs["horizon_hours"] == 168
        assert call_kwargs["confidence"] == 0.85
        assert call_kwargs["history_hours"] == 2160


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestJobConstants:
    """Tests for module constants."""

    def test_daily_retrain_job_name(self) -> None:
        """Test that JOB_DAILY_RETRAIN has the expected value."""
        assert JOB_DAILY_RETRAIN == "daily_retrain"

    def test_hourly_job_name(self) -> None:
        """Test that JOB_HOURLY_PREDICTION has the expected value."""
        assert JOB_HOURLY_PREDICTION == "hourly_prediction"

    def test_daily_7d_job_name(self) -> None:
        """Test that JOB_DAILY_7D_PREDICTION has the expected value."""
        assert JOB_DAILY_7D_PREDICTION == "daily_7d_prediction"

    def test_daily_backtest_job_name(self) -> None:
        """Test that JOB_DAILY_BACKTEST has the expected value."""
        assert JOB_DAILY_BACKTEST == "daily_backtest"