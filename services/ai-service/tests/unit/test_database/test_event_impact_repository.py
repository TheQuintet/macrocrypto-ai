"""Unit tests for EventImpactRepository (A5.1).

The repository is exercised against a fake AsyncSession that records
the statements it is asked to execute and returns canned results.
This keeps the tests fast and database-free while still verifying
the SQL shape (target table, values, RETURNING) and the control
flow of each method.
"""

from datetime import date
from typing import Any, List, Optional

import pytest

from app.database.repositories.event_impact_repository import (
    EventImpactRepository,
    EventImpactRow,
)


# ============================================================
# FAKE ASYNC SESSION
# ============================================================
class _FakeResult:
    """Minimal stand-in for a SQLAlchemy CursorResult."""

    def __init__(self, *, scalar: Any = None, rows: Optional[List[Any]] = None,
                 rowcount: int = 0) -> None:
        self._scalar = scalar
        self._rows = rows or []
        self.rowcount = rowcount

    def scalar_one(self) -> Any:
        return self._scalar

    def scalar_one_or_none(self) -> Any:
        return self._scalar

    def mappings(self) -> "_FakeMappings":
        return _FakeMappings(self._rows)


class _FakeMappings:
    def __init__(self, rows: List[Any]) -> None:
        self._rows = rows

    def first(self) -> Any:
        return self._rows[0] if self._rows else None

    def all(self) -> List[Any]:
        return list(self._rows)


class _FakeSession:
    """Records executed statements and returns pre-queued results."""

    def __init__(self) -> None:
        self.executed: List[Any] = []
        self.flushes: int = 0
        self._queue: List[_FakeResult] = []

    def queue(self, result: _FakeResult) -> None:
        self._queue.append(result)

    async def execute(self, stmt: Any) -> _FakeResult:
        self.executed.append(stmt)
        if not self._queue:
            return _FakeResult()
        return self._queue.pop(0)

    async def flush(self) -> None:
        self.flushes += 1


# ============================================================
# ROW DATACLASS
# ============================================================
def _make_row(
    event_name: str = "FOMC",
    event_date: date = date(2024, 3, 20),
    impact_level: str = "high",
    direction: str = "up",
) -> EventImpactRow:
    """Build a valid EventImpactRow by default; override for tests."""
    return EventImpactRow(
        event_name=event_name,
        event_date=event_date,
        impact_level=impact_level,
        btc_price_before=63000.0,
        btc_price_after=65500.0,
        price_change_percent=3.97,
        volatility=0.021,
        direction=direction,
    )


class TestEventImpactRow:
    """EventImpactRow is a plain dataclass over the insert payload."""

    def test_to_dict_keys(self):
        row = _make_row()
        d = row.to_dict()
        assert set(d.keys()) == {
            "event_name",
            "event_date",
            "impact_level",
            "btc_price_before",
            "btc_price_after",
            "price_change_percent",
            "volatility",
            "direction",
        }

    def test_to_dict_round_trips_through_validator(self):
        from app.database.validators import (
            validate_historical_event_impact_row,
        )

        row = _make_row()
        validate_historical_event_impact_row(row.to_dict())

    def test_repr_contains_key_fields(self):
        text = repr(_make_row())
        assert "FOMC" in text
        assert "2024-03-20" in text
        assert "high" in text
        assert "up" in text


# ============================================================
# save_rows
# ============================================================
class TestSaveRows:
    """save_rows inserts and returns the row count."""

    @pytest.mark.asyncio
    async def test_returns_row_count(self):
        session = _FakeSession()
        repo = EventImpactRepository(session)
        n = await repo.save_rows([_make_row(), _make_row()])
        assert n == 2
        assert session.flushes == 1
        assert len(session.executed) == 1

    @pytest.mark.asyncio
    async def test_empty_returns_zero(self):
        session = _FakeSession()
        repo = EventImpactRepository(session)
        assert await repo.save_rows([]) == 0
        # No statement reached the session.
        assert session.executed == []

    @pytest.mark.asyncio
    async def test_statement_targets_historical_event_impacts(self):
        session = _FakeSession()
        repo = EventImpactRepository(session)
        await repo.save_rows([_make_row()])
        stmt = session.executed[0]
        assert stmt.table.name == "historical_event_impacts"

    @pytest.mark.asyncio
    async def test_validates_before_executing(self):
        session = _FakeSession()
        repo = EventImpactRepository(session)
        bad = _make_row(impact_level="invalid")
        with pytest.raises(ValueError):
            await repo.save_rows([bad])
        assert session.executed == []

    @pytest.mark.asyncio
    async def test_rejects_negative_price(self):
        session = _FakeSession()
        repo = EventImpactRepository(session)
        bad = _make_row()
        bad.btc_price_before = -1.0
        with pytest.raises(ValueError, match="must be positive"):
            await repo.save_rows([bad])
        assert session.executed == []


# ============================================================
# delete_by_event
# ============================================================
class TestDeleteByEvent:
    """delete_by_event removes a row by its natural key."""

    @pytest.mark.asyncio
    async def test_returns_true_when_removed(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=42))
        repo = EventImpactRepository(session)
        assert await repo.delete_by_event("FOMC", date(2024, 3, 20)) is True

    @pytest.mark.asyncio
    async def test_returns_false_when_missing(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=None))
        repo = EventImpactRepository(session)
        assert await repo.delete_by_event("FOMC", date(2024, 3, 20)) is False


# ============================================================
# fetch_all
# ============================================================
class TestFetchAll:
    """fetch_all reads every row, optionally filtered."""

    @pytest.mark.asyncio
    async def test_no_filters(self):
        canned = [{"id": 2, "event_name": "FOMC"}, {"id": 1, "event_name": "CPI"}]
        session = _FakeSession()
        session.queue(_FakeResult(rows=canned))
        repo = EventImpactRepository(session)
        out = await repo.fetch_all()
        assert [r["id"] for r in out] == [2, 1]

    @pytest.mark.asyncio
    async def test_impact_level_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))
        repo = EventImpactRepository(session)
        await repo.fetch_all(impact_level="high")
        compiled = str(session.executed[0].compile())
        assert "impact_level" in compiled.lower()

    @pytest.mark.asyncio
    async def test_orders_by_event_date_desc(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))
        repo = EventImpactRepository(session)
        await repo.fetch_all()
        compiled = str(session.executed[0].compile())
        assert "ORDER BY" in compiled
        assert "event_date" in compiled.lower()
        assert "DESC" in compiled


# ============================================================
# fetch_by_event_name
# ============================================================
class TestFetchByEventName:
    """fetch_by_event_name filters by event name."""

    @pytest.mark.asyncio
    async def test_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))
        repo = EventImpactRepository(session)
        await repo.fetch_by_event_name("FOMC")
        compiled = str(session.executed[0].compile())
        assert "event_name" in compiled.lower()

    @pytest.mark.asyncio
    async def test_returns_rows(self):
        canned = [{"id": 1, "event_name": "FOMC", "event_date": date(2024, 3, 20)}]
        session = _FakeSession()
        session.queue(_FakeResult(rows=canned))
        repo = EventImpactRepository(session)
        out = await repo.fetch_by_event_name("FOMC")
        assert out == canned


# ============================================================
# fetch_by_date_range
# ============================================================
class TestFetchByDateRange:
    """fetch_by_date_range filters by inclusive date bounds."""

    @pytest.mark.asyncio
    async def test_range_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))
        repo = EventImpactRepository(session)
        await repo.fetch_by_date_range(
            date(2024, 1, 1), date(2024, 12, 31)
        )
        compiled = str(session.executed[0].compile())
        assert "event_date" in compiled.lower()

    @pytest.mark.asyncio
    async def test_impact_level_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))
        repo = EventImpactRepository(session)
        await repo.fetch_by_date_range(
            date(2024, 1, 1), date(2024, 12, 31), impact_level="high"
        )
        compiled = str(session.executed[0].compile())
        assert "impact_level" in compiled.lower()


# ============================================================
# count_rows
# ============================================================
class TestCountRows:
    """count_rows returns a scalar count, optionally filtered."""

    @pytest.mark.asyncio
    async def test_returns_scalar(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=17))
        repo = EventImpactRepository(session)
        assert await repo.count_rows() == 17

    @pytest.mark.asyncio
    async def test_event_name_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=0))
        repo = EventImpactRepository(session)
        await repo.count_rows(event_name="FOMC")
        compiled = str(session.executed[0].compile())
        assert "event_name" in compiled.lower()

    @pytest.mark.asyncio
    async def test_impact_level_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=0))
        repo = EventImpactRepository(session)
        await repo.count_rows(impact_level="high")
        compiled = str(session.executed[0].compile())
        assert "impact_level" in compiled.lower()