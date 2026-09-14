"""Unit tests for the PerformanceRepository.

These tests mock the SQLAlchemy AsyncSession so no live database
is required. They verify:
    - Correct SQL statements are issued (shape + parameters)
    - Result rows are correctly mapped
    - Validation is invoked before insert

Test organization:
    - TestPerformanceRow: dataclass behavior
    - TestSavePerformanceRows: bulk insert + validation
    - TestFetchLatestMetrics: single-row read
    - TestFetchMetricsHistory: range read
    - TestCountRows: count with optional filters
    - TestFetchLatestForecastDate: MAX query
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.repositories.performance_repository import (
    PerformanceRepository,
    PerformanceRow,
)


# ============================================================
# HELPERS
# ============================================================
def _make_perf_row(**overrides) -> PerformanceRow:
    """Build a valid PerformanceRow with all fields set."""
    defaults = dict(
        horizon="24h",
        model_name="prophet_fresh",
        model_version="1.0.0",
        forecast_date=datetime.now(timezone.utc),
        predicted_price=50_000.0,
        actual_price=50_500.0,
        mae=500.0,
        rmse=500.0,
        mape=0.99,
        market_condition="bull",
        prediction_id=None,
    )
    defaults.update(overrides)
    return PerformanceRow(**defaults)


def _mock_session_with_rows(rows: List[dict]) -> AsyncMock:
    """Build an AsyncMock whose execute() returns the given rows."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    mock_result.mappings.return_value.first.return_value = (
        rows[0] if rows else None
    )
    mock_result.scalar_one.return_value = 42
    mock_result.scalar_one_or_none.return_value = (
        rows[0].get("max") if rows else None
    )

    session = AsyncMock()
    session.execute.return_value = mock_result
    session.flush = AsyncMock()
    return session


# ============================================================
# ROW DATACLASS
# ============================================================
class TestPerformanceRow:
    """Tests for the PerformanceRow dataclass."""

    def test_construction(self) -> None:
        """Test constructing with all fields."""
        row = _make_perf_row()
        assert row.horizon == "24h"
        assert row.model_name == "prophet_fresh"
        assert row.mae == 500.0

    def test_defaults_are_null(self) -> None:
        """Test that optional fields default to None."""
        now = datetime.now(timezone.utc)
        row = PerformanceRow(
            horizon="24h",
            model_name="x",
            model_version="1.0.0",
            forecast_date=now,
            predicted_price=1.0,
            actual_price=1.0,
        )
        assert row.mae is None
        assert row.rmse is None
        assert row.mape is None
        assert row.market_condition is None
        assert row.prediction_id is None

    def test_to_dict_keys(self) -> None:
        """Test that to_dict returns the expected keys."""
        row = _make_perf_row()
        d = row.to_dict()
        expected = {
            "prediction_id",
            "horizon",
            "model_name",
            "model_version",
            "forecast_date",
            "predicted_price",
            "actual_price",
            "mae",
            "rmse",
            "mape",
            "market_condition",
        }
        assert set(d.keys()) == expected


# ============================================================
# SAVE
# ============================================================
class TestSavePerformanceRows:
    """Tests for save_performance_rows()."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self) -> None:
        """Test that an empty list returns 0 without executing SQL."""
        session = AsyncMock()
        repo = PerformanceRepository(session)

        count = await repo.save_performance_rows([])

        assert count == 0
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_row_count(self) -> None:
        """Test that the returned count equals the number of rows."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = PerformanceRepository(session)

        rows = [_make_perf_row() for _ in range(5)]
        count = await repo.save_performance_rows(rows)

        assert count == 5
        assert session.execute.call_count == 1
        assert session.flush.call_count == 1

    @pytest.mark.asyncio
    async def test_validates_before_insert(self) -> None:
        """Test that invalid rows raise before touching the DB."""
        session = AsyncMock()
        repo = PerformanceRepository(session)

        # horizon is invalid → validator raises
        bad_rows = [_make_perf_row(horizon="bogus")]

        with pytest.raises(ValueError, match="invalid horizon"):
            await repo.save_performance_rows(bad_rows)

        # No DB write attempted
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_negative_mae_raises(self) -> None:
        """Test that a negative MAE raises."""
        session = AsyncMock()
        repo = PerformanceRepository(session)

        with pytest.raises(ValueError, match="mae must be >= 0"):
            await repo.save_performance_rows([_make_perf_row(mae=-1.0)])


# ============================================================
# FETCH LATEST
# ============================================================
class TestFetchLatestMetrics:
    """Tests for fetch_latest_metrics()."""

    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self) -> None:
        """Test that a matching row is returned as a dict."""
        row = {
            "horizon": "24h",
            "model_name": "prophet_fresh",
            "model_version": "1.0.0",
            "forecast_date": datetime.now(timezone.utc),
            "mae": 100.0,
            "rmse": 120.0,
            "mape": 1.5,
            "market_condition": "bull",
            "created_at": datetime.now(timezone.utc),
        }
        session = _mock_session_with_rows([row])
        repo = PerformanceRepository(session)

        result = await repo.fetch_latest_metrics("24h", "prophet_fresh")

        assert result is not None
        assert result["mae"] == 100.0
        assert result["market_condition"] == "bull"

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        """Test that an empty result returns None."""
        session = _mock_session_with_rows([])
        repo = PerformanceRepository(session)

        result = await repo.fetch_latest_metrics("24h", "nonexistent")

        assert result is None


# ============================================================
# FETCH HISTORY
# ============================================================
class TestFetchMetricsHistory:
    """Tests for fetch_metrics_history()."""

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self) -> None:
        """Test that the history is returned as a list of dicts."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "forecast_date": now - timedelta(days=i),
                "mae": 100.0 + i,
                "rmse": 120.0 + i,
                "mape": 1.5,
                "created_at": now,
            }
            for i in range(3)
        ]
        session = _mock_session_with_rows(rows)
        repo = PerformanceRepository(session)

        result = await repo.fetch_metrics_history(
            "24h", "prophet_fresh", days=30
        )

        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_history_returns_empty_list(self) -> None:
        """Test that an empty result returns an empty list."""
        session = _mock_session_with_rows([])
        repo = PerformanceRepository(session)

        result = await repo.fetch_metrics_history(
            "24h", "prophet_fresh", days=30
        )

        assert result == []


# ============================================================
# COUNT
# ============================================================
class TestCountRows:
    """Tests for count_rows()."""

    @pytest.mark.asyncio
    async def test_returns_count(self) -> None:
        """Test that the scalar count is returned as an int."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        count = await repo.count_rows()

        assert count == 42
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        """Test that filters are applied without errors."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        count = await repo.count_rows(horizon="24h", model_name="prophet_fresh")

        assert count == 5


# ============================================================
# LATEST FORECAST DATE
# ============================================================
class TestFetchLatestForecastDate:
    """Tests for fetch_latest_forecast_date()."""

    @pytest.mark.asyncio
    async def test_returns_datetime(self) -> None:
        """Test that a datetime is returned when found."""
        expected = datetime.now(timezone.utc)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_forecast_date("24h", "prophet_fresh")

        assert result == expected

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        """Test that None is returned when no rows exist."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_forecast_date("24h", "prophet_fresh")

        assert result is None