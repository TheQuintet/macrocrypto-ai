"""
Unit tests for the RegimeEventRepository methods added for the
regime event analysis feature (UNIT 2, Option A).

Pure mock-based: no database. Mirrors the pattern used in
tests/unit/test_regime_repository_additions.py and
tests/unit/test_macro_indicator_repository.py — MagicMock for
the session, assert on the calls the repository makes.

Covers:
- exists (True / False paths, filter chain)
- create_event_analysis_many (empty, non-empty, no commit,
  flush, field mapping)

Does not retest create_event_analysis, get_by_regime, or
get_all — those are pre-existing and unchanged.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.database.regime_event_repository import (
    RegimeEventRepository,
)
from app.models.regime_event_analysis import RegimeEventAnalysis


# ============================================================
# HELPERS
# ============================================================


def make_repository():
    """Build a RegimeEventRepository with a mocked session."""
    db = MagicMock()
    return RegimeEventRepository(db), db


# ============================================================
# exists
# ============================================================


def test_exists_returns_true_when_row_found():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.first.return_value = MagicMock(
        spec=RegimeEventAnalysis
    )

    result = repo.exists(
        regime_id=42,
        event_type="fed_meeting",
        event_date=date(2024, 3, 1),
    )

    assert result is True
    db.query.assert_called_once_with(RegimeEventAnalysis)
    q.filter.assert_called_once()
    q.first.assert_called_once()


def test_exists_returns_false_when_no_row():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.first.return_value = None

    result = repo.exists(
        regime_id=42,
        event_type="cpi_release",
        event_date=date(2024, 3, 1),
    )

    assert result is False


def test_exists_called_with_correct_model():
    repo, db = make_repository()

    q = db.query.return_value
    q.filter.return_value = q
    q.first.return_value = None

    repo.exists(
        regime_id=1,
        event_type="gdp_release",
        event_date=date(2024, 1, 1),
    )

    db.query.assert_called_once_with(RegimeEventAnalysis)


# ============================================================
# create_event_analysis_many
# ============================================================


def test_create_event_analysis_many_empty_returns_zero():
    repo, db = make_repository()

    result = repo.create_event_analysis_many([])

    assert result == 0
    db.add_all.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_create_event_analysis_many_adds_all_and_flushes():
    repo, db = make_repository()

    rows = [
        {
            "regime_id": 1,
            "event_type": "fed_meeting",
            "event_date": date(2024, 3, 1),
            "btc_price_before": 62000.0,
            "btc_price_after": 64500.0,
            "btc_return": 4.032258064516129,
        },
        {
            "regime_id": 1,
            "event_type": "cpi_release",
            "event_date": date(2024, 3, 15),
            "btc_price_before": 68000.0,
            "btc_price_after": 66500.0,
            "btc_return": -2.2058823529411766,
        },
    ]

    result = repo.create_event_analysis_many(rows)

    assert result == 2

    db.add_all.assert_called_once()
    added = db.add_all.call_args.args[0]
    assert len(added) == 2
    assert all(
        isinstance(a, RegimeEventAnalysis) for a in added
    )

    # Field mapping — first row.
    assert added[0].regime_id == 1
    assert added[0].event_type == "fed_meeting"
    assert added[0].event_date == date(2024, 3, 1)
    assert added[0].btc_price_before == 62000.0
    assert added[0].btc_price_after == 64500.0

    # Field mapping — second row.
    assert added[1].event_type == "cpi_release"
    assert added[1].event_date == date(2024, 3, 15)
    assert added[1].btc_price_before == 68000.0
    assert added[1].btc_price_after == 66500.0

    db.flush.assert_called_once()


def test_create_event_analysis_many_does_not_commit():
    """
    The caller owns the transaction. This method must not
    commit — that's what makes the service's batch insert
    atomic with the surrounding commit / rollback.
    """
    repo, db = make_repository()

    repo.create_event_analysis_many(
        [
            {
                "regime_id": 1,
                "event_type": "fed_meeting",
                "event_date": date(2024, 3, 1),
                "btc_price_before": 100.0,
                "btc_price_after": 110.0,
                "btc_return": 10.0,
            }
        ]
    )

    db.commit.assert_not_called()


def test_create_event_analysis_many_flushes_once_for_multiple_rows():
    """
    A single flush covers the whole batch, not one per row.
    """
    repo, db = make_repository()

    repo.create_event_analysis_many(
        [
            {
                "regime_id": 1,
                "event_type": "fed_meeting",
                "event_date": date(2024, 3, 1),
                "btc_price_before": 100.0,
                "btc_price_after": 110.0,
                "btc_return": 10.0,
            },
            {
                "regime_id": 1,
                "event_type": "cpi_release",
                "event_date": date(2024, 3, 15),
                "btc_price_before": 200.0,
                "btc_price_after": 190.0,
                "btc_return": -5.0,
            },
            {
                "regime_id": 1,
                "event_type": "gdp_release",
                "event_date": date(2024, 3, 28),
                "btc_price_before": 300.0,
                "btc_price_after": 315.0,
                "btc_return": 5.0,
            },
        ]
    )

    db.flush.assert_called_once()
    db.add_all.assert_called_once()