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
    - TestFetchLatestMetricsBatch: batch read (T5.5)
    - TestFetchMarketBreakdown: per-condition aggregates (T5.5)
    - TestFetchBestModelByMae: best-model lookup (M6a)
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

        bad_rows = [_make_perf_row(horizon="bogus")]

        with pytest.raises(ValueError, match="invalid horizon"):
            await repo.save_performance_rows(bad_rows)

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


# ============================================================
# BATCH — FETCH LATEST METRICS
# ============================================================
class TestFetchLatestMetricsBatch:
    """Tests for fetch_latest_metrics_batch()."""

    @pytest.mark.asyncio
    async def test_returns_one_row_per_model_horizon(self) -> None:
        """Test that duplicate (model, horizon) rows are deduplicated.

        The repository relies on the SQL ORDER BY (model_name ASC,
        horizon ASC, forecast_date DESC) to put the newest row first
        for each group.
        """
        now = datetime.now(timezone.utc)
        rows = [
            # prophet_fresh / 24h — newest first
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "model_version": "1.0.0",
                "forecast_date": now,
                "mae": 100.0,
                "rmse": 120.0,
                "mape": 1.5,
            },
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "model_version": "1.0.0",
                "forecast_date": now - timedelta(days=1),
                "mae": 200.0,
                "rmse": 220.0,
                "mape": 2.5,
            },
            # prophet_fresh / 7d
            {
                "model_name": "prophet_fresh",
                "horizon": "7d",
                "model_version": "1.0.0",
                "forecast_date": now,
                "mae": 300.0,
                "rmse": 320.0,
                "mape": 3.5,
            },
        ]

        # The repository issues two queries:
        # 1. latest rows (this list)
        # 2. sample counts (returns a small dict)
        mock_result_rows = MagicMock()
        mock_result_rows.mappings.return_value.all.return_value = rows

        mock_result_counts = MagicMock()
        mock_result_counts.mappings.return_value.all.return_value = [
            {"model_name": "prophet_fresh", "horizon": "24h", "samples": 480},
            {"model_name": "prophet_fresh", "horizon": "7d", "samples": 168},
        ]

        session = AsyncMock()
        session.execute.side_effect = [mock_result_rows, mock_result_counts]

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_metrics_batch(days=30)

        # Two unique (model, horizon) pairs
        assert len(result) == 2
        names_horizons = {(r["model_name"], r["horizon"]) for r in result}
        assert names_horizons == {
            ("prophet_fresh", "24h"),
            ("prophet_fresh", "7d"),
        }

    @pytest.mark.asyncio
    async def test_picks_latest_row_per_group(self) -> None:
        """Test that the newest row (first in ORDER BY DESC) is kept."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "model_version": "1.0.0",
                "forecast_date": now,
                "mae": 100.0,
                "rmse": 120.0,
                "mape": 1.5,
            },
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "model_version": "1.0.0",
                "forecast_date": now - timedelta(days=1),
                "mae": 999.0,  # would be wrong if kept
                "rmse": 999.0,
                "mape": 999.0,
            },
        ]

        mock_result_rows = MagicMock()
        mock_result_rows.mappings.return_value.all.return_value = rows
        mock_result_counts = MagicMock()
        mock_result_counts.mappings.return_value.all.return_value = [
            {"model_name": "prophet_fresh", "horizon": "24h", "samples": 480},
        ]

        session = AsyncMock()
        session.execute.side_effect = [mock_result_rows, mock_result_counts]

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_metrics_batch(days=30)

        assert len(result) == 1
        assert result[0]["mae"] == 100.0

    @pytest.mark.asyncio
    async def test_samples_field_populated(self) -> None:
        """Test that `samples` is merged in from the second query."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "model_version": "1.0.0",
                "forecast_date": now,
                "mae": 100.0,
                "rmse": 120.0,
                "mape": 1.5,
            },
        ]
        mock_result_rows = MagicMock()
        mock_result_rows.mappings.return_value.all.return_value = rows
        mock_result_counts = MagicMock()
        mock_result_counts.mappings.return_value.all.return_value = [
            {"model_name": "prophet_fresh", "horizon": "24h", "samples": 480},
        ]

        session = AsyncMock()
        session.execute.side_effect = [mock_result_rows, mock_result_counts]

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_metrics_batch(days=30)

        assert result[0]["samples"] == 480

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        """Test that an empty result returns an empty list."""
        mock_result_rows = MagicMock()
        mock_result_rows.mappings.return_value.all.return_value = []
        mock_result_counts = MagicMock()
        mock_result_counts.mappings.return_value.all.return_value = []

        session = AsyncMock()
        session.execute.side_effect = [mock_result_rows, mock_result_counts]

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_metrics_batch(days=30)

        assert result == []

    @pytest.mark.asyncio
    async def test_horizon_filter_passes(self) -> None:
        """Test that the horizon filter is forwarded without error."""
        mock_result_rows = MagicMock()
        mock_result_rows.mappings.return_value.all.return_value = []
        mock_result_counts = MagicMock()
        mock_result_counts.mappings.return_value.all.return_value = []

        session = AsyncMock()
        session.execute.side_effect = [mock_result_rows, mock_result_counts]

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_metrics_batch(
            days=30, horizon="24h"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_model_name_filter_passes(self) -> None:
        """Test that the model_name filter is forwarded without error."""
        mock_result_rows = MagicMock()
        mock_result_rows.mappings.return_value.all.return_value = []
        mock_result_counts = MagicMock()
        mock_result_counts.mappings.return_value.all.return_value = []

        session = AsyncMock()
        session.execute.side_effect = [mock_result_rows, mock_result_counts]

        repo = PerformanceRepository(session)
        result = await repo.fetch_latest_metrics_batch(
            days=30, model_name="prophet_fresh"
        )

        assert result == []


# ============================================================
# MARKET BREAKDOWN
# ============================================================
class TestFetchMarketBreakdown:
    """Tests for fetch_market_breakdown()."""

    @pytest.mark.asyncio
    async def test_returns_one_row_per_condition(self) -> None:
        """Test that each market condition gets its own row."""
        rows = [
            {
                "market_condition": "bull",
                "mae": 450.0,
                "rmse": 500.0,
                "mape": 1.0,
                "samples": 300,
            },
            {
                "market_condition": "bear",
                "mae": 550.0,
                "rmse": 600.0,
                "mape": 1.2,
                "samples": 200,
            },
            {
                "market_condition": "volatile",
                "mae": 600.0,
                "rmse": 700.0,
                "mape": 1.4,
                "samples": 150,
            },
        ]
        session = _mock_session_with_rows(rows)
        repo = PerformanceRepository(session)

        result = await repo.fetch_market_breakdown(
            "24h", "prophet_fresh", days=30
        )

        assert len(result) == 3
        conditions = {r["market_condition"] for r in result}
        assert conditions == {"bull", "bear", "volatile"}

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        """Test that no rows returns an empty list."""
        session = _mock_session_with_rows([])
        repo = PerformanceRepository(session)

        result = await repo.fetch_market_breakdown(
            "24h", "prophet_fresh", days=30
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_aggregates_are_floats(self) -> None:
        """Test that the aggregate values come through as floats."""
        rows = [
            {
                "market_condition": "bull",
                "mae": 450.5,
                "rmse": 500.25,
                "mape": 1.05,
                "samples": 300,
            },
        ]
        session = _mock_session_with_rows(rows)
        repo = PerformanceRepository(session)

        result = await repo.fetch_market_breakdown(
            "24h", "prophet_fresh", days=30
        )

        assert result[0]["mae"] == 450.5
        assert result[0]["rmse"] == 500.25
        assert result[0]["mape"] == 1.05
        assert result[0]["samples"] == 300


# ============================================================
# FETCH BEST MODEL BY MAE (M6a)
# ============================================================
class TestFetchBestModelByMae:
    """Tests for fetch_best_model_by_mae()."""

    @pytest.mark.asyncio
    async def test_returns_model_name_when_found(self) -> None:
        """Test that the model name is returned when a row exists."""
        row = {"model_name": "prophet_fresh", "mean_mae": 100.0}

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = row
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        result = await repo.fetch_best_model_by_mae("24h", days=30)

        assert result == "prophet_fresh"

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        """Test that None is returned when no MAE data exists."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        result = await repo.fetch_best_model_by_mae("24h", days=30)

        assert result is None

    @pytest.mark.asyncio
    async def test_model_names_filter_does_not_error(self) -> None:
        """Test that the optional model_names filter works end-to-end."""
        row = {"model_name": "xgboost_fresh", "mean_mae": 90.0}

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = row
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        result = await repo.fetch_best_model_by_mae(
            "24h",
            days=30,
            model_names=["prophet_fresh", "xgboost_fresh"],
        )

        assert result == "xgboost_fresh"

    @pytest.mark.asyncio
    async def test_statement_has_expected_clauses(self) -> None:
        """Test that the SELECT groups by model and orders by mean MAE."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        session.execute.return_value = mock_result

        repo = PerformanceRepository(session)
        await repo.fetch_best_model_by_mae("24h", days=30)

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "prediction_performance.model_name" in compiled
        assert "avg(prediction_performance.mae)" in compiled
        assert "GROUP BY prediction_performance.model_name" in compiled
        assert "ORDER BY avg(prediction_performance.mae) ASC" in compiled
        assert "LIMIT 1" in compiled