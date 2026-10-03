"""Unit tests for the ChampionRepository.

These tests mock the SQLAlchemy AsyncSession so no live database
is required. They verify:
    - Correct SQL statements are issued (shape + parameters)
    - Result rows are correctly mapped
    - CLI-mode routing resolves to the right tables
    - Idempotency keys are correct on upsert / insert

Test organization:
    - TestModelChampionRow:      dataclass behavior
    - TestChampionCandidateRow:  dataclass behavior
    - TestTableRouting:          CLI vs production table resolution
    - TestGetChampion:           single-row read with regime match
    - TestGetAllChampions:       full-table read
    - TestUpsertChampion:        insert/update via ON CONFLICT
    - TestClearChampion:         delete with regime match
    - TestGetStabilityStreak:    consecutive-day walk
    - TestGetRecentCandidates:   recent-range read
    - TestRecordCandidate:       idempotent insert
    - TestPruneOldCandidates:    retention delete
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.database.repositories.champion_repository import (
    ChampionCandidateRow,
    ChampionRepository,
    ModelChampionRow,
)
from app.database.tables import (
    champion_candidates,
    champion_candidates_cli,
    model_champions,
    model_champions_cli,
)


# ============================================================
# HELPERS
# ============================================================
def _make_champion_row(**overrides) -> ModelChampionRow:
    """Build a valid ModelChampionRow with all fields set."""
    defaults = dict(
        horizon="24h",
        market_condition=None,
        model_name="xgboost_fresh",
        model_version="1.0.0",
        metric_name="mae",
        metric_value=90.0,
        sample_size=200,
        lookback_days=30,
        previous_champion="prophet_fresh",
        reason="improvement 10.0%",
        promoted_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return ModelChampionRow(**defaults)


def _make_candidate_row(**overrides) -> ChampionCandidateRow:
    """Build a valid ChampionCandidateRow with all fields set."""
    defaults = dict(
        candidate_date=date(2026, 9, 15),
        horizon="24h",
        market_condition=None,
        model_name="xgboost_fresh",
        metric_name="mae",
        metric_value=90.0,
        sample_size=200,
    )
    defaults.update(overrides)
    return ChampionCandidateRow(**defaults)


def _make_champion_dict(**overrides) -> dict:
    """Build a champion row as it would appear from the DB."""
    defaults = dict(
        id=1,
        horizon="24h",
        market_condition=None,
        model_name="xgboost_fresh",
        model_version="1.0.0",
        promoted_at=datetime.now(timezone.utc),
        metric_name="mae",
        metric_value=90.0,
        sample_size=200,
        lookback_days=30,
        previous_champion="prophet_fresh",
        reason="improvement 10.0%",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return defaults


def _make_candidate_dict(**overrides) -> dict:
    """Build a candidate row as it would appear from the DB."""
    defaults = dict(
        id=1,
        candidate_date=date(2026, 9, 15),
        horizon="24h",
        market_condition=None,
        model_name="xgboost_fresh",
        metric_name="mae",
        metric_value=90.0,
        sample_size=200,
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return defaults


def _mock_session_with_mappings(rows: List[dict]) -> AsyncMock:
    """AsyncMock session whose execute() returns rows via .mappings()."""
    mock_result = MagicMock()
    mock_result.mappings.return_value.all.return_value = rows
    mock_result.mappings.return_value.first.return_value = (
        rows[0] if rows else None
    )

    session = AsyncMock()
    session.execute.return_value = mock_result
    return session


# ============================================================
# ROW DATACLASSES
# ============================================================
class TestModelChampionRow:
    """Tests for the ModelChampionRow dataclass."""

    def test_construction(self) -> None:
        row = _make_champion_row()
        assert row.horizon == "24h"
        assert row.model_name == "xgboost_fresh"
        assert row.market_condition is None
        assert row.metric_value == 90.0

    def test_to_dict_keys(self) -> None:
        row = _make_champion_row()
        d = row.to_dict()
        expected = {
            "horizon",
            "market_condition",
            "model_name",
            "model_version",
            "promoted_at",
            "metric_name",
            "metric_value",
            "sample_size",
            "lookback_days",
            "previous_champion",
            "reason",
        }
        assert set(d.keys()) == expected

    def test_to_dict_defaults_promoted_at_to_now(self) -> None:
        """When promoted_at is None, to_dict fills in the current UTC time."""
        row = _make_champion_row(promoted_at=None)
        before = datetime.now(timezone.utc)
        d = row.to_dict()
        after = datetime.now(timezone.utc)
        assert d["promoted_at"] is not None
        assert before <= d["promoted_at"] <= after

    def test_to_dict_preserves_explicit_promoted_at(self) -> None:
        explicit = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)
        row = _make_champion_row(promoted_at=explicit)
        d = row.to_dict()
        assert d["promoted_at"] == explicit

    def test_repr_is_readable(self) -> None:
        row = _make_champion_row()
        r = repr(row)
        assert "24h" in r
        assert "xgboost_fresh" in r
        assert "mae" in r


class TestChampionCandidateRow:
    """Tests for the ChampionCandidateRow dataclass."""

    def test_construction(self) -> None:
        row = _make_candidate_row()
        assert row.candidate_date == date(2026, 9, 15)
        assert row.horizon == "24h"
        assert row.model_name == "xgboost_fresh"

    def test_to_dict_keys(self) -> None:
        row = _make_candidate_row()
        d = row.to_dict()
        expected = {
            "candidate_date",
            "horizon",
            "market_condition",
            "model_name",
            "metric_name",
            "metric_value",
            "sample_size",
        }
        assert set(d.keys()) == expected

    def test_repr_is_readable(self) -> None:
        row = _make_candidate_row()
        r = repr(row)
        assert "2026-09-15" in r
        assert "xgboost_fresh" in r


# ============================================================
# TABLE ROUTING
# ============================================================
class TestTableRouting:
    """CLI-mode routing picks the right table."""

    def test_champion_table_production_when_not_cli(self) -> None:
        session = AsyncMock()
        repo = ChampionRepository(session)
        with patch("app.database.repositories.champion_repository.settings") as s:
            s.cli_mode = False
            assert repo._resolve_champion_table() is model_champions

    def test_champion_table_cli_when_cli(self) -> None:
        session = AsyncMock()
        repo = ChampionRepository(session)
        with patch("app.database.repositories.champion_repository.settings") as s:
            s.cli_mode = True
            assert repo._resolve_champion_table() is model_champions_cli

    def test_candidates_table_production_when_not_cli(self) -> None:
        session = AsyncMock()
        repo = ChampionRepository(session)
        with patch("app.database.repositories.champion_repository.settings") as s:
            s.cli_mode = False
            assert repo._resolve_candidates_table() is champion_candidates

    def test_candidates_table_cli_when_cli(self) -> None:
        session = AsyncMock()
        repo = ChampionRepository(session)
        with patch("app.database.repositories.champion_repository.settings") as s:
            s.cli_mode = True
            assert repo._resolve_candidates_table() is champion_candidates_cli


# ============================================================
# GET CHAMPION
# ============================================================
class TestGetChampion:
    """Tests for get_champion()."""

    @pytest.mark.asyncio
    async def test_returns_dict_when_found(self) -> None:
        row = _make_champion_dict()
        session = _mock_session_with_mappings([row])
        repo = ChampionRepository(session)

        result = await repo.get_champion(horizon="24h")

        assert result is not None
        assert result["model_name"] == "xgboost_fresh"
        assert result["metric_value"] == 90.0
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_returns_none_when_empty(self) -> None:
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        result = await repo.get_champion(horizon="24h")

        assert result is None

    @pytest.mark.asyncio
    async def test_global_market_condition_uses_is_null(self) -> None:
        """When market_condition is None, the SQL should use IS NULL."""
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        await repo.get_champion(horizon="24h", market_condition=None)

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition IS NULL" in compiled

    @pytest.mark.asyncio
    async def test_regime_market_condition_uses_equality(self) -> None:
        """When market_condition is a string, the SQL should use =."""
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        await repo.get_champion(horizon="24h", market_condition="bull")

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition = 'bull'" in compiled

    @pytest.mark.asyncio
    async def test_horizon_filter_is_applied(self) -> None:
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        await repo.get_champion(horizon="7d")

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "horizon = '7d'" in compiled


# ============================================================
# GET ALL CHAMPIONS
# ============================================================
class TestGetAllChampions:
    """Tests for get_all_champions()."""

    @pytest.mark.asyncio
    async def test_returns_all_rows(self) -> None:
        rows = [
            _make_champion_dict(id=1, horizon="24h", market_condition=None),
            _make_champion_dict(id=2, horizon="7d", market_condition=None),
            _make_champion_dict(id=3, horizon="24h", market_condition="bull"),
        ]
        session = _mock_session_with_mappings(rows)
        repo = ChampionRepository(session)

        result = await repo.get_all_champions()

        assert len(result) == 3
        assert all(isinstance(r, dict) for r in result)

    @pytest.mark.asyncio
    async def test_empty_table_returns_empty_list(self) -> None:
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        result = await repo.get_all_champions()

        assert result == []


# ============================================================
# UPSERT CHAMPION
# ============================================================
class TestUpsertChampion:
    """Tests for upsert_champion()."""

    @pytest.mark.asyncio
    async def test_returns_row_id(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        row_id = await repo.upsert_champion(_make_champion_row())

        assert row_id == 42

    @pytest.mark.asyncio
    async def test_statement_uses_on_conflict_do_update(self) -> None:
        """The generated SQL should contain ON CONFLICT ... DO UPDATE."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.upsert_champion(_make_champion_row())

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "ON CONFLICT" in compiled
        assert "DO UPDATE" in compiled

    @pytest.mark.asyncio
    async def test_does_not_commit(self) -> None:
        """The repository must not commit — the caller controls tx."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 1
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.upsert_champion(_make_champion_row())

        session.commit.assert_not_called()


# ============================================================
# CLEAR CHAMPION
# ============================================================
class TestClearChampion:
    """Tests for clear_champion()."""

    @pytest.mark.asyncio
    async def test_returns_true_when_row_removed(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 1
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        removed = await repo.clear_champion(horizon="24h")

        assert removed is True

    @pytest.mark.asyncio
    async def test_returns_false_when_no_row(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        removed = await repo.clear_champion(horizon="24h")

        assert removed is False

    @pytest.mark.asyncio
    async def test_global_uses_is_null(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.clear_champion(horizon="24h", market_condition=None)

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition IS NULL" in compiled

    @pytest.mark.asyncio
    async def test_regime_uses_equality(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.clear_champion(horizon="24h", market_condition="bull")

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition = 'bull'" in compiled


# ============================================================
# GET STABILITY STREAK
# ============================================================
class TestGetStabilityStreak:
    """Tests for get_stability_streak()."""

    @pytest.mark.asyncio
    async def test_no_rows_returns_zero(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        streak = await repo.get_stability_streak(
            horizon="24h",
            market_condition=None,
            model_name="xgboost_fresh",
            metric_name="mae",
            today=date(2026, 9, 20),
        )

        assert streak == 0

    @pytest.mark.asyncio
    async def test_consecutive_days_counted(self) -> None:
        """Three consecutive days ending today → streak of 3."""
        today = date(2026, 9, 20)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (today,),                                  # 2026-09-20
            (today - timedelta(days=1),),              # 2026-09-19
            (today - timedelta(days=2),),              # 2026-09-18
        ]
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        streak = await repo.get_stability_streak(
            horizon="24h",
            market_condition=None,
            model_name="xgboost_fresh",
            metric_name="mae",
            today=today,
        )

        assert streak == 3

    @pytest.mark.asyncio
    async def test_gap_breaks_streak(self) -> None:
        """A missing day stops the walk."""
        today = date(2026, 9, 20)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (today,),                                  # 2026-09-20
            (today - timedelta(days=1),),              # 2026-09-19
            # gap on 2026-09-18
            (today - timedelta(days=3),),              # 2026-09-17
        ]
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        streak = await repo.get_stability_streak(
            horizon="24h",
            market_condition=None,
            model_name="xgboost_fresh",
            metric_name="mae",
            today=today,
        )

        assert streak == 2

    @pytest.mark.asyncio
    async def test_old_most_recent_breaks_streak(self) -> None:
        """If the most recent row is older than yesterday, streak is 0."""
        today = date(2026, 9, 20)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (today - timedelta(days=5),),              # 2026-09-15
        ]
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        streak = await repo.get_stability_streak(
            horizon="24h",
            market_condition=None,
            model_name="xgboost_fresh",
            metric_name="mae",
            today=today,
        )

        assert streak == 0

    @pytest.mark.asyncio
    async def test_most_recent_yesterday_still_counts(self) -> None:
        """A streak ending yesterday is valid — the job may not have
        recorded today's candidate yet."""
        today = date(2026, 9, 20)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (today - timedelta(days=1),),              # 2026-09-19
            (today - timedelta(days=2),),              # 2026-09-18
        ]
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        streak = await repo.get_stability_streak(
            horizon="24h",
            market_condition=None,
            model_name="xgboost_fresh",
            metric_name="mae",
            today=today,
        )

        assert streak == 2

    @pytest.mark.asyncio
    async def test_single_day_streak(self) -> None:
        today = date(2026, 9, 20)
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(today,)]
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        streak = await repo.get_stability_streak(
            horizon="24h",
            market_condition=None,
            model_name="xgboost_fresh",
            metric_name="mae",
            today=today,
        )

        assert streak == 1

    @pytest.mark.asyncio
    async def test_regime_filter_in_statement(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.get_stability_streak(
            horizon="24h",
            market_condition="bull",
            model_name="xgboost_fresh",
            metric_name="mae",
            today=date(2026, 9, 20),
        )

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition = 'bull'" in compiled


# ============================================================
# GET RECENT CANDIDATES
# ============================================================
class TestGetRecentCandidates:
    """Tests for get_recent_candidates()."""

    @pytest.mark.asyncio
    async def test_returns_list_of_dicts(self) -> None:
        rows = [
            _make_candidate_dict(id=3, candidate_date=date(2026, 9, 20)),
            _make_candidate_dict(id=2, candidate_date=date(2026, 9, 19)),
            _make_candidate_dict(id=1, candidate_date=date(2026, 9, 18)),
        ]
        session = _mock_session_with_mappings(rows)
        repo = ChampionRepository(session)

        result = await repo.get_recent_candidates(
            horizon="24h", days=30
        )

        assert len(result) == 3
        assert all(isinstance(r, dict) for r in result)

    @pytest.mark.asyncio
    async def test_empty_returns_empty_list(self) -> None:
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        result = await repo.get_recent_candidates(
            horizon="24h", days=30
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_global_uses_is_null(self) -> None:
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        await repo.get_recent_candidates(
            horizon="24h", market_condition=None, days=30
        )

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition IS NULL" in compiled

    @pytest.mark.asyncio
    async def test_regime_uses_equality(self) -> None:
        session = _mock_session_with_mappings([])
        repo = ChampionRepository(session)

        await repo.get_recent_candidates(
            horizon="24h", market_condition="bull", days=30
        )

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "market_condition = 'bull'" in compiled


# ============================================================
# RECORD CANDIDATE
# ============================================================
class TestRecordCandidate:
    """Tests for record_candidate()."""

    @pytest.mark.asyncio
    async def test_returns_true_when_inserted(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 42
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        inserted = await repo.record_candidate(_make_candidate_row())

        assert inserted is True

    @pytest.mark.asyncio
    async def test_returns_false_when_conflict(self) -> None:
        """ON CONFLICT DO NOTHING returns None for the RETURNING clause."""
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        inserted = await repo.record_candidate(_make_candidate_row())

        assert inserted is False

    @pytest.mark.asyncio
    async def test_statement_uses_on_conflict_do_nothing(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 1
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.record_candidate(_make_candidate_row())

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "ON CONFLICT" in compiled
        assert "DO NOTHING" in compiled


# ============================================================
# PRUNE OLD CANDIDATES
# ============================================================
class TestPruneOldCandidates:
    """Tests for prune_old_candidates()."""

    @pytest.mark.asyncio
    async def test_returns_count_of_deleted_rows(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = [(1,), (2,), (3,), (4,), (5,)]
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        count = await repo.prune_old_candidates(keep_days=180)

        assert count == 5

    @pytest.mark.asyncio
    async def test_returns_zero_when_nothing_deleted(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        count = await repo.prune_old_candidates(keep_days=180)

        assert count == 0

    @pytest.mark.asyncio
    async def test_statement_is_delete(self) -> None:
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        session.execute.return_value = mock_result

        repo = ChampionRepository(session)
        await repo.prune_old_candidates(keep_days=30)

        stmt = session.execute.call_args.args[0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "DELETE" in compiled
        assert "candidate_date" in compiled