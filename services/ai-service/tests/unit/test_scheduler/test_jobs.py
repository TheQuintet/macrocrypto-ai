"""Unit tests for the scheduler jobs module.

These tests mock the Prophet model, the repository, and the
generator to isolate the job orchestration logic (model load,
session opening, result evaluation).

Test organization:
    - TestHourlyPredictionJob: 24h job happy path + failure paths
    - TestDaily7dPredictionJob: 7d job happy path + failure paths
    - TestJobConstants: module constants
"""

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.prediction.generator import GenerationResult
from app.scheduler.jobs import (
    JOB_DAILY_7D_PREDICTION,
    JOB_HOURLY_PREDICTION,
    daily_7d_prediction_job,
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

        # Assert PredictionGenerator was called with 7d parameters
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

    def test_hourly_job_name(self) -> None:
        """Test that JOB_HOURLY_PREDICTION has the expected value."""
        assert JOB_HOURLY_PREDICTION == "hourly_prediction"

    def test_daily_7d_job_name(self) -> None:
        """Test that JOB_DAILY_7D_PREDICTION has the expected value."""
        assert JOB_DAILY_7D_PREDICTION == "daily_7d_prediction"