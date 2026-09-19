"""Unit tests for the CorrelationRepository.

These tests mock the SQLAlchemy AsyncSession so no live database
is required. They verify:
    - Correct SQL statements are issued (shape + parameters)
    - Result rows are correctly mapped
    - Validation is invoked before insert
    - The Python-side deduplication in fetch_latest_per_indicator
      keeps the newest row per (indicator, window)
    - fetch_strongest_for_window picks the highest |coefficient|

Test organization:
    - TestCorrelationRow: dataclass behavior
    - TestSaveRows: bulk insert + validation
    - TestFetchLatestPerIndicator: dedup + filters
    - TestFetchHistory: ordered time series
    - TestFetchStrongestForWindow: max-abs selection
    - TestCountRows: count with optional filters
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.database.repositories.correlation_repository import (
    CorrelationRepository,
    CorrelationRow,
)


# ============================================================
# HELPERS
# ============================================================
def _make_row(**overrides) -> CorrelationRow:
    """Build a valid CorrelationRow with all fields set."""
    defaults = dict(
        indicator_name="inflation",
        window_days=90,
        calculated_at=datetime.now(timezone.utc),
        correlation_coefficient=-0.42,
        strength="medium",
        direction="negative",
        p_value=0.03,
    )
    defaults.update(overrides)
    return CorrelationRow(**defaults)


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


def _make_latest_row(
    indicator_name: str = "inflation",
    window_days: int = 90,
    coefficient: float = -0.42,
    strength: str = "medium",
    direction: str = "negative",
    p_value: Any = 0.03,
    calculated_at: Any = None,
) -> dict:
    """Build a row shaped like fetch_latest_per_indicator's result."""
    return {
        "indicator_name": indicator_name,
        "window_days": window_days,
        "calculated_at": calculated_at or datetime.now(timezone.utc),
        "correlation_coefficient": coefficient,
        "strength": strength,
        "direction": direction,
        "p_value": p_value,
        "created_at": datetime.now(timezone.utc),
    }


# ============================================================
# ROW DATACLASS
# ============================================================
class TestCorrelationRow:
    """Tests for the CorrelationRow dataclass."""

    def test_construction(self) -> None:
        """Test constructing with all fields."""
        row = _make_row()
        assert row.indicator_name == "inflation"
        assert row.window_days == 90
        assert row.correlation_coefficient == -0.42
        assert row.strength == "medium"
        assert row.direction == "negative"

    def test_p_value_defaults_to_none(self) -> None:
        """Test that p_value defaults to None."""
        now = datetime.now(timezone.utc)
        row = CorrelationRow(
            indicator_name="rates",
            window_days=30,
            calculated_at=now,
            correlation_coefficient=0.5,
            strength="medium",
            direction="positive",
        )
        assert row.p_value is None

    def test_to_dict_keys(self) -> None:
        """Test that to_dict returns the expected keys."""
        row = _make_row()
        d = row.to_dict()
        expected = {
            "indicator_name",
            "window_days",
            "calculated_at",
            "correlation_coefficient",
            "strength",
            "direction",
            "p_value",
        }
        assert set(d.keys()) == expected

    def test_repr_contains_identity(self) -> None:
        """Test that __repr__ includes indicator_name and window_days."""
        row = _make_row()
        r = repr(row)
        assert "inflation" in r
        assert "90" in r
        assert "medium" in r

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
        repo = CorrelationRepository(session)

        count = await repo.save_rows([])

        assert count == 0
        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_returns_row_count(self) -> None:
        """Test that the returned count equals the number of rows."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = CorrelationRepository(session)

        rows = [_make_row() for _ in range(5)]
        count = await repo.save_rows(rows)

        assert count == 5
        assert session.execute.call_count == 1
        assert session.flush.call_count == 1

    @pytest.mark.asyncio
    async def test_validates_before_insert(self) -> None:
        """Test that invalid rows raise before touching the DB."""
        session = AsyncMock()
        repo = CorrelationRepository(session)

        bad_rows = [_make_row(indicator_name="bogus")]

        with pytest.raises(ValueError, match="invalid indicator_name"):
            await repo.save_rows(bad_rows)

        assert session.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_invalid_window_raises(self) -> None:
        """Test that an invalid window_days raises."""
        session = AsyncMock()
        repo = CorrelationRepository(session)

        with pytest.raises(ValueError, match="invalid window_days"):
            await repo.save_rows([_make_row(window_days=45)])

    @pytest.mark.asyncio
    async def test_invalid_strength_raises(self) -> None:
        """Test that an invalid strength raises."""
        session = AsyncMock()
        repo = CorrelationRepository(session)

        with pytest.raises(ValueError, match="invalid strength"):
            await repo.save_rows([_make_row(strength="enormous")])

    @pytest.mark.asyncio
    async def test_invalid_direction_raises(self) -> None:
        """Test that an invalid direction raises."""
        session = AsyncMock()
        repo = CorrelationRepository(session)

        with pytest.raises(ValueError, match="invalid direction"):
            await repo.save_rows([_make_row(direction="neutral")])

    @pytest.mark.asyncio
    async def test_out_of_range_coefficient_raises(self) -> None:
        """Test that coefficient outside [-1, 1] raises."""
        session = AsyncMock()
        repo = CorrelationRepository(session)

        with pytest.raises(
            ValueError, match="correlation_coefficient must be in"
        ):
            await repo.save_rows(
                [_make_row(correlation_coefficient=1.5)]
            )

    @pytest.mark.asyncio
    async def test_out_of_range_p_value_raises(self) -> None:
        """Test that p_value outside [0, 1] raises."""
        session = AsyncMock()
        repo = CorrelationRepository(session)

        with pytest.raises(ValueError, match="p_value must be in"):
            await repo.save_rows([_make_row(p_value=1.5)])

    @pytest.mark.asyncio
    async def test_none_p_value_passes(self) -> None:
        """Test that None p_value is allowed."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = CorrelationRepository(session)

        count = await repo.save_rows([_make_row(p_value=None)])
        assert count == 1

    @pytest.mark.asyncio
    async def test_does_not_commit(self) -> None:
        """Test that the repository never commits."""
        session = AsyncMock()
        session.flush = AsyncMock()
        repo = CorrelationRepository(session)

        await repo.save_rows([_make_row()])

        assert not hasattr(session, "commit") or not session.commit.called


# ============================================================
# FETCH LATEST PER INDICATOR
# ============================================================
class TestFetchLatestPerIndicator:
    """Tests for fetch_latest_per_indicator()."""

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        """Test that no rows returns an empty list."""
        session = _mock_session_with_rows([])
        repo = CorrelationRepository(session)

        result = await repo.fetch_latest_per_indicator()

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self) -> None:
        """Test that rows come back as plain dicts."""
        rows = [_make_latest_row()]
        session = _mock_session_with_rows(rows)
        repo = CorrelationRepository(session)

        result = await repo.fetch_latest_per_indicator()

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["indicator_name"] == "inflation"
        assert result[0]["correlation_coefficient"] == -0.42

    @pytest.mark.asyncio
    async def test_dedups_by_indicator_window_keeping_newest(self) -> None:
        """Test that dedup keeps the row with the newest calculated_at.

        The repository relies on the SQL ORDER BY (indicator_name ASC,
        window_days ASC, calculated_at DESC) to put the newest row
        first for each group.
        """
        now = datetime.now(timezone.utc)
        rows = [
            # inflation / 90d — newest first
            _make_latest_row(
                indicator_name="inflation",
                window_days=90,
                coefficient=-0.42,
                calculated_at=now,
            ),
            _make_latest_row(
                indicator_name="inflation",
                window_days=90,
                coefficient=-0.99,  # older, must be dropped
                calculated_at=now - timedelta(days=1),
            ),
            # rates / 30d
            _make_latest_row(
                indicator_name="rates",
                window_days=30,
                coefficient=0.55,
                strength="medium",
                direction="positive",
                calculated_at=now,
            ),
        ]
        session = _mock_session_with_rows(rows)
        repo = CorrelationRepository(session)

        result = await repo.fetch_latest_per_indicator()

        assert len(result) == 2
        keys = {
            (r["indicator_name"], r["window_days"]) for r in result
        }
        assert keys == {("inflation", 90), ("rates", 30)}
        # Newer inflation row kept
        inflation_row = next(
            r for r in result if r["indicator_name"] == "inflation"
        )
        assert inflation_row["correlation_coefficient"] == -0.42

    @pytest.mark.asyncio
    async def test_window_filter_does_not_error(self) -> None:
        """Test that the window_days filter is forwarded without error."""
        session = _mock_session_with_rows([])
        repo = CorrelationRepository(session)

        result = await repo.fetch_latest_per_indicator(window_days=30)

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
        repo = CorrelationRepository(session)

        result = await repo.fetch_history("inflation", 90, days=30)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_ordered_list_of_dicts(self) -> None:
        """Test that rows come back in ascending calculated_at order."""
        now = datetime.now(timezone.utc)
        rows = [
            {
                "indicator_name": "inflation",
                "window_days": 90,
                "calculated_at": now - timedelta(days=i),
                "correlation_coefficient": -0.4 - i * 0.01,
                "strength": "medium",
                "direction": "negative",
                "p_value": 0.03,
            }
            for i in range(3)
        ]
        session = _mock_session_with_rows(rows)
        repo = CorrelationRepository(session)

        result = await repo.fetch_history("inflation", 90, days=30)

        assert isinstance(result, list)
        assert len(result) == 3
        # Repository returns whatever the DB returned, in that order.
        # Use approx because -0.4 - i*0.01 accumulates binary
        # floating-point error (e.g. -0.41000000000000003).
        coefficients = [r["correlation_coefficient"] for r in result]
        assert coefficients == pytest.approx([-0.4, -0.41, -0.42])


# ============================================================
# FETCH STRONGEST FOR WINDOW
# ============================================================
class TestFetchStrongestForWindow:
    """Tests for fetch_strongest_for_window()."""

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        """Test that no rows returns None."""
        session = _mock_session_with_rows([])
        repo = CorrelationRepository(session)

        result = await repo.fetch_strongest_for_window(90)

        assert result is None

    @pytest.mark.asyncio
    async def test_picks_highest_absolute_coefficient(self) -> None:
        """Test that the row with the largest |coefficient| wins.

        A negative coefficient with a larger magnitude beats a
        positive one with a smaller magnitude.
        """
        rows = [
            _make_latest_row(
                indicator_name="inflation",
                window_days=90,
                coefficient=-0.85,  # |0.85| — should win
                strength="strong",
                direction="negative",
            ),
            _make_latest_row(
                indicator_name="rates",
                window_days=90,
                coefficient=0.42,
                strength="medium",
                direction="positive",
            ),
        ]
        session = _mock_session_with_rows(rows)
        repo = CorrelationRepository(session)

        result = await repo.fetch_strongest_for_window(90)

        assert result is not None
        assert result["indicator_name"] == "inflation"
        assert result["correlation_coefficient"] == -0.85

    @pytest.mark.asyncio
    async def test_ties_broken_by_indicator_name(self) -> None:
        """Test that equal |coefficient| ties are broken deterministically.

        `max()` with a tuple key (abs(coefficient), indicator_name)
        picks the largest tuple on ties, so the alphabetically *last*
        indicator name wins. This is deterministic — the same input
        always yields the same output — which is what we care about.
        """
        rows = [
            _make_latest_row(
                indicator_name="unemployment",
                window_days=90,
                coefficient=0.5,
            ),
            _make_latest_row(
                indicator_name="gdp",
                window_days=90,
                coefficient=-0.5,
            ),
        ]
        session = _mock_session_with_rows(rows)
        repo = CorrelationRepository(session)

        result = await repo.fetch_strongest_for_window(90)

        assert result is not None
        # 'unemployment' > 'gdp' alphabetically, so max() picks it
        assert result["indicator_name"] == "unemployment"

    @pytest.mark.asyncio
    async def test_single_row_returns_that_row(self) -> None:
        """Test that a single-row result is returned as-is."""
        rows = [
            _make_latest_row(
                indicator_name="inflation",
                window_days=30,
                coefficient=0.1,
                strength="weak",
                direction="positive",
            ),
        ]
        session = _mock_session_with_rows(rows)
        repo = CorrelationRepository(session)

        result = await repo.fetch_strongest_for_window(30)

        assert result is not None
        assert result["indicator_name"] == "inflation"


# ============================================================
# COUNTS
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

        repo = CorrelationRepository(session)
        count = await repo.count_rows()

        assert count == 42
        assert isinstance(count, int)

    @pytest.mark.asyncio
    async def test_with_indicator_filter(self) -> None:
        """Test that the indicator filter is applied without error."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 5
        session.execute.return_value = mock_result

        repo = CorrelationRepository(session)
        count = await repo.count_rows(indicator_name="inflation")

        assert count == 5

    @pytest.mark.asyncio
    async def test_with_window_filter(self) -> None:
        """Test that the window filter is applied without error."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 3
        session.execute.return_value = mock_result

        repo = CorrelationRepository(session)
        count = await repo.count_rows(window_days=90)

        assert count == 3

    @pytest.mark.asyncio
    async def test_with_both_filters(self) -> None:
        """Test that indicator + window filters combine."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 2
        session.execute.return_value = mock_result

        repo = CorrelationRepository(session)
        count = await repo.count_rows(
            indicator_name="inflation", window_days=30
        )

        assert count == 2