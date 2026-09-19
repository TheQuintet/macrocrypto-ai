"""Unit tests for ExportHistoryRepository (A2.1).

The repository is exercised against a fake AsyncSession that records
the statements it is asked to execute and returns canned results.
This keeps the tests fast and database-free while still verifying
the SQL shape (target table, values, RETURNING) and the control flow
of each method.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional

import pytest

from app.database.repositories.export_history_repository import (
    ExportHistoryRepository,
    ExportHistoryRow,
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
class TestExportHistoryRow:
    """ExportHistoryRow is a plain dataclass over the insert payload."""

    def test_defaults(self):
        row = ExportHistoryRow(
            export_type="csv",
            timeframe="30d",
            file_name="f.csv",
        )
        assert row.user_id is None
        assert row.data_types == []
        assert row.status == "pending"
        assert row.file_size is None

    def test_to_dict_keys(self):
        row = ExportHistoryRow(
            export_type="png",
            timeframe="1y",
            file_name="f.png",
            user_id="u-1",
            data_types=["btc_price"],
            file_size=123,
        )
        d = row.to_dict()
        assert set(d.keys()) == {
            "user_id",
            "export_type",
            "data_types",
            "timeframe",
            "file_name",
            "file_size",
            "status",
        }
        # data_types must be copied, not aliased.
        assert d["data_types"] == ["btc_price"]
        assert d["data_types"] is not row.data_types

    def test_to_dict_round_trips_through_validator(self):
        from app.database.validators import validate_export_history_row

        row = ExportHistoryRow(
            export_type="pdf",
            timeframe="5y",
            file_name="report.pdf",
            data_types=["btc_price", "correlations"],
        )
        validate_export_history_row(row.to_dict())

    def test_repr_contains_key_fields(self):
        row = ExportHistoryRow(
            export_type="csv",
            timeframe="90d",
            file_name="f.csv",
            user_id="u-9",
        )
        text = repr(row)
        assert "csv" in text
        assert "90d" in text
        assert "f.csv" in text
        assert "u-9" in text


# ============================================================
# create_request
# ============================================================
class TestCreateRequest:
    """create_request inserts and returns the new id."""

    @pytest.mark.asyncio
    async def test_returns_new_id(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=42))

        repo = ExportHistoryRepository(session)
        row = ExportHistoryRow(
            export_type="csv",
            timeframe="30d",
            file_name="f.csv",
            data_types=["btc_price"],
        )
        new_id = await repo.create_request(row)

        assert new_id == 42
        assert session.flushes == 1
        assert len(session.executed) == 1

    @pytest.mark.asyncio
    async def test_statement_targets_export_history(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=1))

        repo = ExportHistoryRepository(session)
        row = ExportHistoryRow(
            export_type="csv",
            timeframe="30d",
            file_name="f.csv",
        )
        await repo.create_request(row)

        stmt = session.executed[0]
        # The insert's target table name is carried on the compiled
        # object; assert via the statement's .table attribute.
        assert stmt.table.name == "export_history"

    @pytest.mark.asyncio
    async def test_validates_before_executing(self):
        session = _FakeSession()
        repo = ExportHistoryRepository(session)

        bad = ExportHistoryRow(
            export_type="xlsx",  # invalid
            timeframe="30d",
            file_name="f.xlsx",
        )
        with pytest.raises(ValueError):
            await repo.create_request(bad)

        # No statement should have reached the session.
        assert session.executed == []

    @pytest.mark.asyncio
    async def test_rejects_duplicate_data_types(self):
        session = _FakeSession()
        repo = ExportHistoryRepository(session)

        bad = ExportHistoryRow(
            export_type="csv",
            timeframe="30d",
            file_name="f.csv",
            data_types=["btc_price", "btc_price"],
        )
        with pytest.raises(ValueError, match="duplicate data_type"):
            await repo.create_request(bad)

        assert session.executed == []


# ============================================================
# mark_completed
# ============================================================
class TestMarkCompleted:
    """mark_completed flips status and records file metadata."""

    @pytest.mark.asyncio
    async def test_returns_rowcount(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=1))

        repo = ExportHistoryRepository(session)
        rc = await repo.mark_completed(
            export_id=7,
            file_name="done.csv",
            file_size=2048,
        )

        assert rc == 1
        assert session.flushes == 1
        stmt = session.executed[0]
        # Verify the values carried on the UPDATE.
        values = dict(stmt.compile().params)
        assert "completed" in values.values()
        assert "done.csv" in values.values()
        assert 2048 in values.values()

    @pytest.mark.asyncio
    async def test_zero_when_id_missing(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=0))

        repo = ExportHistoryRepository(session)
        rc = await repo.mark_completed(
            export_id=999,
            file_name="done.csv",
            file_size=1,
        )
        assert rc == 0


# ============================================================
# mark_failed
# ============================================================
class TestMarkFailed:
    """mark_failed flips status to 'failed'."""

    @pytest.mark.asyncio
    async def test_returns_rowcount(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=1))

        repo = ExportHistoryRepository(session)
        rc = await repo.mark_failed(export_id=7)
        assert rc == 1

        values = dict(session.executed[0].compile().params)
        assert "failed" in values.values()

    @pytest.mark.asyncio
    async def test_zero_when_id_missing(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=0))

        repo = ExportHistoryRepository(session)
        rc = await repo.mark_failed(export_id=999)
        assert rc == 0


# ============================================================
# mark_downloaded
# ============================================================
class TestMarkDownloaded:
    """mark_downloaded records the timestamp."""

    @pytest.mark.asyncio
    async def test_defaults_to_now_utc(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=1))

        before = datetime.now(timezone.utc)
        repo = ExportHistoryRepository(session)
        rc = await repo.mark_downloaded(export_id=7)
        after = datetime.now(timezone.utc)

        assert rc == 1
        params = dict(session.executed[0].compile().params)
        # The timestamp is one of the param values.
        ts = next(v for v in params.values() if isinstance(v, datetime))
        assert before <= ts <= after

    @pytest.mark.asyncio
    async def test_explicit_timestamp_is_used(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=1))

        ts = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
        repo = ExportHistoryRepository(session)
        await repo.mark_downloaded(export_id=7, downloaded_at=ts)

        params = dict(session.executed[0].compile().params)
        assert ts in params.values()

    @pytest.mark.asyncio
    async def test_zero_when_id_missing(self):
        session = _FakeSession()
        session.queue(_FakeResult(rowcount=0))

        repo = ExportHistoryRepository(session)
        rc = await repo.mark_downloaded(export_id=999)
        assert rc == 0


# ============================================================
# fetch_by_id
# ============================================================
class TestFetchById:
    """fetch_by_id returns a dict or None."""

    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self):
        canned = {
            "id": 1,
            "user_id": "u-1",
            "export_type": "csv",
            "data_types": ["btc_price"],
            "timeframe": "30d",
            "file_name": "f.csv",
            "file_size": 10,
            "status": "completed",
            "created_at": datetime(2026, 9, 15, tzinfo=timezone.utc),
            "downloaded_at": None,
        }
        session = _FakeSession()
        session.queue(_FakeResult(rows=[canned]))

        repo = ExportHistoryRepository(session)
        out = await repo.fetch_by_id(1)

        assert out == canned
        assert out is not canned  # dict() copy, not the same object

    @pytest.mark.asyncio
    async def test_returns_none_when_missing(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))

        repo = ExportHistoryRepository(session)
        out = await repo.fetch_by_id(999)
        assert out is None


# ============================================================
# fetch_history
# ============================================================
class TestFetchHistory:
    """fetch_history applies filters and orders newest-first."""

    @pytest.mark.asyncio
    async def test_no_filters_returns_all(self):
        rows = [
            {"id": 2, "user_id": "u-1", "status": "completed"},
            {"id": 1, "user_id": "u-1", "status": "pending"},
        ]
        session = _FakeSession()
        session.queue(_FakeResult(rows=rows))

        repo = ExportHistoryRepository(session)
        out = await repo.fetch_history()

        assert [r["id"] for r in out] == [2, 1]

    @pytest.mark.asyncio
    async def test_user_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))

        repo = ExportHistoryRepository(session)
        await repo.fetch_history(user_id="u-42")

        compiled = str(session.executed[0].compile())
        assert "user_id" in compiled.lower()

    @pytest.mark.asyncio
    async def test_status_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))

        repo = ExportHistoryRepository(session)
        await repo.fetch_history(status="failed")

        compiled = str(session.executed[0].compile())
        assert "status" in compiled.lower()

    @pytest.mark.asyncio
    async def test_timeframe_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))

        repo = ExportHistoryRepository(session)
        await repo.fetch_history(timeframe="90d")

        compiled = str(session.executed[0].compile())
        assert "timeframe" in compiled.lower()

    @pytest.mark.asyncio
    async def test_orders_by_created_at_desc(self):
        session = _FakeSession()
        session.queue(_FakeResult(rows=[]))

        repo = ExportHistoryRepository(session)
        await repo.fetch_history()

        compiled = str(session.executed[0].compile())
        assert "ORDER BY" in compiled
        assert "created_at" in compiled.lower()
        # "DESC" is rendered by the dialect compiler.
        assert "DESC" in compiled


# ============================================================
# count_rows
# ============================================================
class TestCountRows:
    """count_rows returns a scalar count, optionally filtered."""

    @pytest.mark.asyncio
    async def test_returns_scalar(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=17))

        repo = ExportHistoryRepository(session)
        assert await repo.count_rows() == 17

    @pytest.mark.asyncio
    async def test_user_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=0))

        repo = ExportHistoryRepository(session)
        await repo.count_rows(user_id="u-1")

        compiled = str(session.executed[0].compile())
        assert "user_id" in compiled.lower()

    @pytest.mark.asyncio
    async def test_status_filter_is_applied(self):
        session = _FakeSession()
        session.queue(_FakeResult(scalar=0))

        repo = ExportHistoryRepository(session)
        await repo.count_rows(status="pending")

        compiled = str(session.executed[0].compile())
        assert "status" in compiled.lower()