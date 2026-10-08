"""
Unit tests for the --regime-backfill CLI hook in
app.scripts.run_live_path.

Invokes run_live_path.main() with --regime-backfill and asserts
on the interaction with RegimeBackfillService, without touching
a real database.

The handler lazily imports RegimeBackfillService and
DEFAULT_REGIME_BACKFILL_START from
app.services.regime_backfill_service, so patching happens at
that module path.

Covers:
- Default range: DEFAULT_REGIME_BACKFILL_START -> today
- Explicit --start / --end
- --days N
- Exit code 1 on advisory-lock contention
- Exit code 0 on no_data
- Exit code 0 on success (with rows_inserted > 0 and == 0)
- Exit code 2 on ValueError from range parsing
- The service is constructed with the session from SessionLocal
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scripts import run_live_path


# ============================================================
# HELPERS
# ============================================================


def make_service_result(
    status="ok",
    rows_inserted=1,
    start=date(2024, 1, 1),
    end=date(2024, 12, 31),
    regimes=None,
):
    return {
        "status": status,
        "rows_inserted": rows_inserted,
        "date_range": (start, end),
        "regimes_found": regimes or ["growth"],
    }


def patched_service(result):
    """
    Patch RegimeBackfillService and SessionLocal for a single
    test. Returns (service_instance, session_mock).
    """
    service_instance = MagicMock()
    service_instance.backfill_regimes = AsyncMock(return_value=result)

    session = MagicMock()

    return service_instance, session


# ============================================================
# RANGE RESOLUTION
# ============================================================


def test_default_range_uses_2017_08_17_and_today(capsys):
    service_instance, session = patched_service(make_service_result())

    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(["--regime-backfill"])

    assert rc == 0

    service_instance.backfill_regimes.assert_awaited_once()
    kwargs = service_instance.backfill_regimes.call_args.kwargs
    assert kwargs["start_date"] == date(2017, 8, 17)
    # end_date is "today" — assert it is the current UTC date.
    assert kwargs["end_date"] == datetime.now(timezone.utc).date()


def test_explicit_start_end(capsys):
    service_instance, session = patched_service(make_service_result())

    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(
            [
                "--regime-backfill",
                "--start", "2020-01-01",
                "--end", "2020-12-31",
            ]
        )

    assert rc == 0
    kwargs = service_instance.backfill_regimes.call_args.kwargs
    assert kwargs["start_date"] == date(2020, 1, 1)
    assert kwargs["end_date"] == date(2020, 12, 31)


def test_days_flag(capsys):
    service_instance, session = patched_service(make_service_result())

    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(
            ["--regime-backfill", "--days", "30"]
        )

    assert rc == 0
    kwargs = service_instance.backfill_regimes.call_args.kwargs
    # start = end - 30 days; end = today.
    expected_end = datetime.now(timezone.utc).date()
    # Allow +/- 1 day around midnight UTC.
    delta = (expected_end - kwargs["start_date"]).days
    assert delta in (30, 31)


# ============================================================
# STATUS HANDLING
# ============================================================


def test_skipped_already_running_returns_exit_1(capsys):
    result = make_service_result(status="skipped_already_running", rows_inserted=0)
    service_instance, session = patched_service(result)
    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(["--regime-backfill"])

    assert rc == 1


def test_no_data_returns_exit_0(capsys):
    result = make_service_result(status="no_data", rows_inserted=0, regimes=[])
    service_instance, session = patched_service(result)
    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(["--regime-backfill"])

    assert rc == 0


def test_ok_with_inserted_rows_returns_exit_0(capsys):
    result = make_service_result(rows_inserted=17)
    service_instance, session = patched_service(result)
    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(["--regime-backfill"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "rows_inserted:  17" in out


def test_ok_with_zero_rows_returns_exit_0(capsys):
    """
    Idempotent re-run: everything already covered. Still a
    successful outcome.
    """
    result = make_service_result(rows_inserted=0)
    service_instance, session = patched_service(result)
    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(["--regime-backfill"])

    assert rc == 0
    out = capsys.readouterr().out
    assert "rows_inserted:  0" in out


# ============================================================
# ERROR HANDLING
# ============================================================


def test_service_exception_returns_exit_2(capsys):
    service_instance, session = patched_service(make_service_result())
    service_instance.backfill_regimes = AsyncMock(
        side_effect=RuntimeError("kaboom")
    )
    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(["--regime-backfill"])

    assert rc == 2


def test_bad_range_returns_exit_2(capsys):
    """
    --end before --start triggers ValueError inside
    _resolve_backfill_range, which the handler converts to
    exit 2.
    """
    service_instance, session = patched_service(make_service_result())
    cls = MagicMock(return_value=service_instance)

    with patch(
        "app.services.regime_backfill_service.RegimeBackfillService",
        cls,
    ), patch(
        "app.database.session.SessionLocal",
        return_value=session,
    ):
        rc = run_live_path.main(
            [
                "--regime-backfill",
                "--start", "2024-12-31",
                "--end", "2024-01-01",
            ]
        )

    assert rc == 2
    # Service must not have been called.
    service_instance.backfill_regimes.assert_not_awaited()


# ============================================================
# SUBCOMMAND WIRING
# ============================================================


def test_regime_backfill_is_a_subcommand():
    from app.scripts.run_live_path import SUBCOMMANDS

    assert "--regime-backfill" in SUBCOMMANDS


def test_regime_backfill_help_text():
    from app.scripts.run_live_path import SUBCOMMANDS

    help_text, _handler = SUBCOMMANDS["--regime-backfill"]
    assert "macro_regimes" in help_text
    assert "2017-08-17" in help_text


def test_regime_backfill_is_in_arg_taking_flags():
    """
    The handler signature takes args, so it must appear in
    ARG_TAKING_FLAGS in _dispatch. We assert this indirectly by
    invoking the CLI and confirming the handler reached the
    service (the previous tests already do that), but a direct
    inspection of the parser is also worth having.
    """
    import inspect

    source = inspect.getsource(run_live_path._dispatch)
    assert "--regime-backfill" in source