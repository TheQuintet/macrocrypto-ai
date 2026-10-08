"""
Integration test for app.scripts.run_live_path.

Invokes the CLI through its main() entry point with each flag,
mocking the underlying service calls so no DB or network is used.
Verifies:
- --backfill calls check_and_backfill(force=True)
- --btc-hourly / --macro-hourly / --features-db print a
  "not yet implemented" message and exit 0
- --all runs backfill then the three stubs, exit 0
- exit code is non-zero when the backfill reports a failure
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.scripts import run_live_path


# ============================================================
# --backfill
# ============================================================


def test_backfill_calls_service_with_force(capsys):
    mock_check = AsyncMock(return_value=None)

    with patch.object(run_live_path, "check_and_backfill", mock_check), \
         patch.object(run_live_path, "get_backfill_status") as mock_status:
        mock_status.return_value.state = "completed"
        mock_status.return_value.current_source = None
        mock_status.return_value.error = None
        mock_status.return_value.sources_run = 8
        mock_status.return_value.sources_skipped = 0

        rc = run_live_path.main(["--backfill"])

    assert rc == 0
    mock_check.assert_awaited_once_with(force=True)


def test_backfill_returns_nonzero_on_failure(capsys):
    mock_check = AsyncMock(return_value=None)

    with patch.object(run_live_path, "check_and_backfill", mock_check), \
         patch.object(run_live_path, "get_backfill_status") as mock_status:
        mock_status.return_value.state = "failed"
        mock_status.return_value.current_source = "btc_prices"
        mock_status.return_value.error = "boom"
        mock_status.return_value.sources_run = 0
        mock_status.return_value.sources_skipped = 0

        rc = run_live_path.main(["--backfill"])

    assert rc == 1


# ============================================================
# PHASE B STUBS
# ============================================================


@pytest.mark.parametrize(
    "flag,needle",
    [
        ("--btc-hourly", "not yet implemented"),
        ("--macro-hourly", "not yet implemented"),
        ("--features-db", "not yet implemented"),
    ],
)
def test_stub_flags_print_and_exit_zero(flag, needle, capsys):
    rc = run_live_path.main([flag])
    out = capsys.readouterr().out
    assert rc == 0
    assert needle in out


# ============================================================
# --all
# ============================================================


def test_all_runs_backfill_then_stubs(capsys):
    mock_check = AsyncMock(return_value=None)

    with patch.object(run_live_path, "check_and_backfill", mock_check), \
         patch.object(run_live_path, "get_backfill_status") as mock_status:
        mock_status.return_value.state = "completed"
        mock_status.return_value.current_source = None
        mock_status.return_value.error = None
        mock_status.return_value.sources_run = 8
        mock_status.return_value.sources_skipped = 0

        rc = run_live_path.main(["--all"])

    out = capsys.readouterr().out
    assert rc == 0
    mock_check.assert_awaited_once_with(force=True)
    assert out.count("not yet implemented") == 3


# ============================================================
# ARGPARSE
# ============================================================


def test_no_flag_is_error(capsys):
    with pytest.raises(SystemExit):
        run_live_path.main([])


def test_two_flags_is_error(capsys):
    with pytest.raises(SystemExit):
        run_live_path.main(["--backfill", "--all"])