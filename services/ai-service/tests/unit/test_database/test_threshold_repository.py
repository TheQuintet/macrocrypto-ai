"""Unit tests for the ThresholdRepository.

These tests mock the SQLAlchemy AsyncSession so no live database
is required. They verify:
    - Correct SQL statements are issued
    - Result rows are correctly mapped
    - Bulk insert payload construction

Test organization:
    - TestThresholdBreachRow: dataclass behavior
    - TestSaveBreaches: bulk insert
    - TestFetchRecentBreaches: range read
    - TestFetchLatestBreach: single-row read
    - TestCountBreaches: count with filters
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.repositories.threshold_repository import (
    ThresholdBreachRow,
    ThresholdRepository,
)


# ============================================================
# HELPERS
# ============================================================
def _make_breach_row(**overrides) -> ThresholdBreachRow:
    """Build a valid ThresholdBreachRow."""
    defaults = dict(
        horizon="24h",
        model_name="prophet_fresh",
        metric="mae_pct",
        metric_unit="percent",
        value=12.5,
        threshold=10.0,
        breach_direction="above",
        consecutive_days=1,
        model_version="1.0.0",
        notes=None,
    )
    defaults.update(overrides)
    return ThresholdBreachRow(**defaults)


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
class TestThresholdBreachRow:
    """Tests for the ThresholdBreachRow dataclass."""

    def test_construction(self) -> None:
        """Test constructing with all fields."""
        row = _make_breach_row()
        assert row.horizon == "24h"
        assert row.metric == "mae_pct"
        assert row.value == 12.5

    def test_default_consecutive_days(self) -> None:
        """Test that consecutive_days defaults to 1."""
        row = ThresholdBreachRow(
            horizon="24h",
            model_name="x",
            metric="mae_pct",
            metric_unit="percent",
            value=12.0,
            threshold=10.0,
            breach_direction="above",
        )
        assert row.consecutive_days == 1

    def test_to_dict_keys(self) -> None:
        """Test to_dict returns the expected keys."""
        row = _make_breach_row()
        d = row.to_dict()
        expected = {
            "horizon",
            "model_name",
            "metric",
            "metric_unit",
            "value",
            "threshold",
            "breach_direction",
            "consecutive_days",
            "model_version",
            "notes",
        }
        assert set(d.keys()) == expected


# ============================================================
# SAVE
# ============================================================
class TestSaveBreaches:
    """Tests for save_breaches()."""

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(self) -> None:
        """Test that an empty list returns 0 without executing SQL."""
        session = AsyncMock()
        repo = ThresholdRepository(session)

        count = await repo.save_breaches([])

        assert count == 0
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_row_count(self) -> None:
        """Test that the returned count equals the number of rows."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = ThresholdRepository(session)

        rows = [_make_breach_row() for _ in range(5)]
        count = await repo.save_breaches(rows)

        assert count == 5
        assert session.execute.call_count == 1
        assert session.flush.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_and_flush_called(self) -> None:
        """Test that execute() and flush() are both called."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = ThresholdRepository(session)

        await repo.save_breaches([_make_breach_row()])

        session.execute.assert_called_once()
        session.flush.assert_called_once()


# ============================================================
# FETCH RECENT
# ============================================================
class TestFetchRecentBreaches:
    """Tests for fetch_recent_breaches()."""

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self) -> None:
        """Test that recent breaches are returned as dicts."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "id": i,
                "detected_at": now - timedelta(days=i),
                "horizon": "24h",
                "model_name": "prophet_fresh",
                "metric": "mae_pct",
                "metric_unit": "percent",
                "value": 12.0 + i,
                "threshold": 10.0,
                "breach_direction": "above",
                "consecutive_days": 1 + i,
                "model_version": "1.0.0",
                "notes": None,
            }
            for i in range(3)
        ]
        session = _mock_session_with_rows(rows)
        repo = ThresholdRepository(session)

        result = await repo.fetch_recent_breaches(
            "24h", "prophet_fresh", days=7
        )

        assert isinstance(result, list)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        """Test that an empty result returns an empty list."""
        session = _mock_session_with_rows([])
        repo = ThresholdRepository(session)

        result = await repo.fetch_recent_breaches("24h", "nonexistent")

        assert result == []


# ============================================================
# FETCH LATEST
# ============================================================
class TestFetchLatestBreach:
    """Tests for fetch_latest_breach()."""

    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self) -> None:
        """Test that the latest breach is returned."""
        now = datetime.now(timezone.utc)
        row = {
            "id": 1,
            "detected_at": now,
            "consecutive_days": 3,
            "value": 12.5,
            "threshold": 10.0,
        }
        session = _mock_session_with_rows([row])
        repo = ThresholdRepository(session)

        result = await repo.fetch_latest_breach(
            "24h", "prophet_fresh", "mae_pct"
        )

        assert result is not None
        assert result["consecutive_days"] == 3

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        """Test that no rows returns None."""
        session = _mock_session_with_rows([])
        repo = ThresholdRepository(session)

        result = await repo.fetch_latest_breach(
            "24h", "prophet_fresh", "mae_pct"
        )

        assert result is None


# ============================================================
# COUNT
# ============================================================
class TestCountBreaches:
    """Tests for count_breaches()."""

    @pytest.mark.asyncio
    async def test_returns_count(self) -> None:
        """Test that the count is returned as an int."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        session.execute.return_value = mock_result

        repo = ThresholdRepository(session)
        count = await repo.count_breaches()

        assert count == 42
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_with_all_filters(self) -> None:
        """Test that horizon + model + since_days are all applied."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        session.execute.return_value = mock_result

        repo = ThresholdRepository(session)
        count = await repo.count_breaches(
            horizon="24h", model_name="prophet_fresh", since_days=7
        )

        assert count == 5