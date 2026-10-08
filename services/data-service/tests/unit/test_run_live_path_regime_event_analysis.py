"""
Unit tests for the --regime-event-analysis CLI hook in
app.scripts.run_live_path.

Invokes run_live_path.main() with --regime-event-analysis and
asserts on the interaction with RegimeEventService and
RegimeRepository, without touching a real database.

The handler lazily imports RegimeEventService from
app.services.regime_event_service and RegimeRepository from
app.database.regime_repository, so patching happens at those
module paths.

Covers:
- Happy path: open regime exists -> service called with its id
- --days N passed through as lookback_days
- No --days -> lookback_days not in kwargs (service default)
- Invalid --days (0 or negative) -> exit 2, service not called
- No open regime -> exit 1, service not constructed
- Service exception -> exit 2
- Subcommand wiring (SUBCOMMANDS entry, help text, dispatch)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.scripts import run_live_path


# ============================================================
# HELPERS
# ============================================================


def make_stats(
    events_scanned=5,
    rows_inserted=3,
    skipped_existing=1,
    skipped_missing_price=1,
    skipped_unmapped_type=0,
):
    return {
        "events_scanned": events_scanned,
        "rows_inserted": rows_inserted,
        "skipped_existing": skipped_existing,
        "skipped_missing_price": skipped_missing_price,
        "skipped_unmapped_type": skipped_unmapped_type,
    }


def make_macro_regime(regime_id=42, regime_type="growth"):
    return MagicMock(id=regime_id, regime_type=regime_type)


# ============================================================
# HAPPY PATH
# ============================================================


def test_happy_path_calls_service_with_regime_id(capsys):
    """
    Open regime exists -> service.process_regime_events called
    with regime_id, no lookback override.
    """
    macro_regime = make_macro_regime(regime_id=42)
    service_stats = make_stats()

    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = macro_regime

    service_instance = MagicMock()
    service_instance.process_regime_events.return_value = (
        service_stats
    )

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
        return_value=service_instance,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(["--regime-event-analysis"])

    assert rc == 0
    service_instance.process_regime_events.assert_called_once_with(
        regime_id=42
    )


def test_happy_path_prints_summary(capsys):
    macro_regime = make_macro_regime(regime_id=7, regime_type="rising_rates")
    service_stats = make_stats(
        events_scanned=10,
        rows_inserted=8,
        skipped_existing=1,
        skipped_missing_price=1,
        skipped_unmapped_type=0,
    )

    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = macro_regime

    service_instance = MagicMock()
    service_instance.process_regime_events.return_value = (
        service_stats
    )

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
        return_value=service_instance,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(["--regime-event-analysis"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "regime_event_analysis" in out
    assert "regime_id:              7" in out
    assert "rising_rates" in out
    assert "events_scanned:         10" in out
    assert "rows_inserted:          8" in out


# ============================================================
# --days OVERRIDE
# ============================================================


def test_days_flag_passed_as_lookback():
    macro_regime = make_macro_regime(regime_id=42)

    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = macro_regime

    service_instance = MagicMock()
    service_instance.process_regime_events.return_value = (
        make_stats()
    )

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
        return_value=service_instance,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(
            ["--regime-event-analysis", "--days", "30"]
        )

    assert rc == 0
    service_instance.process_regime_events.assert_called_once_with(
        regime_id=42,
        lookback_days=30,
    )


def test_no_days_flag_uses_service_default():
    """
    When --days is not given, the handler must NOT pass
    lookback_days, so the service falls back to its own default
    (_DEFAULT_LOOKBACK_DAYS).
    """
    macro_regime = make_macro_regime(regime_id=42)

    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = macro_regime

    service_instance = MagicMock()
    service_instance.process_regime_events.return_value = (
        make_stats()
    )

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
        return_value=service_instance,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(["--regime-event-analysis"])

    assert rc == 0
    kwargs = (
        service_instance.process_regime_events.call_args.kwargs
    )
    assert "lookback_days" not in kwargs


@pytest.mark.parametrize("bad_days", ["0", "-5"])
def test_invalid_days_returns_exit_2(bad_days):
    """
    Zero or negative --days must be rejected before the service
    is called.
    """
    macro_regime = make_macro_regime(regime_id=42)

    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = macro_regime

    service_instance = MagicMock()

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
        return_value=service_instance,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(
            ["--regime-event-analysis", "--days", bad_days]
        )

    assert rc == 2
    service_instance.process_regime_events.assert_not_called()


# ============================================================
# NO OPEN REGIME
# ============================================================


def test_no_open_regime_returns_exit_1():
    """
    If macro_regimes has no open row (backfill never ran),
    exit 1 with a clear message. The service must not be
    constructed.
    """
    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = None

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
    ) as service_cls, patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(["--regime-event-analysis"])

    assert rc == 1
    service_cls.assert_not_called()


# ============================================================
# SERVICE EXCEPTION
# ============================================================


def test_service_exception_returns_exit_2():
    macro_regime = make_macro_regime(regime_id=42)

    repo_instance = MagicMock()
    repo_instance.get_current_regime.return_value = macro_regime

    service_instance = MagicMock()
    service_instance.process_regime_events.side_effect = (
        RuntimeError("kaboom")
    )

    with patch(
        "app.database.regime_repository.RegimeRepository",
        return_value=repo_instance,
    ), patch(
        "app.services.regime_event_service.RegimeEventService",
        return_value=service_instance,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=MagicMock(),
    ):
        rc = run_live_path.main(["--regime-event-analysis"])

    assert rc == 2


# ============================================================
# SUBCOMMAND WIRING
# ============================================================


def test_regime_event_analysis_is_a_subcommand():
    from app.scripts.run_live_path import SUBCOMMANDS

    assert "--regime-event-analysis" in SUBCOMMANDS


def test_regime_event_analysis_help_text():
    from app.scripts.run_live_path import SUBCOMMANDS

    help_text, _handler = SUBCOMMANDS["--regime-event-analysis"]
    assert "regime_event_analysis" in help_text
    assert "--days" in help_text


def test_regime_event_analysis_is_in_arg_taking_flags():
    """
    The handler signature takes args, so it must appear in
    ARG_TAKING_FLAGS in _dispatch. Confirmed indirectly by the
    earlier tests (which pass --days and see it forwarded), but
    a direct source inspection is cheap insurance.
    """
    import inspect

    source = inspect.getsource(run_live_path._dispatch)
    assert "--regime-event-analysis" in source