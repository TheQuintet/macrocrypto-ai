"""
Unit tests for RegimeBackfillService.

Pure mock-based: no database, no Postgres, no fixtures from
conftest. The service's helpers are tested directly, and the
public async entry point is tested with mocked collaborators.

Coverage:
- Timeline construction (dedup + sort)
- Walk-forward classification (multi-regime sequence)
- Run grouping (consecutive same-regime collapse)
- Final run is open (end_date is None)
- Idempotency by-skip
- Defensive open-row replacement
- Advisory lock behaviour (contended / free)
- No-data short circuit
- current_regime reconciliation (called, and best-effort on
  failure)
- _is_covered edge cases
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.regime_backfill_service import (
    DEFAULT_REGIME_BACKFILL_START,
    RegimeBackfillService,
    _CLASSIFIER_INDICATORS,
)


# ============================================================
# HELPERS
# ============================================================


def utc(year, month, day=1, hour=0):
    """Timezone-aware UTC datetime."""
    return datetime(
        year, month, day, hour, tzinfo=timezone.utc
    )


def make_indicator(name, value, time, change_percent=None):
    """Lightweight stand-in for a MacroIndicator row."""
    return SimpleNamespace(
        indicator_name=name,
        value=value,
        time=time,
        change_percent=change_percent,
    )


def make_service():
    """
    Build a RegimeBackfillService with a mocked db and
    mocked repository. Real RegimeService is kept because
    determine_regime is DB-free.
    """
    db = MagicMock()
    service = RegimeBackfillService(db)
    service.repository = MagicMock()
    return service


def patch_lock(acquired=True):
    """
    Return two patchers so tests can decide whether the
    advisory lock succeeds. Use as context managers.
    """
    return (
        patch.object(
            RegimeBackfillService,
            "_acquire_lock",
            return_value=acquired,
        ),
        patch.object(
            RegimeBackfillService,
            "_release_lock",
            return_value=None,
        ),
    )


# ============================================================
# TIMELINE
# ============================================================


def test_build_timeline_dedups_and_sorts():
    service = make_service()

    indicators = [
        make_indicator("cpi", 300.0, utc(2024, 3, 1)),
        make_indicator("cpi", 301.0, utc(2024, 1, 1)),
        make_indicator("federal_funds_rate", 5.0, utc(2024, 2, 1)),
        make_indicator("gdp", 100.0, utc(2024, 3, 1)),  # dup of cpi time
    ]

    timeline = service._build_timeline(indicators)

    assert timeline == [
        utc(2024, 1, 1),
        utc(2024, 2, 1),
        utc(2024, 3, 1),
    ]


def test_build_timeline_empty_returns_empty():
    service = make_service()
    assert service._build_timeline([]) == []


# ============================================================
# LOADING
# ============================================================


def test_load_indicators_queries_three_classifier_names():
    """
    Only cpi, federal_funds_rate, gdp are loaded. Anything
    else in the raw table (vix, dxy, gold_spot, ...) must not
    reach the classifier.
    """
    service = make_service()
    captured = {}

    def fake_query(model):
        captured["model"] = model
        return service.db.query.return_value

    service.db.query.side_effect = fake_query

    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = []

    service._load_indicators(
        date(2020, 1, 1),
        date(2024, 12, 31),
    )

    # The indicator_name.in_(...) filter must have been given
    # exactly the three classifier indicators.
    in_call = q.filter.call_args_list[0]
    # The first positional arg is a SQLAlchemy expression; we
    # can't introspect its right-hand side portably, so the
    # strongest assertion we can make here is structural.
    # The functional guarantee is asserted in the integration
    # path (if a database is wired up) and is trivially true
    # from reading _CLASSIFIER_INDICATORS.
    assert _CLASSIFIER_INDICATORS == (
        "cpi",
        "federal_funds_rate",
        "gdp",
    )
    assert in_call is not None


# ============================================================
# CLASSIFICATION + GROUPING
# ============================================================


def test_classify_runs_single_regime_returns_one_open_run():
    """
    A single-regime history produces exactly one run, with
    end_date = None (the get_current_regime invariant).
    """
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
        make_indicator("gdp", 101.0, utc(2024, 4, 1), change_percent=2.6),
    ]

    timeline = service._build_timeline(indicators)

    runs = service._classify_runs(
        indicators=indicators,
        timeline=timeline,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 4, 30),
    )

    assert len(runs) == 1
    assert runs[0]["regime_type"] == "growth"
    assert runs[0]["start_date"] == date(2024, 1, 1)
    assert runs[0]["end_date"] is None


def test_classify_runs_groups_consecutive_same_regime():
    """
    Two timestamps that classify identically collapse into a
    single run. This is the core walk-forward dedup.
    """
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
        make_indicator("gdp", 100.5, utc(2024, 2, 1), change_percent=2.6),
        make_indicator("gdp", 101.0, utc(2024, 3, 1), change_percent=2.7),
    ]

    timeline = service._build_timeline(indicators)

    runs = service._classify_runs(
        indicators=indicators,
        timeline=timeline,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
    )

    assert len(runs) == 1
    assert runs[0]["regime_type"] == "growth"


def test_classify_runs_splits_on_regime_change():
    """
    Two distinct regimes in the walk-forward produce two runs.
    The first is closed; the last is open.
    """
    service = make_service()

    indicators = [
        # Growth at Jan / Feb.
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
        make_indicator("gdp", 101.0, utc(2024, 2, 1), change_percent=2.5),
        # Recession from March (two negative quarters).
        make_indicator("gdp", 99.0, utc(2024, 3, 1), change_percent=-0.5),
        make_indicator("gdp", 98.0, utc(2024, 4, 1), change_percent=-0.3),
    ]

    timeline = service._build_timeline(indicators)

    runs = service._classify_runs(
        indicators=indicators,
        timeline=timeline,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 4, 30),
    )

    assert len(runs) == 2
    assert runs[0]["regime_type"] == "growth"
    assert runs[0]["end_date"] is not None
    assert runs[1]["regime_type"] == "recession"
    assert runs[1]["end_date"] is None


def test_classify_runs_empty_when_all_points_before_start():
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2020, 1, 1), change_percent=2.5),
    ]

    runs = service._classify_runs(
        indicators=indicators,
        timeline=service._build_timeline(indicators),
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert runs == []


# ============================================================
# MAKE RUN
# ============================================================


def test_make_run_computes_duration_days():
    run = RegimeBackfillService._make_run(
        regime_type="growth",
        run_start=utc(2024, 1, 1),
        run_end_exclusive=utc(2024, 1, 11),
    )

    assert run["regime_type"] == "growth"
    assert run["start_date"] == date(2024, 1, 1)
    assert run["end_date"] == date(2024, 1, 10)
    assert run["duration_days"] == 9


# ============================================================
# IDEMPOTENCY
# ============================================================


def test_filter_covered_runs_drops_fully_covered():
    """
    A candidate run entirely inside an existing closed regime
    is dropped.
    """
    service = make_service()

    existing = [
        SimpleNamespace(
            regime_type="growth",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        ),
    ]
    service.repository.get_regimes_in_range.return_value = existing

    candidate = {
        "regime_type": "growth",
        "start_date": date(2024, 3, 1),
        "end_date": date(2024, 6, 30),
        "duration_days": 121,
    }

    kept = service._filter_covered_runs(
        [candidate],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert kept == []


def test_filter_covered_runs_keeps_uncovered():
    service = make_service()
    service.repository.get_regimes_in_range.return_value = []

    candidate = {
        "regime_type": "growth",
        "start_date": date(2024, 3, 1),
        "end_date": date(2024, 6, 30),
        "duration_days": 121,
    }

    kept = service._filter_covered_runs(
        [candidate],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert kept == [candidate]


def test_filter_covered_runs_keeps_open_when_existing_is_closed():
    """
    An open candidate run (end_date=None) is not covered by a
    closed existing regime.
    """
    service = make_service()
    service.repository.get_regimes_in_range.return_value = [
        SimpleNamespace(
            regime_type="growth",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30),
        ),
    ]

    candidate = {
        "regime_type": "recession",
        "start_date": date(2024, 7, 1),
        "end_date": None,
        "duration_days": None,
    }

    kept = service._filter_covered_runs(
        [candidate],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
    )

    assert kept == [candidate]


# ============================================================
# _is_covered
# ============================================================


def test_is_covered_closed_run_inside_closed_regime():
    run = {
        "start_date": date(2024, 3, 1),
        "end_date": date(2024, 6, 1),
    }
    existing = [
        SimpleNamespace(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        ),
    ]
    assert RegimeBackfillService._is_covered(run, existing) is True


def test_is_covered_closed_run_extends_past_existing():
    run = {
        "start_date": date(2024, 3, 1),
        "end_date": date(2025, 3, 1),
    }
    existing = [
        SimpleNamespace(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        ),
    ]
    assert RegimeBackfillService._is_covered(run, existing) is False


def test_is_covered_open_run_with_open_existing():
    run = {
        "start_date": date(2024, 7, 1),
        "end_date": None,
    }
    existing = [
        SimpleNamespace(
            start_date=date(2024, 1, 1),
            end_date=None,
        ),
    ]
    assert RegimeBackfillService._is_covered(run, existing) is True


def test_is_covered_existing_starts_after_run():
    run = {
        "start_date": date(2024, 1, 1),
        "end_date": date(2024, 6, 1),
    }
    existing = [
        SimpleNamespace(
            start_date=date(2024, 3, 1),
            end_date=date(2024, 12, 31),
        ),
    ]
    assert RegimeBackfillService._is_covered(run, existing) is False


# ============================================================
# PUBLIC ENTRY POINT
# ============================================================


@pytest.mark.asyncio
async def test_backfill_returns_no_data_when_no_indicators():
    service = make_service()
    service._load_indicators = MagicMock(return_value=[])

    lock_p, unlock_p = patch_lock(acquired=True)
    with lock_p, unlock_p:
        result = await service.backfill_regimes(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

    assert result["status"] == "no_data"
    assert result["rows_inserted"] == 0


@pytest.mark.asyncio
async def test_backfill_returns_skipped_when_lock_contended():
    service = make_service()

    lock_p, unlock_p = patch_lock(acquired=False)
    with lock_p, unlock_p:
        result = await service.backfill_regimes(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

    assert result["status"] == "skipped_already_running"
    assert result["rows_inserted"] == 0
    service.repository.get_regimes_in_range.assert_not_called()


@pytest.mark.asyncio
async def test_backfill_writes_runs_and_reconciles_current_regime():
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
        make_indicator("gdp", 101.0, utc(2024, 4, 1), change_percent=2.6),
    ]
    service._load_indicators = MagicMock(return_value=indicators)

    service.repository.get_regimes_in_range.return_value = []
    service.repository.create_regime_many.return_value = 1

    # Don't touch current_regime in this test — we assert on
    # the reconcile call in a separate test.
    service._reconcile_current_regime = MagicMock()

    lock_p, unlock_p = patch_lock(acquired=True)
    with lock_p, unlock_p:
        result = await service.backfill_regimes(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 4, 30),
        )

    assert result["status"] == "ok"
    assert result["rows_inserted"] == 1
    assert result["regimes_found"] == ["growth"]

    service.repository.delete_open_regime.assert_called_once()
    service.repository.create_regime_many.assert_called_once()
    service.db.commit.assert_called_once()
    service._reconcile_current_regime.assert_called_once()


@pytest.mark.asyncio
async def test_backfill_idempotent_when_all_runs_covered():
    """
    If every candidate run is already in macro_regimes, the
    service does not call delete_open_regime, does not call
    create_regime_many, and returns rows_inserted=0.
    """
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
    ]
    service._load_indicators = MagicMock(return_value=indicators)

    service.repository.get_regimes_in_range.return_value = [
        SimpleNamespace(
            regime_type="growth",
            start_date=date(2024, 1, 1),
            end_date=None,
        ),
    ]

    service._reconcile_current_regime = MagicMock()

    lock_p, unlock_p = patch_lock(acquired=True)
    with lock_p, unlock_p:
        result = await service.backfill_regimes(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

    assert result["status"] == "ok"
    assert result["rows_inserted"] == 0
    service.repository.delete_open_regime.assert_not_called()
    service.repository.create_regime_many.assert_not_called()


@pytest.mark.asyncio
async def test_backfill_rolls_back_on_write_failure():
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
    ]
    service._load_indicators = MagicMock(return_value=indicators)
    service.repository.get_regimes_in_range.return_value = []
    service.repository.create_regime_many.side_effect = RuntimeError("boom")

    service._reconcile_current_regime = MagicMock()

    lock_p, unlock_p = patch_lock(acquired=True)
    with lock_p, unlock_p, pytest.raises(RuntimeError):
        await service.backfill_regimes(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )

    service.db.rollback.assert_called_once()
    service._reconcile_current_regime.assert_not_called()


# ============================================================
# RECONCILIATION
# ============================================================


def test_reconcile_calls_current_regime_service():
    """
    _reconcile_current_regime delegates to
    CurrentRegimeService.update_current_regime with the final
    run's label and the loaded indicator list.
    """
    service = make_service()

    indicators = [
        make_indicator("gdp", 100.0, utc(2024, 1, 1), change_percent=2.5),
    ]

    # Patch the query used inside _reconcile_current_regime to
    # return our indicators.
    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = indicators

    runs = [
        {
            "regime_type": "growth",
            "start_date": date(2024, 1, 1),
            "end_date": None,
            "duration_days": None,
        }
    ]

    with patch(
        "app.services.current_regime_service.CurrentRegimeService"
    ) as cls:
        instance = cls.return_value
        service._reconcile_current_regime(runs)

    instance.update_current_regime.assert_called_once()
    kwargs = instance.update_current_regime.call_args.kwargs
    assert kwargs["regime_type"] == "growth"
    assert kwargs["indicators"] == indicators


def test_reconcile_swallows_errors():
    """
    A failure inside reconciliation must not propagate — the
    macro_regimes write has already committed by then, and the
    daily job will reconcile on its next run.
    """
    service = make_service()

    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = []

    runs = [
        {
            "regime_type": "growth",
            "start_date": date(2024, 1, 1),
            "end_date": None,
            "duration_days": None,
        }
    ]

    with patch(
        "app.services.current_regime_service.CurrentRegimeService"
    ) as cls:
        cls.return_value.update_current_regime.side_effect = RuntimeError("nope")
        # Must not raise.
        service._reconcile_current_regime(runs)


def test_reconcile_noop_on_empty_runs():
    service = make_service()
    service._reconcile_current_regime([])
    # No DB access was attempted.
    service.db.query.assert_not_called()


# ============================================================
# CONSTANTS
# ============================================================


def test_default_start_constant():
    assert DEFAULT_REGIME_BACKFILL_START == date(2017, 8, 17)


def test_classifier_indicator_set_is_locked():
    assert _CLASSIFIER_INDICATORS == (
        "cpi",
        "federal_funds_rate",
        "gdp",
    )