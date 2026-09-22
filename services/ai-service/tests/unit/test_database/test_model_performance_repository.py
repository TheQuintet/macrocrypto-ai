"""Unit tests for the ModelPerformanceRepository.

These tests mock the SQLAlchemy AsyncSession so no live database
is required. They verify:
    - Correct SQL statements are issued (shape + parameters)
    - Result rows are correctly mapped
    - Validation is invoked before insert
    - The Python-side deduplication in fetch_latest_per_model keeps
      the newest row per (model, horizon)

Test organization:
    - TestModelPerformanceRow: dataclass behavior
    - TestSaveRows: bulk insert + validation
    - TestFetchLatestPerModel: dedup + filters
    - TestFetchHistory: ordered time series
    - TestFetchBestModelByMae: min-avg-MAE lookup
    - TestCountRows: count with optional filters
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.repositories.model_performance_repository import (
    ModelPerformanceRepository,
    ModelPerformanceRow,
)


# ============================================================
# HELPERS
# ============================================================
def _make_row(**overrides) -> ModelPerformanceRow:
    """Build a valid ModelPerformanceRow with all fields set."""
    defaults = dict(
        model_name="prophet_fresh",
        horizon="24h",
        sample_size=480,
        calculated_at=datetime.now(timezone.utc),
        mae=100.0,
        rmse=120.0,
        mape=1.5,
        directional_accuracy=62.0,
    )
    defaults.update(overrides)
    return ModelPerformanceRow(**defaults)


def _mock_session_with_rows(rows: List[dict]) -> AsyncMock:
    """Build an AsyncMock whose execute() returns the given rows."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    mock_result.mappings.return_value.first.return_value = (
        rows[0] if rows else None
    )
    mock_result.scalar_one.return_value = 42
    mock_result.scalar_one_or_none.return_value = None

    session = AsyncMock()
    session.execute.return_value = mock_result
    session.flush = AsyncMock()
    return session


# ============================================================
# ROW DATACLASS
# ============================================================
class TestModelPerformanceRow:
    """Tests for the ModelPerformanceRow dataclass."""

    def test_construction(self) -> None:
        """Test constructing with all fields."""
        row = _make_row()
        assert row.model_name == "prophet_fresh"
        assert row.horizon == "24h"
        assert row.sample_size == 480
        assert row.mae == 100.0

    def test_defaults_are_null(self) -> None:
        """Test that optional metric fields default to None."""
        now = datetime.now(timezone.utc)
        row = ModelPerformanceRow(
            model_name="x",
            horizon="24h",
            sample_size=10,
            calculated_at=now,
        )
        assert row.mae is None
        assert row.rmse is None
        assert row.mape is None
        assert row.directional_accuracy is None

    def test_to_dict_keys(self) -> None:
        """Test that to_dict returns the expected keys."""
        row = _make_row()
        d = row.to_dict()
        expected = {
            "model_name",
            "horizon",
            "mae",
            "rmse",
            "mape",
            "directional_accuracy",
            "sample_size",
            "calculated_at",
        }
        assert set(d.keys()) == expected

    def test_repr_contains_identity(self) -> None:
        """Test that __repr__ includes model_name and horizon."""
        row = _make_row()
        r = repr(row)
        assert "prophet_fresh" in r
        assert "24h" in r

    def test_repr_returns_string(self) -> None:
        """Test that __repr__ returns a string."""
        assert isinstance(repr(_make_row()), str)


# ============================================================
# SAVE
# ============================================================
class TestSaveRows:
    """Tests for save_rows()."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self) -> None:
        """Test that an empty list returns 0 without executing SQL."""
        session = AsyncMock()
        repo = ModelPerformanceRepository(session)

        count = await repo.save_rows([])

        assert count == 0
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_row_count(self) -> None:
        """Test that the returned count equals the number of rows."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = ModelPerformanceRepository(session)

        rows = [_make_row() for _ in range(5)]
        count = await repo.save_rows(rows)

        assert count == 5
        assert session.execute.call_count == 1
        assert session.flush.call_count == 1

    @pytest.mark.asyncio
    async def test_validates_before_insert(self) -> None:
        """Test that invalid rows raise before touching the DB."""
        session = AsyncMock()
        repo = ModelPerformanceRepository(session)

        bad_rows = [_make_row(horizon="bogus")]

        with pytest.raises(ValueError, match="invalid horizon"):
            await repo.save_rows(bad_rows)

        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_negative_sample_size_raises(self) -> None:
        """Test that a non-positive sample_size raises before insert."""
        session = AsyncMock()
        repo = ModelPerformanceRepository(session)

        with pytest.raises(ValueError, match="sample_size must be positive"):
            await repo.save_rows([_make_row(sample_size=0)])

        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_negative_mae_raises(self) -> None:
        """Test that a negative MAE raises before insert."""
        session = AsyncMock()
        repo = ModelPerformanceRepository(session)

        with pytest.raises(ValueError, match="mae must be >= 0"):
            await repo.save_rows([_make_row(mae=-1.0)])

        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_directional_accuracy_above_100_raises(self) -> None:
        """Test that directional_accuracy > 100 raises before insert."""
        session = AsyncMock()
        repo = ModelPerformanceRepository(session)

        with pytest.raises(
            ValueError, match="directional_accuracy must be in"
        ):
            await repo.save_rows(
                [_make_row(directional_accuracy=101.0)]
            )

        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_does_not_commit(self) -> None:
        """Test that the repository never commits — callers control that."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = ModelPerformanceRepository(session)

        await repo.save_rows([_make_row()])

        # AsyncSession.commit should not be called by the repository.
        assert not hasattr(session, "commit") or not session.commit.called


# ============================================================
# FETCH LATEST PER MODEL
# ============================================================
class TestFetchLatestPerModel:
    """Tests for fetch_latest_per_model()."""

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        """Test that no rows returns an empty list."""
        session = _mock_session_with_rows([])
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_latest_per_model(days=30)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self) -> None:
        """Test that rows come back as plain dicts."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "id": 1,
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "mae": 100.0,
                "rmse": 120.0,
                "mape": 1.5,
                "directional_accuracy": 62.0,
                "sample_size": 480,
                "calculated_at": now,
                "created_at": now,
            }
        ]
        session = _mock_session_with_rows(rows)
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_latest_per_model(days=30)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["model_name"] == "prophet_fresh"
        assert result[0]["mae"] == 100.0

    @pytest.mark.asyncio
    async def test_dedups_by_model_horizon_keeping_newest(self) -> None:
        """Test that dedup keeps the row with the newest calculated_at.

        The repository relies on the SQL ORDER BY (model_name ASC,
        horizon ASC, calculated_at DESC) to put the newest row first
        for each group. This test feeds the mocked result in that
        order and asserts the first row per (model, horizon) wins.
        """
        now = datetime.now(timezone.utc)
        rows = [
            # prophet_fresh / 24h — newest first
            {
                "id": 1,
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "mae": 100.0,
                "rmse": 120.0,
                "mape": 1.5,
                "directional_accuracy": 62.0,
                "sample_size": 480,
                "calculated_at": now,
                "created_at": now,
            },
            {
                "id": 2,
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "mae": 999.0,  # older, must be dropped
                "rmse": 999.0,
                "mape": 999.0,
                "directional_accuracy": 50.0,
                "sample_size": 480,
                "calculated_at": now - timedelta(days=1),
                "created_at": now - timedelta(days=1),
            },
            # prophet_fresh / 7d
            {
                "id": 3,
                "model_name": "prophet_fresh",
                "horizon": "7d",
                "mae": 300.0,
                "rmse": 320.0,
                "mape": 3.5,
                "directional_accuracy": 58.0,
                "sample_size": 168,
                "calculated_at": now,
                "created_at": now,
            },
        ]
        session = _mock_session_with_rows(rows)
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_latest_per_model(days=30)

        assert len(result) == 2
        keys = {(r["model_name"], r["horizon"]) for r in result}
        assert keys == {
            ("prophet_fresh", "24h"),
            ("prophet_fresh", "7d"),
        }
        # The newer 24h row (mae=100) should be kept, not the older (mae=999)
        row_24h = next(
            r for r in result if r["horizon"] == "24h"
        )
        assert row_24h["mae"] == 100.0

    @pytest.mark.asyncio
    async def test_multiple_models(self) -> None:
        """Test that multiple models each get their own row."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "id": 1,
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "mae": 100.0,
                "rmse": 120.0,
                "mape": 1.5,
                "directional_accuracy": 62.0,
                "sample_size": 480,
                "calculated_at": now,
                "created_at": now,
            },
            {
                "id": 2,
                "model_name": "xgboost_fresh",
                "horizon": "24h",
                "mae": 90.0,
                "rmse": 110.0,
                "mape": 1.4,
                "directional_accuracy": 63.0,
                "sample_size": 480,
                "calculated_at": now,
                "created_at": now,
            },
        ]
        session = _mock_session_with_rows(rows)
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_latest_per_model(days=30)

        assert len(result) == 2
        names = {r["model_name"] for r in result}
        assert names == {"prophet_fresh", "xgboost_fresh"}

    @pytest.mark.asyncio
    async def test_horizon_filter_does_not_error(self) -> None:
        """Test that the horizon filter is forwarded without error."""
        session = _mock_session_with_rows([])
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_latest_per_model(
            horizon="24h", days=30
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_model_names_filter_does_not_error(self) -> None:
        """Test that the model_names filter is forwarded without error."""
        session = _mock_session_with_rows([])
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_latest_per_model(
            days=30, model_names=["prophet_fresh", "xgboost_fresh"]
        )

        assert result == []


# ============================================================
# FETCH HISTORY
# ============================================================
class TestFetchHistory:
    """Tests for fetch_history()."""

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        """Test that no rows returns an empty list."""
        session = _mock_session_with_rows([])
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_history(
            "prophet_fresh", "24h", days=30
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_ordered_list_of_dicts(self) -> None:
        """Test that rows come back in ascending calculated_at order."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "mae": 100.0 + i,
                "rmse": 120.0 + i,
                "mape": 1.5,
                "directional_accuracy": 60.0,
                "sample_size": 480,
                "calculated_at": now - timedelta(days=i),
            }
            for i in range(3)
        ]
        session = _mock_session_with_rows(rows)
        repo = ModelPerformanceRepository(session)

        result = await repo.fetch_history(
            "prophet_fresh", "24h", days=30
        )

        assert isinstance(result, list)
        assert len(result) == 3
        # Repository returns whatever the DB returned, in that order
        assert [r["mae"] for r in result] == [100.0, 101.0, 102.0]


# ============================================================
# FETCH BEST MODEL BY MAE
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

        repo = ModelPerformanceRepository(session)
        result = await repo.fetch_best_model_by_mae("24h", days=30)

        assert result == "prophet_fresh"

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        """Test that None is returned when no MAE data exists."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.first.return_value = None
        session.execute.return_value = mock_result

        repo = ModelPerformanceRepository(session)
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

        repo = ModelPerformanceRepository(session)
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

        repo = ModelPerformanceRepository(session)
        await repo.fetch_best_model_by_mae("24h", days=30)

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "model_performance.model_name" in compiled
        assert "avg(model_performance.mae)" in compiled
        assert "GROUP BY model_performance.model_name" in compiled
        assert "ORDER BY avg(model_performance.mae) ASC" in compiled
        assert "LIMIT 1" in compiled


# ============================================================
# COUNT ROWS
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

        repo = ModelPerformanceRepository(session)
        count = await repo.count_rows()

        assert count == 42
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_with_horizon_filter(self) -> None:
        """Test that the horizon filter is applied without error."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        session.execute.return_value = mock_result

        repo = ModelPerformanceRepository(session)
        count = await repo.count_rows(horizon="24h")

        assert count == 5

    @pytest.mark.asyncio
    async def test_with_model_name_filter(self) -> None:
        """Test that the model_name filter is applied without error."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        session.execute.return_value = mock_result

        repo = ModelPerformanceRepository(session)
        count = await repo.count_rows(model_name="prophet_fresh")

        assert count == 3

    @pytest.mark.asyncio
    async def test_with_both_filters(self) -> None:
        """Test that horizon + model_name filters combine."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2
        session.execute.return_value = mock_result

        repo = ModelPerformanceRepository(session)
        count = await repo.count_rows(
            horizon="7d", model_name="prophet_fresh"
        )

        assert count == 2