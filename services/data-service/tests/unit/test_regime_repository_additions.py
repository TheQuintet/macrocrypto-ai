"""
Unit tests for the RegimeRepository methods added for the
regime backfill (UNIT 1).

Pure mock-based: no database. Mirrors the pattern used in
tests/unit/test_macro_indicator_repository.py — MagicMock for
the session, assert on the calls the repository makes.

Covers:
- count_regimes
- get_regimes_in_range (overlap semantics, ordering)
- create_regime_many (empty, non-empty, no commit, flush)
- delete_open_regime (rowcount returned, no commit)
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import MagicMock

from app.database.regime_repository import RegimeRepository
from app.models.macro_regime import MacroRegime


# ============================================================
# HELPERS
# ============================================================


def make_repository():
    """Build a RegimeRepository with a mocked session."""
    db = MagicMock()
    return RegimeRepository(db), db


# ============================================================
# count_regimes
# ============================================================


def test_count_regimes_returns_query_count():
    repo, db = make_repository()

    # db.query(MacroRegime).count() -> 42
    db.query.return_value.count.return_value = 42

    assert repo.count_regimes() == 42
    db.query.assert_called_once_with(MacroRegime)


def test_count_regimes_returns_zero_on_empty_table():
    repo, db = make_repository()
    db.query.return_value.count.return_value = 0

    assert repo.count_regimes() == 0


# ============================================================
# get_regimes_in_range
# ============================================================


def test_get_regimes_in_range_returns_query_result():
    repo, db = make_repository()

    existing = [
        MagicMock(spec=MacroRegime),
        MagicMock(spec=MacroRegime),
    ]

    q = db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = existing

    result = repo.get_regimes_in_range(
        date(2024, 1, 1),
        date(2024, 12, 31),
    )

    assert result == existing
    db.query.assert_called_once_with(MacroRegime)
    q.filter.assert_called_once()
    q.order_by.assert_called_once()
    q.all.assert_called_once()


def test_get_regimes_in_range_returns_empty_when_no_match():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = []

    result = repo.get_regimes_in_range(
        date(2024, 1, 1),
        date(2024, 12, 31),
    )

    assert result == []


# ============================================================
# create_regime_many
# ============================================================


def test_create_regime_many_empty_returns_zero():
    repo, db = make_repository()

    result = repo.create_regime_many([])

    assert result == 0
    db.add_all.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_create_regime_many_adds_all_and_flushes():
    repo, db = make_repository()

    rows = [
        {
            "regime_type": "growth",
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 6, 30),
            "duration_days": 181,
        },
        {
            "regime_type": "recession",
            "start_date": date(2024, 7, 1),
            "end_date": None,
            "duration_days": None,
        },
    ]

    result = repo.create_regime_many(rows)

    assert result == 2

    db.add_all.assert_called_once()
    added = db.add_all.call_args.args[0]
    assert len(added) == 2
    assert all(isinstance(r, MacroRegime) for r in added)

    assert added[0].regime_type == "growth"
    assert added[0].start_date == date(2024, 1, 1)
    assert added[0].end_date == date(2024, 6, 30)
    assert added[0].duration_days == 181

    assert added[1].regime_type == "recession"
    assert added[1].end_date is None
    assert added[1].duration_days is None

    db.flush.assert_called_once()


def test_create_regime_many_does_not_commit():
    """
    The caller owns the transaction. This method must not
    commit — that's what makes the delete + insert sequence in
    the backfill atomic.
    """
    repo, db = make_repository()

    repo.create_regime_many(
        [
            {
                "regime_type": "growth",
                "start_date": date(2024, 1, 1),
                "end_date": None,
                "duration_days": None,
            }
        ]
    )

    db.commit.assert_not_called()


def test_create_regime_many_uses_provided_created_at():
    """
    Rows generated within one call share a created_at value.
    """
    repo, db = make_repository()

    repo.create_regime_many(
        [
            {
                "regime_type": "growth",
                "start_date": date(2024, 1, 1),
                "end_date": None,
                "duration_days": None,
            },
            {
                "regime_type": "recession",
                "start_date": date(2024, 7, 1),
                "end_date": None,
                "duration_days": None,
            },
        ]
    )

    added = db.add_all.call_args.args[0]
    assert added[0].created_at == added[1].created_at
    # Sanity: it should be tz-aware UTC.
    assert added[0].created_at.tzinfo is not None


# ============================================================
# delete_open_regime
# ============================================================


def test_delete_open_regime_returns_rowcount():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.delete.return_value = 1

    result = repo.delete_open_regime()

    assert result == 1
    db.query.assert_called_once_with(MacroRegime)
    q.filter.assert_called_once()
    q.delete.assert_called_once_with(synchronize_session=False)


def test_delete_open_regime_returns_zero_when_nothing_open():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.delete.return_value = 0

    assert repo.delete_open_regime() == 0


def test_delete_open_regime_does_not_commit():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.delete.return_value = 1

    repo.delete_open_regime()

    db.commit.assert_not_called()