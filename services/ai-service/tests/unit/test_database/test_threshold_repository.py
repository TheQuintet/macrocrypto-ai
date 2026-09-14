"""Unit tests for ThresholdRepository.

Strategy:
    These are *unit* tests — no database is involved. The
    AsyncSession is replaced with AsyncMock/MagicMock, and we
    assert on:
        - The shape of the values returned (which we control)
        - The SQLAlchemy statement(s) passed to session.execute()
        - The parameters bound to raw SQL (for the DISTINCT ON path)
        - Short-circuit behavior (empty inputs never touch the DB)

    Integration tests against a real Postgres live in
    tests/integration/ and are out of scope for T5.6.

Covers:
    - ThresholdBreachRow dataclass
    - save_breaches()
    - fetch_recent_breaches()
    - fetch_latest_breach()
    - fetch_latest_breaches_batch() (T5.6)
    - count_breaches()
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.sql import Select

from app.database.repositories.threshold_repository import (
    ThresholdBreachRow,
    ThresholdRepository,
)


# ============================================================
# Mock helpers
# ============================================================
def _mock_session() -> MagicMock:
    """Build a mocked AsyncSession with async execute()/flush()."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    return session


def _mock_execute_returning_rows(rows: List[Dict[str, Any]]) -> MagicMock:
    """Build a return value whose .mappings().all() yields `rows`.

    Matches the calling convention used by fetch_recent_breaches and
    fetch_latest_breaches_batch:

        result = await session.execute(stmt)
        result.mappings().all()  # -> list of dicts
    """
    result = MagicMock()
    mappings = MagicMock()
    mappings.all = MagicMock(return_value=list(rows))
    result.mappings = MagicMock(return_value=mappings)
    return result


def _mock_execute_returning_first(
    row: Optional[Dict[str, Any]],
) -> MagicMock:
    """Build a return value whose .mappings().first() yields `row`.

    Matches fetch_latest_breach:

        result = await session.execute(stmt)
        result.mappings().first()  # -> dict or None
    """
    result = MagicMock()
    mappings = MagicMock()
    mappings.first = MagicMock(return_value=row)
    result.mappings = MagicMock(return_value=mappings)
    return result


def _mock_execute_returning_scalar(value: Any) -> MagicMock:
    """Build a return value whose .scalar_one() yields `value`.

    Matches count_breaches:

        result = await session.execute(stmt)
        result.scalar_one()  # -> int
    """
    result = MagicMock()
    result.scalar_one = MagicMock(return_value=value)
    return result


def _last_stmt(session: MagicMock) -> Any:
    """Return the statement from the most recent session.execute() call."""
    return session.execute.call_args.args[0]


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def session() -> MagicMock:
    """A mocked AsyncSession."""
    return _mock_session()


@pytest.fixture
def repo(session: MagicMock) -> ThresholdRepository:
    """A repository bound to the mocked session."""
    return ThresholdRepository(session)


# ============================================================
# ThresholdBreachRow
# ============================================================
class TestThresholdBreachRow:
    """Tests for the ThresholdBreachRow dataclass."""

    def test_to_dict_contains_expected_keys(self) -> None:
        """Test to_dict includes every insertable column."""
        row = ThresholdBreachRow(
            horizon="24h",
            model_name="prophet_fresh",
            metric="mae_pct",
            metric_unit="percent",
            value=12.0,
            threshold=10.0,
            breach_direction="above",
            consecutive_days=3,
        )
        d = row.to_dict()
        for key in (
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
        ):
            assert key in d

    def test_defaults(self) -> None:
        """Test consecutive_days defaults to 1; optionals to None."""
        row = ThresholdBreachRow(
            horizon="24h",
            model_name="prophet_fresh",
            metric="mae_pct",
            metric_unit="percent",
            value=12.0,
            threshold=10.0,
            breach_direction="above",
        )
        assert row.consecutive_days == 1
        assert row.model_version is None
        assert row.notes is None


# ============================================================
# save_breaches
# ============================================================
class TestSaveBreaches:
    """Tests for save_breaches()."""

    async def test_empty_list_returns_zero_without_execute(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test empty input short-circuits and never touches the DB."""
        assert await repo.save_breaches([]) == 0
        session.execute.assert_not_called()
        session.flush.assert_not_called()

    async def test_inserts_rows_and_flushes(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test rows are inserted via a single INSERT and flushed."""
        session.execute.return_value = MagicMock()

        rows = [
            ThresholdBreachRow(
                horizon="24h",
                model_name="prophet_fresh",
                metric="mae_pct",
                metric_unit="percent",
                value=12.0,
                threshold=10.0,
                breach_direction="above",
            ),
            ThresholdBreachRow(
                horizon="24h",
                model_name="prophet_fresh",
                metric="mape",
                metric_unit="percent",
                value=14.0,
                threshold=10.0,
                breach_direction="above",
            ),
        ]
        n = await repo.save_breaches(rows)
        assert n == 2
        session.execute.assert_awaited_once()
        session.flush.assert_awaited_once()

        stmt = _last_stmt(session)
        # An INSERT statement carries a compiled string starting
        # with "INSERT INTO threshold_breaches".
        compiled = str(stmt.compile())
        assert "INSERT INTO threshold_breaches" in compiled

    async def test_does_not_commit(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the repository never commits — callers control that."""
        session.execute.return_value = MagicMock()
        rows = [
            ThresholdBreachRow(
                horizon="24h",
                model_name="prophet_fresh",
                metric="mae_pct",
                metric_unit="percent",
                value=12.0,
                threshold=10.0,
                breach_direction="above",
            )
        ]
        await repo.save_breaches(rows)
        # AsyncSession.commit should not be called by the repository.
        assert not hasattr(session, "commit") or not session.commit.called


# ============================================================
# fetch_recent_breaches
# ============================================================
class TestFetchRecentBreaches:
    """Tests for fetch_recent_breaches()."""

    async def test_empty_result(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test an empty DB result maps to an empty list."""
        session.execute.return_value = _mock_execute_returning_rows([])
        result = await repo.fetch_recent_breaches(
            horizon="24h", model_name="prophet_fresh"
        )
        assert result == []

    async def test_returns_list_of_dicts(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test rows come back as plain dicts."""
        rows = [
            {
                "id": 1,
                "metric": "mae_pct",
                "consecutive_days": 3,
                "detected_at": datetime.now(timezone.utc),
            }
        ]
        session.execute.return_value = _mock_execute_returning_rows(rows)
        result = await repo.fetch_recent_breaches(
            horizon="24h", model_name="prophet_fresh", days=7
        )
        assert result == rows
        session.execute.assert_awaited_once()

    async def test_statement_filters_and_orders(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the SELECT filters by horizon/model/since and DESC-orders."""
        session.execute.return_value = _mock_execute_returning_rows([])
        await repo.fetch_recent_breaches(
            horizon="24h", model_name="prophet_fresh", days=7
        )
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        # Filters
        assert "threshold_breaches.horizon" in compiled
        assert "threshold_breaches.model_name" in compiled
        assert "threshold_breaches.detected_at >=" in compiled
        # Ordering (DESC)
        assert "ORDER BY threshold_breaches.detected_at DESC" in compiled
        # Only one statement
        assert session.execute.await_count == 1


# ============================================================
# fetch_latest_breach
# ============================================================
class TestFetchLatestBreach:
    """Tests for fetch_latest_breach()."""

    async def test_none_when_absent(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test no matching row → None."""
        session.execute.return_value = _mock_execute_returning_first(None)
        result = await repo.fetch_latest_breach(
            horizon="24h", model_name="prophet_fresh", metric="mae_pct"
        )
        assert result is None

    async def test_returns_dict_when_found(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test a matching row comes back as a dict."""
        row = {
            "id": 1,
            "detected_at": datetime.now(timezone.utc),
            "consecutive_days": 4,
            "value": 11.0,
            "threshold": 10.0,
        }
        session.execute.return_value = _mock_execute_returning_first(row)
        result = await repo.fetch_latest_breach(
            horizon="24h", model_name="prophet_fresh", metric="mae_pct"
        )
        assert result == row

    async def test_statement_has_limit_1_and_desc(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the SELECT orders DESC and limits to 1."""
        session.execute.return_value = _mock_execute_returning_first(None)
        await repo.fetch_latest_breach(
            horizon="24h", model_name="prophet_fresh", metric="mae_pct"
        )
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "ORDER BY threshold_breaches.detected_at DESC" in compiled
        assert "LIMIT 1" in compiled
        # All three filters present
        assert "threshold_breaches.horizon" in compiled
        assert "threshold_breaches.model_name" in compiled
        assert "threshold_breaches.metric" in compiled


# ============================================================
# fetch_latest_breaches_batch  (T5.6)
# ============================================================
class TestFetchLatestBreachesBatch:
    """Tests for fetch_latest_breaches_batch()."""

    async def test_empty_result(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test an empty DB result maps to an empty list."""
        session.execute.return_value = _mock_execute_returning_rows([])
        result = await repo.fetch_latest_breaches_batch(since_days=30)
        assert result == []

    async def test_returns_dicts(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test rows come back as plain dicts."""
        rows = [
            {
                "model_name": "prophet_fresh",
                "horizon": "24h",
                "metric": "mae_pct",
                "consecutive_days": 3,
                "detected_at": datetime.now(timezone.utc),
            }
        ]
        session.execute.return_value = _mock_execute_returning_rows(rows)
        result = await repo.fetch_latest_breaches_batch(since_days=30)
        assert result == rows

    async def test_uses_distinct_on_sql_and_passes_since_param(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the raw SQL uses DISTINCT ON and binds the since param.

        The method issues raw SQL via text(); we assert on the
        compiled statement and on the bound parameters dict.
        """
        session.execute.return_value = _mock_execute_returning_rows([])
        await repo.fetch_latest_breaches_batch(since_days=30)

        # The statement is a text() Clauses object; str() reveals the SQL.
        stmt = _last_stmt(session)
        sql = str(stmt)
        assert "DISTINCT ON (model_name, horizon, metric)" in sql
        assert "FROM threshold_breaches" in sql
        assert "WHERE detected_at >= :since" in sql
        assert "ORDER BY model_name, horizon, metric, detected_at DESC" in sql

        # The bound parameters dict is the second positional arg.
        params = session.execute.call_args.args[1]
        assert "since" in params
        # `since` is "now - since_days"; assert it's a recent past datetime.
        delta = datetime.now(timezone.utc) - params["since"]
        assert timedelta(days=29) < delta < timedelta(days=31)

    async def test_since_days_respected(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the since_days argument drives the bound `since` value."""
        session.execute.return_value = _mock_execute_returning_rows([])
        await repo.fetch_latest_breaches_batch(since_days=7)
        params = session.execute.call_args.args[1]
        delta = datetime.now(timezone.utc) - params["since"]
        assert timedelta(days=6) < delta < timedelta(days=8)


# ============================================================
# count_breaches
# ============================================================
class TestCountBreaches:
    """Tests for count_breaches()."""

    async def test_zero_when_empty(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test a count query returning 0 maps to int 0."""
        session.execute.return_value = _mock_execute_returning_scalar(0)
        assert await repo.count_breaches() == 0

    async def test_no_filters(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test no filters produces a bare COUNT query."""
        session.execute.return_value = _mock_execute_returning_scalar(42)
        assert await repo.count_breaches() == 42
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        # SQLAlchemy 2.x inserts a newline between the SELECT clause
        # and FROM, so match on the two fragments independently.
        assert "SELECT count(*) AS count_1" in compiled
        assert "FROM threshold_breaches" in compiled
        # No WHERE clause when no filters are given
        assert "WHERE" not in compiled

    async def test_horizon_filter(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the horizon filter is applied."""
        session.execute.return_value = _mock_execute_returning_scalar(7)
        assert await repo.count_breaches(horizon="24h") == 7
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "WHERE" in compiled
        assert "threshold_breaches.horizon = '24h'" in compiled

    async def test_model_name_filter(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the model_name filter is applied."""
        session.execute.return_value = _mock_execute_returning_scalar(3)
        assert (
            await repo.count_breaches(model_name="prophet_fresh") == 3
        )
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert (
            "threshold_breaches.model_name = 'prophet_fresh'" in compiled
        )

    async def test_since_days_filter(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test the since_days filter is applied."""
        session.execute.return_value = _mock_execute_returning_scalar(5)
        assert await repo.count_breaches(since_days=30) == 5
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "threshold_breaches.detected_at >=" in compiled

    async def test_all_filters_combined(
        self, repo: ThresholdRepository, session: MagicMock
    ) -> None:
        """Test horizon + model + since all appear in the WHERE clause."""
        session.execute.return_value = _mock_execute_returning_scalar(2)
        assert (
            await repo.count_breaches(
                horizon="7d",
                model_name="xgboost_fresh",
                since_days=14,
            )
            == 2
        )
        stmt = _last_stmt(session)
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "threshold_breaches.horizon = '7d'" in compiled
        assert (
            "threshold_breaches.model_name = 'xgboost_fresh'" in compiled
        )
        assert "threshold_breaches.detected_at >=" in compiled