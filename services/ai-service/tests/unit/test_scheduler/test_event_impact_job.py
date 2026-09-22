"""Unit tests for daily_event_impact_update_job (A5.5).

The job reads every row from ``historical_event_impacts``,
recomputes the BTC reaction with A5.2's ``ReactionCalculator``,
and updates stored rows whose reaction changed. It is idempotent:
a second run the same day is a no-op.

The job itself is mocked at the repository and calculator
boundaries — no live DB, no live calculator, no live BTC price
data is required.

Test organization:
    - TestEventRowMatches: the pure comparison helper
    - TestDailyEventImpactUpdateJob: the job body
        - no rows: empty summary
        - unchanged rows: zero writes
        - changed rows: delete + re-insert
        - recompute skips: row preserved, counted under skipped
        - row vanished before update: counted under skipped
        - per-event exception: counted under failed, loop continues
        - read failure: RuntimeError raised
"""

from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, patch

import pytest

from app.database.repositories.event_impact_repository import (
    EventImpactRow,
)
from app.events.reaction import (
    ReactionCalculationResult,
    ReactionSkip,
)
from app.scheduler.jobs import (
    _event_row_matches,
    daily_event_impact_update_job,
)


# ============================================================
# HELPERS
# ============================================================
def _stored_row(
    name: str = "FOMC",
    day: int = 20,
    before: float = 63000.0,
    after: float = 65500.0,
    change: float = 3.9683,
    vol: float = 1.3372,
    direction: str = "up",
) -> Dict[str, Any]:
    """Build a dict shaped like a historical_event_impacts read row."""
    return {
        "event_name": name,
        "event_date": date(2024, 3, day),
        "impact_level": "high",
        "btc_price_before": before,
        "btc_price_after": after,
        "price_change_percent": change,
        "volatility": vol,
        "direction": direction,
    }


def _computed_row(
    name: str = "FOMC",
    day: int = 20,
    before: float = 63000.0,
    after: float = 65500.0,
    change: float = 3.9683,
    vol: float = 1.3372,
    direction: str = "up",
) -> EventImpactRow:
    """Build an EventImpactRow as the calculator would produce."""
    return EventImpactRow(
        event_name=name,
        event_date=date(2024, 3, day),
        impact_level="high",
        btc_price_before=before,
        btc_price_after=after,
        price_change_percent=change,
        volatility=vol,
        direction=direction,
    )


def _calc_result(
    rows: Optional[List[EventImpactRow]] = None,
    skipped: Optional[List[ReactionSkip]] = None,
) -> ReactionCalculationResult:
    """Build a ReactionCalculationResult for the fake calculator."""
    rows = rows or []
    return ReactionCalculationResult(
        calculated_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
        rows=rows,
        rows_built=len(rows),
        skipped=skipped or [],
    )


class _FakeEventRepo:
    """Fake EventImpactRepository for the job tests.

    Accepts a canned ``fetch_all`` result, records every
    ``delete_by_event`` and ``save_rows`` call, and can be
    configured to fail on fetch or on delete.
    """

    def __init__(
        self,
        stored_rows: Optional[List[Dict[str, Any]]] = None,
        fetch_error: Optional[Exception] = None,
        delete_return: bool = True,
    ) -> None:
        self._stored = stored_rows if stored_rows is not None else []
        self._fetch_error = fetch_error
        self._delete_return = delete_return
        self.fetch_calls: List[Dict[str, Any]] = []
        self.deletes: List[tuple] = []
        self.writes: List[List[EventImpactRow]] = []

    async def fetch_all(
        self,
        impact_level: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        self.fetch_calls.append({"impact_level": impact_level, "limit": limit})
        if self._fetch_error is not None:
            raise self._fetch_error
        return list(self._stored)

    async def delete_by_event(
        self, event_name: str, event_date: date
    ) -> bool:
        self.deletes.append((event_name, event_date))
        return self._delete_return

    async def save_rows(self, rows: List[EventImpactRow]) -> int:
        self.writes.append(list(rows))
        return len(rows)


class _FakeSessionScope:
    """Async context manager mimicking ``session_scope``."""

    async def __aenter__(self):
        return object()

    async def __aexit__(self, *args):
        return False


class _FakeReactionCalculator:
    """Fake ReactionCalculator returning canned per-event results."""

    def __init__(self, results_by_key: Dict[str, Any]) -> None:
        self._results = results_by_key
        self.run_calls: List[List[Any]] = []

    async def run(self, events: List[Any]) -> ReactionCalculationResult:
        self.run_calls.append(list(events))
        event = events[0]
        key = f"{event['event_name']}_{event['event_date'].isoformat()}"
        result = self._results.get(key)
        if result is None:
            # Default: no row, no skip — the caller probably wants
            # a specific behavior for this key. Return empty.
            return _calc_result()
        if isinstance(result, Exception):
            raise result
        return result


# ============================================================
# PURE HELPER
# ============================================================
class TestEventRowMatches:
    """Tests for _event_row_matches()."""

    def test_identical_returns_true(self) -> None:
        stored = _stored_row()
        computed = _computed_row()
        assert _event_row_matches(stored, computed) is True

    def test_price_before_changed(self) -> None:
        stored = _stored_row()
        computed = _computed_row(before=63100.0)
        assert _event_row_matches(stored, computed) is False

    def test_price_after_changed(self) -> None:
        stored = _stored_row()
        computed = _computed_row(after=65600.0)
        assert _event_row_matches(stored, computed) is False

    def test_change_changed(self) -> None:
        stored = _stored_row()
        computed = _computed_row(change=4.0)
        assert _event_row_matches(stored, computed) is False

    def test_volatility_changed(self) -> None:
        stored = _stored_row()
        computed = _computed_row(vol=1.5)
        assert _event_row_matches(stored, computed) is False

    def test_direction_changed(self) -> None:
        stored = _stored_row()
        computed = _computed_row(direction="down")
        assert _event_row_matches(stored, computed) is False

    def test_exact_float_equality(self) -> None:
        # A tiny drift in a float field means "changed", not "same".
        # Tolerance-based comparison would hide a stale row.
        stored = _stored_row(vol=1.3372)
        computed = _computed_row(vol=1.33720001)
        assert _event_row_matches(stored, computed) is False


# ============================================================
# JOB — no rows
# ============================================================
class TestJobNoRows:
    """Empty repository is a valid, cheap run."""

    @pytest.mark.asyncio
    async def test_empty_repo_returns_zeros(self) -> None:
        repo = _FakeEventRepo(stored_rows=[])

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ):
            summary = await daily_event_impact_update_job()

        assert summary["events_seen"] == 0
        assert summary["events_updated"] == 0
        assert summary["events_unchanged"] == 0
        assert summary["events_skipped"] == 0
        assert summary["events_failed"] == 0
        assert summary["results"] == {}

    @pytest.mark.asyncio
    async def test_fetch_is_capped(self) -> None:
        # The job reads at most 10_000 rows; confirm the limit is
        # forwarded so a runaway table does not stall the scheduler.
        repo = _FakeEventRepo(stored_rows=[])

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ):
            await daily_event_impact_update_job()

        assert repo.fetch_calls == [{"impact_level": None, "limit": 10_000}]


# ============================================================
# JOB — unchanged
# ============================================================
class TestJobUnchanged:
    """Rows whose recomputation matches are not written."""

    @pytest.mark.asyncio
    async def test_identical_row_is_unchanged(self) -> None:
        stored = [_stored_row()]
        repo = _FakeEventRepo(stored_rows=stored)
        key = "FOMC_2024-03-20"
        calc = _FakeReactionCalculator(
            {key: _calc_result(rows=[_computed_row()])}
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ), patch(
            "app.scheduler.jobs.ReactionCalculator",
            lambda prediction_repo: calc,
        ):
            summary = await daily_event_impact_update_job()

        assert summary["events_seen"] == 1
        assert summary["events_unchanged"] == 1
        assert summary["events_updated"] == 0
        assert repo.deletes == []
        assert repo.writes == []
        assert summary["results"][key]["status"] == "unchanged"


# ============================================================
# JOB — changed
# ============================================================
class TestJobChanged:
    """Rows whose recomputation differs are deleted and re-inserted."""

    @pytest.mark.asyncio
    async def test_changed_row_is_deleted_and_reinserted(self) -> None:
        stored = [_stored_row()]
        repo = _FakeEventRepo(stored_rows=stored)
        key = "FOMC_2024-03-20"
        new_row = _computed_row(
            before=63100.0, change=3.8, vol=1.4
        )
        calc = _FakeReactionCalculator(
            {key: _calc_result(rows=[new_row])}
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ), patch(
            "app.scheduler.jobs.ReactionCalculator",
            lambda prediction_repo: calc,
        ):
            summary = await daily_event_impact_update_job()

        assert summary["events_seen"] == 1
        assert summary["events_updated"] == 1
        assert summary["events_unchanged"] == 0
        assert repo.deletes == [("FOMC", date(2024, 3, 20))]
        assert len(repo.writes) == 1
        assert repo.writes[0][0].btc_price_before == 63100.0
        assert summary["results"][key]["status"] == "updated"
        assert summary["results"][key]["old"]["volatility"] == 1.3372
        assert summary["results"][key]["new"]["volatility"] == 1.4

    @pytest.mark.asyncio
    async def test_vanish_before_update_is_skipped(self) -> None:
        # Someone else removed the row between our read and our
        # delete. Count as skipped, do not write.
        stored = [_stored_row()]
        repo = _FakeEventRepo(stored_rows=stored, delete_return=False)
        key = "FOMC_2024-03-20"
        calc = _FakeReactionCalculator(
            {key: _calc_result(rows=[_computed_row(before=63100.0)])}
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ), patch(
            "app.scheduler.jobs.ReactionCalculator",
            lambda prediction_repo: calc,
        ):
            summary = await daily_event_impact_update_job()

        assert summary["events_skipped"] == 1
        assert summary["events_updated"] == 0
        assert repo.writes == []
        assert (
            summary["results"][key]["reason"]
            == "vanished_before_update"
        )


# ============================================================
# JOB — recompute skips
# ============================================================
class TestJobRecomputeSkips:
    """A skip from the calculator leaves the stored row alone."""

    @pytest.mark.asyncio
    async def test_missing_price_is_skipped(self) -> None:
        stored = [_stored_row()]
        repo = _FakeEventRepo(stored_rows=stored)
        key = "FOMC_2024-03-20"
        skip = ReactionSkip(
            event_name="FOMC",
            event_date=date(2024, 3, 20),
            reason="missing_before_price",
            detail="2024-03-19T00:00:00+00:00",
        )
        calc = _FakeReactionCalculator(
            {key: _calc_result(skipped=[skip])}
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ), patch(
            "app.scheduler.jobs.ReactionCalculator",
            lambda prediction_repo: calc,
        ):
            summary = await daily_event_impact_update_job()

        assert summary["events_skipped"] == 1
        assert summary["events_updated"] == 0
        assert repo.deletes == []
        assert repo.writes == []
        assert (
            summary["results"][key]["reason"] == "missing_before_price"
        )


# ============================================================
# JOB — per-event exceptions
# ============================================================
class TestJobPerEventException:
    """A per-event failure is recorded, not raised."""

    @pytest.mark.asyncio
    async def test_one_failure_does_not_abort_others(self) -> None:
        stored = [
            _stored_row(name="FOMC", day=20),
            _stored_row(name="CPI", day=15),
        ]
        repo = _FakeEventRepo(stored_rows=stored)

        fomc_result = _calc_result(rows=[_computed_row()])
        cpi_result = RuntimeError("price lookup blew up")

        calc = _FakeReactionCalculator(
            {
                "FOMC_2024-03-20": fomc_result,
                "CPI_2024-03-15": cpi_result,
            }
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ), patch(
            "app.scheduler.jobs.ReactionCalculator",
            lambda prediction_repo: calc,
        ):
            summary = await daily_event_impact_update_job()

        assert summary["events_seen"] == 2
        assert summary["events_failed"] == 1
        assert summary["events_unchanged"] == 1
        assert (
            summary["results"]["CPI_2024-03-15"]["status"] == "failed"
        )
        assert (
            "price lookup blew up"
            in summary["results"]["CPI_2024-03-15"]["error"]
        )


# ============================================================
# JOB — read failure
# ============================================================
class TestJobReadFailure:
    """A failure to read the source table raises."""

    @pytest.mark.asyncio
    async def test_fetch_failure_raises_runtime_error(self) -> None:
        repo = _FakeEventRepo(
            fetch_error=RuntimeError("db down"),
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ):
            with pytest.raises(
                RuntimeError, match="Cannot read historical_event_impacts"
            ):
                await daily_event_impact_update_job()


# ============================================================
# JOB — idempotency
# ============================================================
class TestJobIdempotency:
    """Running the job twice in a row produces zero writes on the
    second run if nothing changed."""

    @pytest.mark.asyncio
    async def test_second_run_is_a_noop(self) -> None:
        stored = [_stored_row()]

        # First run: recompute matches, no writes.
        repo = _FakeEventRepo(stored_rows=stored)
        key = "FOMC_2024-03-20"
        calc = _FakeReactionCalculator(
            {key: _calc_result(rows=[_computed_row()])}
        )

        with patch(
            "app.scheduler.jobs.session_scope", _FakeSessionScope
        ), patch(
            "app.scheduler.jobs.EventImpactRepository",
            lambda session: repo,
        ), patch(
            "app.scheduler.jobs.ReactionCalculator",
            lambda prediction_repo: calc,
        ):
            first = await daily_event_impact_update_job()
            second = await daily_event_impact_update_job()

        assert first["events_unchanged"] == 1
        assert second["events_unchanged"] == 1
        assert first["events_updated"] == 0
        assert second["events_updated"] == 0
        assert repo.deletes == []
        assert repo.writes == []