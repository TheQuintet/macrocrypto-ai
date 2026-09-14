"""Unit tests for the scheduler jobs module.

These tests mock the Prophet model, the repository, and the
generator to isolate the job orchestration logic (model load,
session opening, result evaluation).

Test organization:
    - TestHourlyPredictionJob: happy path + failure paths
    - TestJobConstants: module constants
"""

from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.prediction.generator import GenerationResult
from app.scheduler.jobs import (
    JOB_HOURLY_PREDICTION,
    hourly_prediction_job,
)


# ============================================================
# HELPERS
# ============================================================
def _make_generation_result(
    succeeded: bool = True,
    rows_generated: int = 24,
    rows_saved: int = 24,
    error: str = None,
) -> GenerationResult:
    """Build a GenerationResult for tests."""
    return GenerationResult(
        horizon="24h",
        model_name="prophet",
        prediction_time=datetime.now(timezone.utc),
        rows_generated=rows_generated,
        rows_saved=rows_saved,
        confidence=0.85,
        elapsed_seconds=0.5,
        error=error if not succeeded else None,
    )


# ============================================================
# JOB TESTS
# ============================================================
class TestHourlyPredictionJob:
    """Tests for hourly_prediction_job()."""

    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        """Test that a successful generation returns a summary dict."""
        mock_model = MagicMock()
        mock_model.load = MagicMock()
        mock_model.is_model_trained = MagicMock(return_value=True)
        mock_model.get_name = MagicMock(return_value="prophet")

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
            "app.scheduler.jobs.session_scope"
        ) as mock_session_scope:
            # session_scope is an async context manager
            mock_session_scope.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock()
            )
            mock_session_scope.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

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

        mock_model = MagicMock()
        mock_model.load = MagicMock()
        mock_model.is_model_trained = MagicMock(return_value=True)
        mock_model.get_name = MagicMock(return_value="prophet")

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
            "app.scheduler.jobs.session_scope"
        ) as mock_session_scope:
            mock_session_scope.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock()
            )
            mock_session_scope.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

            await hourly_prediction_job()

        mock_model.load.assert_called_once_with(settings.prophet_24h_model_path)

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
        mock_model = MagicMock()
        mock_model.load = MagicMock()
        mock_model.is_model_trained = MagicMock(return_value=True)
        mock_model.get_name = MagicMock(return_value="prophet")

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
            "app.scheduler.jobs.session_scope"
        ) as mock_session_scope:
            mock_session_scope.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock()
            )
            mock_session_scope.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

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
# CONSTANTS TESTS
# ============================================================
class TestJobConstants:
    """Tests for module constants."""

    def test_job_name(self) -> None:
        """Test that JOB_HOURLY_PREDICTION has the expected value."""
        assert JOB_HOURLY_PREDICTION == "hourly_prediction"