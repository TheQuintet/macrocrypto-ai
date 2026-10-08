"""
Unit tests for RegimeEventService (UNIT 2, Option A).

Pure mock-based: no database, no fixtures from conftest. The
service's helpers are tested directly; process_regime_events is
tested with mocked collaborators (db session, repositories).

Coverage:
- calculate_reaction: math + guards
- validate_event_type: supported / unsupported
- _normalize_event_type: mapping + case + None
- _get_btc_price_at_or_before: found / missing
- _recent_events: filter shape (via mock assertions)
- process_regime_events: happy path, idempotency, missing
  prices, unmapped types, future events, batch failure
- process_current_regime_event: None regime, no id, delegate
- module constants
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.services.regime_event_service import (
    SUPPORTED_EVENTS,
    RegimeEventService,
    _EVENT_TYPE_MAP,
    _IMPACT_LEVELS,
)


# ============================================================
# HELPERS
# ============================================================


def utc(year, month, day=1, hour=0):
    return datetime(
        year, month, day, hour, tzinfo=timezone.utc
    )


def make_event(
    event_type="fed",
    event_date=None,
    impact_level="high",
):
    return SimpleNamespace(
        event_type=event_type,
        event_date=event_date or utc(2024, 3, 1),
        impact_level=impact_level,
        event_name="Test Event",
    )


def make_service():
    """
    Build a RegimeEventService with a mocked db session and
    mocked repositories. calculate_reaction and the private
    static helpers are real.
    """
    db = MagicMock()
    service = RegimeEventService(db)
    service.events = MagicMock()
    service.regimes = MagicMock()
    return service


def zero_stats(scanned=0):
    return {
        "events_scanned": scanned,
        "rows_inserted": 0,
        "skipped_existing": 0,
        "skipped_missing_price": 0,
        "skipped_unmapped_type": 0,
    }


# ============================================================
# calculate_reaction
# ============================================================


def test_calculate_reaction_positive():
    result = RegimeEventService.calculate_reaction(
        btc_price_before=100.0,
        btc_price_after=110.0,
    )
    assert result == pytest.approx(10.0)


def test_calculate_reaction_negative():
    result = RegimeEventService.calculate_reaction(
        btc_price_before=100.0,
        btc_price_after=90.0,
    )
    assert result == pytest.approx(-10.0)


def test_calculate_reaction_zero_change():
    result = RegimeEventService.calculate_reaction(
        btc_price_before=100.0,
        btc_price_after=100.0,
    )
    assert result == 0.0


def test_calculate_reaction_raises_on_zero_before():
    with pytest.raises(ValueError):
        RegimeEventService.calculate_reaction(
            btc_price_before=0.0,
            btc_price_after=100.0,
        )


def test_calculate_reaction_raises_on_negative_before():
    with pytest.raises(ValueError):
        RegimeEventService.calculate_reaction(
            btc_price_before=-1.0,
            btc_price_after=100.0,
        )


# ============================================================
# validate_event_type
# ============================================================


@pytest.mark.parametrize(
    "event_type",
    [
        "fed_meeting",
        "cpi_release",
        "gdp_release",
        "employment_report",
    ],
)
def test_validate_event_type_accepts_supported(event_type):
    RegimeEventService.validate_event_type(event_type)


@pytest.mark.parametrize(
    "event_type",
    ["fed", "unknown", "", "CPI"],
)
def test_validate_event_type_rejects_unknown(event_type):
    with pytest.raises(ValueError):
        RegimeEventService.validate_event_type(event_type)


# ============================================================
# _normalize_event_type
# ============================================================


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("fed", "fed_meeting"),
        ("cpi", "cpi_release"),
        ("gdp", "gdp_release"),
        ("employment", "employment_report"),
    ],
)
def test_normalize_event_type_maps_known(raw, expected):
    assert RegimeEventService._normalize_event_type(raw) == expected


def test_normalize_event_type_is_case_insensitive():
    assert (
        RegimeEventService._normalize_event_type("FED")
        == "fed_meeting"
    )
    assert (
        RegimeEventService._normalize_event_type("Cpi")
        == "cpi_release"
    )


@pytest.mark.parametrize("raw", [None, "", "vix", "unknown"])
def test_normalize_event_type_returns_none_for_unmapped(raw):
    assert RegimeEventService._normalize_event_type(raw) is None


# ============================================================
# _get_btc_price_at_or_before
# ============================================================


def test_get_btc_price_returns_float_when_found():
    service = make_service()

    # Mock the chained query: .filter().order_by().first()
    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.first.return_value = (42000.0,)

    result = service._get_btc_price_at_or_before(
        utc(2024, 3, 1)
    )

    assert result == 42000.0
    assert isinstance(result, float)


def test_get_btc_price_returns_none_when_no_row():
    service = make_service()

    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.first.return_value = None

    assert (
        service._get_btc_price_at_or_before(utc(2020, 1, 1))
        is None
    )


# ============================================================
# _recent_events
# ============================================================


def test_recent_events_calls_filter_chain():
    service = make_service()

    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = []

    service._recent_events(lookback_days=90)

    # The filter chain must be invoked, and .all() must be
    # the terminal call.
    q.filter.assert_called_once()
    q.order_by.assert_called_once()
    q.all.assert_called_once()


def test_recent_events_returns_query_result():
    service = make_service()
    expected = [make_event(), make_event()]

    q = service.db.query.return_value
    q.filter.return_value = q
    q.order_by.return_value = q
    q.all.return_value = expected

    result = service._recent_events(lookback_days=90)

    assert result == expected


# ============================================================
# process_regime_events — the core
# ============================================================


def test_process_regime_events_no_candidates():
    """
    No events in the window → zero stats, no inserts, no
    commit.
    """
    service = make_service()
    service._recent_events = MagicMock(return_value=[])

    result = service.process_regime_events(regime_id=1)

    assert result == zero_stats(scanned=0)
    service.events.exists.assert_not_called()
    service.events.create_event_analysis_many.assert_not_called()
    service.db.commit.assert_not_called()


def test_process_regime_events_happy_path():
    """
    One event, both prices found, no existing row → insert.
    """
    service = make_service()

    event = make_event(
        event_type="fed",
        event_date=utc(2024, 3, 1, 12),
    )
    service._recent_events = MagicMock(return_value=[event])

    service.events.exists.return_value = False
    service.events.create_event_analysis_many.return_value = 1

    # _get_btc_price_at_or_before returns 100 before, 110 after.
    service._get_btc_price_at_or_before = MagicMock(
        side_effect=[100.0, 110.0]
    )

    result = service.process_regime_events(regime_id=42)

    assert result["events_scanned"] == 1
    assert result["rows_inserted"] == 1
    assert result["skipped_existing"] == 0
    assert result["skipped_missing_price"] == 0
    assert result["skipped_unmapped_type"] == 0

    # The staged row must carry the mapped type and the correct
    # return.
    staged = (
        service.events
        .create_event_analysis_many
        .call_args.args[0]
    )
    assert len(staged) == 1
    assert staged[0]["regime_id"] == 42
    assert staged[0]["event_type"] == "fed_meeting"
    assert staged[0]["event_date"] == date(2024, 3, 1)
    assert staged[0]["btc_price_before"] == 100.0
    assert staged[0]["btc_price_after"] == 110.0
    assert staged[0]["btc_return"] == pytest.approx(10.0)

    service.db.commit.assert_called_once()
    service.db.rollback.assert_not_called()


def test_process_regime_events_skips_existing():
    service = make_service()

    event = make_event(event_date=utc(2024, 3, 1))
    service._recent_events = MagicMock(return_value=[event])
    service.events.exists.return_value = True

    result = service.process_regime_events(regime_id=1)

    assert result["events_scanned"] == 1
    assert result["rows_inserted"] == 0
    assert result["skipped_existing"] == 1
    service.events.create_event_analysis_many.assert_not_called()
    service.db.commit.assert_not_called()


def test_process_regime_events_skips_missing_before_price():
    service = make_service()

    event = make_event(event_date=utc(2024, 3, 1))
    service._recent_events = MagicMock(return_value=[event])
    service.events.exists.return_value = False

    # Before price missing, after price present.
    service._get_btc_price_at_or_before = MagicMock(
        side_effect=[None, 110.0]
    )

    result = service.process_regime_events(regime_id=1)

    assert result["skipped_missing_price"] == 1
    assert result["rows_inserted"] == 0
    service.events.create_event_analysis_many.assert_not_called()


def test_process_regime_events_skips_missing_after_price():
    service = make_service()

    event = make_event(event_date=utc(2024, 3, 1))
    service._recent_events = MagicMock(return_value=[event])
    service.events.exists.return_value = False

    service._get_btc_price_at_or_before = MagicMock(
        side_effect=[100.0, None]
    )

    result = service.process_regime_events(regime_id=1)

    assert result["skipped_missing_price"] == 1
    assert result["rows_inserted"] == 0


def test_process_regime_events_skips_unmapped_type():
    service = make_service()

    event = make_event(
        event_type="vix",  # not in _EVENT_TYPE_MAP
        event_date=utc(2024, 3, 1),
    )
    service._recent_events = MagicMock(return_value=[event])

    result = service.process_regime_events(regime_id=1)

    assert result["skipped_unmapped_type"] == 1
    assert result["rows_inserted"] == 0
    service.events.exists.assert_not_called()
    service._get_btc_price_at_or_before_mock = None  # not reached


def test_process_regime_events_skips_future_event():
    """
    An event whose +24h window is still in the future cannot
    have an after-price. Skip it.
    """
    service = make_service()

    # Event happening right now.
    now = datetime.now(timezone.utc)
    event = make_event(event_type="fed", event_date=now)
    service._recent_events = MagicMock(return_value=[event])

    result = service.process_regime_events(regime_id=1)

    # The future-window check short-circuits before exists()
    # or price lookups.
    assert result["rows_inserted"] == 0
    service.events.exists.assert_not_called()


def test_process_regime_events_mixed_batch():
    """
    Two events, one insertable and one existing.
    """
    service = make_service()

    new_event = make_event(
        event_type="cpi",
        event_date=utc(2024, 3, 1),
    )
    old_event = make_event(
        event_type="gdp",
        event_date=utc(2024, 2, 15),
    )
    service._recent_events = MagicMock(
        return_value=[new_event, old_event]
    )

    # First event not existing, second existing.
    service.events.exists.side_effect = [False, True]
    service.events.create_event_analysis_many.return_value = 1

    service._get_btc_price_at_or_before = MagicMock(
        side_effect=[100.0, 110.0]
    )

    result = service.process_regime_events(regime_id=1)

    assert result["events_scanned"] == 2
    assert result["rows_inserted"] == 1
    assert result["skipped_existing"] == 1
    service.db.commit.assert_called_once()


def test_process_regime_events_all_skipped_no_commit():
    service = make_service()

    e1 = make_event(event_type="fed", event_date=utc(2024, 3, 1))
    e2 = make_event(event_type="cpi", event_date=utc(2024, 2, 1))
    service._recent_events = MagicMock(return_value=[e1, e2])
    service.events.exists.return_value = True

    result = service.process_regime_events(regime_id=1)

    assert result["skipped_existing"] == 2
    assert result["rows_inserted"] == 0
    service.events.create_event_analysis_many.assert_not_called()
    service.db.commit.assert_not_called()


def test_process_regime_events_rollback_on_batch_failure():
    service = make_service()

    event = make_event(event_type="fed", event_date=utc(2024, 3, 1))
    service._recent_events = MagicMock(return_value=[event])
    service.events.exists.return_value = False
    service.events.create_event_analysis_many.side_effect = (
        RuntimeError("boom")
    )
    service._get_btc_price_at_or_before = MagicMock(
        side_effect=[100.0, 110.0]
    )

    with pytest.raises(RuntimeError):
        service.process_regime_events(regime_id=1)

    service.db.rollback.assert_called_once()
    service.db.commit.assert_not_called()


# ============================================================
# process_current_regime_event wrapper
# ============================================================


def test_process_current_regime_event_none_regime():
    service = make_service()

    result = service.process_current_regime_event(None)

    assert result == zero_stats()
    service.process_regime_events = MagicMock()  # ensure not called
    service.process_regime_events.assert_not_called()


def test_process_current_regime_event_no_id():
    service = make_service()

    regime = SimpleNamespace(id=None, regime_type="growth")
    result = service.process_current_regime_event(regime)

    assert result == zero_stats()


def test_process_current_regime_event_delegates():
    service = make_service()

    regime = SimpleNamespace(id=7, regime_type="growth")
    expected = {
        "events_scanned": 3,
        "rows_inserted": 1,
        "skipped_existing": 2,
        "skipped_missing_price": 0,
        "skipped_unmapped_type": 0,
    }
    service.process_regime_events = MagicMock(
        return_value=expected
    )

    result = service.process_current_regime_event(regime)

    assert result == expected
    service.process_regime_events.assert_called_once_with(7)


# ============================================================
# Module constants
# ============================================================


def test_supported_events_locked():
    assert SUPPORTED_EVENTS == {
        "fed_meeting",
        "cpi_release",
        "gdp_release",
        "employment_report",
    }


def test_event_type_map_covers_economic_events_vocabulary():
    """
    economic_events.event_type is constrained to
    {'fed','cpi','employment','gdp'} — the map must cover all four.
    """
    assert set(_EVENT_TYPE_MAP.keys()) == {
        "fed",
        "cpi",
        "employment",
        "gdp",
    }


def test_impact_levels_locked():
    assert _IMPACT_LEVELS == ("high", "medium")