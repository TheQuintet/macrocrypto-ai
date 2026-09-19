"""Unit tests for the scheduler jobs module.

These tests mock the Prophet model, the repository, and the
generator to isolate the job orchestration logic (model load,
session opening, result evaluation).

Test organization:
    - TestDailyRetrainJob: daily retrain of all 6 models
    - TestHourlyPredictionJob: 24h job happy path + failure paths
    - TestDaily7dPredictionJob: 7d job happy path + failure paths
    - TestJobConstants: module constants
"""

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.prediction.generator import GenerationResult
from app.scheduler.jobs import (
    JOB_DAILY_7D_PREDICTION,
    JOB_DAILY_RETRAIN,
    JOB_HOURLY_PREDICTION,
    daily_7d_prediction_job,
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
    """Build a synthetic training frame for the retrain job."""
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