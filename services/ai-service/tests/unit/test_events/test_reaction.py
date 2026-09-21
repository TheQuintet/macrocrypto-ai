"""Unit tests for app.events.reaction (A5.2).

Covers:
    - The three pure functions: price_change_percent,
      volatility_pct, classify_direction
    - Their edge cases and error paths
    - The constants (PRICE_WINDOW_HOURS_BEFORE / AFTER,
      DIRECTION_THRESHOLD_PCT, MIN_PRICE_POINTS,
      PRICE_LOOKUP_TOLERANCE_HOURS)
    - The ReactionSkip and ReactionCalculationResult dataclasses
    - The ReactionCalculator orchestrator against a fake
      PredictionRepository:
        - happy path: two prices + window → one row with the
          expected metrics
        - missing before price → skip
        - missing after price → skip
        - empty window → skip
        - insufficient window prices → skip
        - invalid event spec → skip
        - repository raises → recorded in errors, run continues
        - window sizes passed to the constructor are honored
        - the row is shaped as an EventImpactRow

Pure-function tests have no I/O. The orchestrator tests use a
local fake repository that records its calls and returns canned
values, so no real database is needed.
"""

from datetime import date, datetime, timezone

import pandas as pd
import pytest

from app.database.repositories.event_impact_repository import (
    EventImpactRow,
)
from app.events.reaction import (
    DIRECTION_THRESHOLD_PCT,
    MIN_PRICE_POINTS,
    PRICE_LOOKUP_TOLERANCE_HOURS,
    PRICE_WINDOW_HOURS_AFTER,
    PRICE_WINDOW_HOURS_BEFORE,
    ReactionCalculationResult,
    ReactionCalculator,
    ReactionSkip,
    classify_direction,
    price_change_percent,
    volatility_pct,
)


# ============================================================
# CONSTANTS
# ============================================================
class TestConstants:
    """The module's public constants are what the A5.2 spec says."""

    def test_window_before(self) -> None:
        assert PRICE_WINDOW_HOURS_BEFORE == 24

    def test_window_after(self) -> None:
        assert PRICE_WINDOW_HOURS_AFTER == 24

    def test_tolerance(self) -> None:
        assert PRICE_LOOKUP_TOLERANCE_HOURS == 1

    def test_direction_threshold(self) -> None:
        assert DIRECTION_THRESHOLD_PCT == 0.5

    def test_min_price_points(self) -> None:
        assert MIN_PRICE_POINTS == 3


# ============================================================
# price_change_percent
# ============================================================
class TestPriceChangePercent:
    """Tests for price_change_percent()."""

    def test_positive_change(self) -> None:
        assert price_change_percent(100.0, 110.0) == pytest.approx(10.0)

    def test_negative_change(self) -> None:
        assert price_change_percent(110.0, 100.0) == pytest.approx(
            (100.0 - 110.0) / 110.0 * 100.0
        )

    def test_zero_change(self) -> None:
        assert price_change_percent(100.0, 100.0) == 0.0

    def test_large_change(self) -> None:
        assert price_change_percent(100.0, 200.0) == pytest.approx(100.0)

    def test_zero_before_raises(self) -> None:
        with pytest.raises(ValueError, match="price_before must be positive"):
            price_change_percent(0.0, 100.0)

    def test_negative_before_raises(self) -> None:
        with pytest.raises(ValueError, match="price_before must be positive"):
            price_change_percent(-1.0, 100.0)


# ============================================================
# volatility_pct
# ============================================================
class TestVolatilityPct:
    """Tests for volatility_pct()."""

    def test_constant_series_is_zero(self) -> None:
        assert volatility_pct([100.0, 100.0, 100.0, 100.0]) == 0.0

    def test_linear_rise(self) -> None:
        # Same pct_change at every step → std of a constant series.
        # 100 → 110 → 121: two equal +10% returns → std = 0.
        assert volatility_pct([100.0, 110.0, 121.0]) == pytest.approx(0.0)

    def test_alternating_series_nonzero(self) -> None:
        v = volatility_pct([100.0, 110.0, 100.0, 110.0])
        # Returns: +0.1, -0.0909..., +0.1 → nonzero std.
        assert v > 0.0

    def test_exact_three_points_minimum(self) -> None:
        # Exactly MIN_PRICE_POINTS should pass.
        assert volatility_pct([100.0, 101.0, 102.0]) >= 0.0

    def test_too_few_prices_raises(self) -> None:
        with pytest.raises(
            ValueError, match="at least .* prices"
        ):
            volatility_pct([100.0, 101.0])

    def test_empty_list_raises(self) -> None:
        with pytest.raises(ValueError):
            volatility_pct([])

    def test_non_positive_price_raises(self) -> None:
        with pytest.raises(
            ValueError, match="positive"
        ):
            volatility_pct([100.0, 0.0, 100.0])

    def test_negative_price_raises(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            volatility_pct([100.0, -1.0, 100.0])

    def test_is_non_negative(self) -> None:
        for prices in (
            [100.0, 101.0, 102.0, 103.0],
            [100.0, 90.0, 80.0, 70.0],
            [100.0, 110.0, 100.0, 110.0],
            [50.0, 50.5, 50.2, 50.9],
        ):
            assert volatility_pct(prices) >= 0.0

    def test_larger_swings_give_larger_volatility(self) -> None:
        calm = volatility_pct([100.0, 100.5, 100.0, 100.5])
        wild = volatility_pct([100.0, 110.0, 100.0, 110.0])
        assert wild > calm


# ============================================================
# classify_direction
# ============================================================
class TestClassifyDirection:
    """Tests for classify_direction()."""

    def test_large_positive_is_up(self) -> None:
        assert classify_direction(5.0) == "up"

    def test_large_negative_is_down(self) -> None:
        assert classify_direction(-5.0) == "down"

    def test_small_positive_is_neutral(self) -> None:
        assert classify_direction(0.1) == "neutral"

    def test_small_negative_is_neutral(self) -> None:
        assert classify_direction(-0.1) == "neutral"

    def test_zero_is_neutral(self) -> None:
        assert classify_direction(0.0) == "neutral"

    def test_exact_positive_boundary(self) -> None:
        # The rule is strict `< threshold` → boundary is NOT neutral.
        assert classify_direction(0.5) == "up"

    def test_exact_negative_boundary(self) -> None:
        assert classify_direction(-0.5) == "down"

    def test_just_under_boundary_is_neutral(self) -> None:
        assert classify_direction(0.4999) == "neutral"
        assert classify_direction(-0.4999) == "neutral"

    def test_just_over_boundary_is_directional(self) -> None:
        assert classify_direction(0.5001) == "up"
        assert classify_direction(-0.5001) == "down"

    def test_custom_threshold(self) -> None:
        assert classify_direction(1.0, threshold_pct=2.0) == "neutral"
        assert classify_direction(3.0, threshold_pct=2.0) == "up"
        assert classify_direction(-3.0, threshold_pct=2.0) == "down"


# ============================================================
# ReactionSkip
# ============================================================
class TestReactionSkip:
    """The ReactionSkip dataclass."""

    def test_to_dict(self) -> None:
        s = ReactionSkip(
            event_name="FOMC",
            event_date=date(2024, 3, 20),
            reason="missing_before_price",
            detail="2024-03-19T00:00:00+00:00",
        )
        assert s.to_dict() == {
            "event_name": "FOMC",
            "event_date": "2024-03-20",
            "reason": "missing_before_price",
            "detail": "2024-03-19T00:00:00+00:00",
        }

    def test_detail_defaults_to_empty_string(self) -> None:
        s = ReactionSkip(
            event_name="FOMC",
            event_date=date(2024, 3, 20),
            reason="invalid_event_spec",
        )
        assert s.detail == ""


# ============================================================
# ReactionCalculationResult
# ============================================================
class TestReactionCalculationResult:
    """The ReactionCalculationResult dataclass."""

    def test_to_dict_omits_rows(self) -> None:
        result = ReactionCalculationResult(
            calculated_at=datetime(2024, 3, 20, tzinfo=timezone.utc),
        )
        d = result.to_dict()
        assert "rows" not in d
        assert d["rows_built"] == 0
        assert d["skipped"] == []
        assert d["errors"] == []

    def test_to_dict_includes_skips(self) -> None:
        result = ReactionCalculationResult(
            calculated_at=datetime(2024, 3, 20, tzinfo=timezone.utc),
            skipped=[
                ReactionSkip(
                    event_name="FOMC",
                    event_date=date(2024, 3, 20),
                    reason="missing_before_price",
                )
            ],
        )
        d = result.to_dict()
        assert len(d["skipped"]) == 1
        assert d["skipped"][0]["event_name"] == "FOMC"
        assert d["skipped"][0]["reason"] == "missing_before_price"

    def test_repr(self) -> None:
        result = ReactionCalculationResult(
            calculated_at=datetime(2024, 3, 20, tzinfo=timezone.utc),
        )
        text = repr(result)
        assert "ReactionCalculationResult" in text
        assert "rows=0" in text
        assert "skipped=0" in text
        assert "errors=0" in text


# ============================================================
# FAKE PREDICTION REPOSITORY
# ============================================================
# All orchestrator tests use an event dated 2024-03-20. The fake
# uses that date as the "event midnight" reference so before/after
# discrimination is based on the target timestamp relative to the
# event, not on a hardcoded day-of-month.
_EVENT_MIDNIGHT = datetime(2024, 3, 20, 0, 0, 0, tzinfo=timezone.utc)


class _FakeRepo:
    """Fake PredictionRepository for orchestrator tests.

    The fake accepts three canned responses:
        - ``before_price`` (or None to simulate a missing lookup)
        - ``after_price``  (or None)
        - ``window``       (a list of floats, or None for empty)

    The ``window`` is materialized as a DataFrame with both a
    ``time`` and a ``close`` column, matching the real repository's
    contract from Group 1. The times are synthetic (one hour apart,
    anchored at the event midnight minus the window size), but the
    shape is what the calculator reads.

    The fake records every call so tests can assert on the
    arguments.
    """

    def __init__(
        self,
        before_price=None,
        after_price=None,
        window=None,
        raise_on_before=None,
    ) -> None:
        self._before = before_price
        self._after = after_price
        self._window = window if window is not None else []
        self._raise_on_before = raise_on_before

        # Call log
        self.price_at_calls = []
        self.range_calls = []

    async def fetch_btc_price_at(self, target_time, *, tolerance_hours=1):
        self.price_at_calls.append((target_time, tolerance_hours))
        if self._raise_on_before is not None:
            exc, self._raise_on_before = self._raise_on_before, None
            raise exc
        # Discriminate before vs. after by comparing the target
        # timestamp to the event's midnight. Anything strictly
        # before the event midnight is the "before" lookup; the
        # "after" lookup is strictly after.
        if target_time < _EVENT_MIDNIGHT:
            return self._before
        return self._after

    async def fetch_btc_prices_range(self, start, end):
        self.range_calls.append((start, end))
        # Build a DataFrame with the same column shape the real
        # repository returns. The ``time`` column is synthetic but
        # ordered; the ``close`` column carries the canned values.
        closes = list(self._window)
        times = [
            start + (end - start) * (i / max(len(closes) - 1, 1))
            for i in range(len(closes))
        ]
        return pd.DataFrame({"time": times, "close": closes})


def _event():
    return {
        "event_name": "FOMC",
        "event_date": date(2024, 3, 20),
        "impact_level": "high",
    }


# ============================================================
# ReactionCalculator — happy path
# ============================================================
class TestReactionCalculatorHappyPath:
    """run() produces one row on a fully-populated event."""

    @pytest.mark.asyncio
    async def test_one_row_built(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 63500.0, 64000.0, 64800.0, 65500.0],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])

        assert isinstance(result, ReactionCalculationResult)
        assert result.rows_built == 1
        assert len(result.rows) == 1
        assert result.skipped == []
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_row_is_event_impact_row(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 63500.0, 64000.0, 64800.0, 65500.0],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])
        row = result.rows[0]
        assert isinstance(row, EventImpactRow)

    @pytest.mark.asyncio
    async def test_row_fields(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 63500.0, 64000.0, 64800.0, 65500.0],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])
        row = result.rows[0]
        assert row.event_name == "FOMC"
        assert row.event_date == date(2024, 3, 20)
        assert row.impact_level == "high"
        assert row.btc_price_before == 63000.0
        assert row.btc_price_after == 65500.0
        assert row.price_change_percent == pytest.approx(
            (65500.0 - 63000.0) / 63000.0 * 100.0
        )
        assert row.volatility > 0.0
        assert row.direction == "up"

    @pytest.mark.asyncio
    async def test_direction_down(self) -> None:
        repo = _FakeRepo(
            before_price=70000.0,
            after_price=65000.0,
            window=[70000.0, 68000.0, 66000.0, 65000.0],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])
        assert result.rows[0].direction == "down"

    @pytest.mark.asyncio
    async def test_direction_neutral_on_tiny_change(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=63010.0,
            window=[63000.0, 63005.0, 63010.0],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])
        assert result.rows[0].direction == "neutral"

    @pytest.mark.asyncio
    async def test_no_events_returns_empty_result(self) -> None:
        repo = _FakeRepo()
        calc = ReactionCalculator(repo)
        result = await calc.run([])
        assert result.rows_built == 0
        assert result.rows == []
        assert result.skipped == []
        assert result.errors == []
        # No lookups for an empty event list.
        assert repo.price_at_calls == []
        assert repo.range_calls == []


# ============================================================
# ReactionCalculator — skips
# ============================================================
class TestReactionCalculatorSkips:
    """Missing data produces skips, not exceptions."""

    @pytest.mark.asyncio
    async def test_missing_before_price(self) -> None:
        repo = _FakeRepo(before_price=None, after_price=65500.0)
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])

        assert result.rows_built == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].reason == "missing_before_price"
        assert result.errors == []
        # The after lookup never happened.
        assert len(repo.price_at_calls) == 1

    @pytest.mark.asyncio
    async def test_missing_after_price(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=None,
            window=[63000.0, 63500.0, 64000.0],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])

        assert result.rows_built == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].reason == "missing_after_price"
        # Both lookups happened; the range lookup did not.
        assert len(repo.price_at_calls) == 2
        assert repo.range_calls == []

    @pytest.mark.asyncio
    async def test_empty_window(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[],
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])

        assert result.rows_built == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].reason == "empty_window"

    @pytest.mark.asyncio
    async def test_insufficient_window_prices(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 65500.0],  # only 2, need 3
        )
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])

        assert result.rows_built == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].reason == "insufficient_window_prices"

    @pytest.mark.asyncio
    async def test_invalid_event_spec(self) -> None:
        repo = _FakeRepo()
        calc = ReactionCalculator(repo)
        # Missing event_name
        result = await calc.run(
            [{"event_date": date(2024, 3, 20), "impact_level": "high"}]
        )
        assert result.rows_built == 0
        assert len(result.skipped) == 1
        assert result.skipped[0].reason == "invalid_event_spec"
        assert repo.price_at_calls == []

    @pytest.mark.asyncio
    async def test_datetime_event_date_is_rejected(self) -> None:
        """A datetime is a subclass of date — must be rejected."""
        repo = _FakeRepo()
        calc = ReactionCalculator(repo)
        result = await calc.run(
            [
                {
                    "event_name": "FOMC",
                    "event_date": datetime(2024, 3, 20, 12, 0, 0),
                    "impact_level": "high",
                }
            ]
        )
        assert result.rows_built == 0
        assert result.skipped[0].reason == "invalid_event_spec"

    @pytest.mark.asyncio
    async def test_multiple_events_mixed_outcomes(self) -> None:
        """One good event, one skipped, both processed."""
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 63500.0, 64000.0, 64800.0, 65500.0],
        )
        calc = ReactionCalculator(repo)
        events = [
            _event(),  # good
            {"event_name": "Bad"},  # missing date/level → skip
        ]
        result = await calc.run(events)
        assert result.rows_built == 1
        assert len(result.skipped) == 1


# ============================================================
# ReactionCalculator — errors
# ============================================================
class TestReactionCalculatorErrors:
    """A repository exception is recorded, not raised."""

    @pytest.mark.asyncio
    async def test_repo_exception_is_captured(self) -> None:
        repo = _FakeRepo(raise_on_before=RuntimeError("db down"))
        calc = ReactionCalculator(repo)
        result = await calc.run([_event()])

        assert result.rows_built == 0
        assert len(result.errors) == 1
        assert result.errors[0]["event_name"] == "FOMC"
        assert "db down" in result.errors[0]["error"]

    @pytest.mark.asyncio
    async def test_run_continues_after_error(self) -> None:
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 63500.0, 64000.0, 64800.0, 65500.0],
            raise_on_before=RuntimeError("first call fails"),
        )
        calc = ReactionCalculator(repo)
        events = [_event(), _event()]
        result = await calc.run(events)

        # First event raised; second succeeded.
        assert result.rows_built == 1
        assert len(result.errors) == 1


# ============================================================
# ReactionCalculator — constructor and window
# ============================================================
class TestReactionCalculatorConstructor:
    """Constructor validation and window handling."""

    def test_zero_before_raises(self) -> None:
        with pytest.raises(ValueError, match="hours_before must be positive"):
            ReactionCalculator(_FakeRepo(), hours_before=0)

    def test_zero_after_raises(self) -> None:
        with pytest.raises(ValueError, match="hours_after must be positive"):
            ReactionCalculator(_FakeRepo(), hours_after=0)

    def test_negative_before_raises(self) -> None:
        with pytest.raises(ValueError, match="hours_before must be positive"):
            ReactionCalculator(_FakeRepo(), hours_before=-1)

    def test_defaults_match_constants(self) -> None:
        calc = ReactionCalculator(_FakeRepo())
        assert calc.hours_before == PRICE_WINDOW_HOURS_BEFORE
        assert calc.hours_after == PRICE_WINDOW_HOURS_AFTER

    @pytest.mark.asyncio
    async def test_custom_window_is_used(self) -> None:
        """A custom window changes the range lookup bounds."""
        repo = _FakeRepo(
            before_price=63000.0,
            after_price=65500.0,
            window=[63000.0, 63500.0, 64000.0, 64800.0, 65500.0],
        )
        calc = ReactionCalculator(
            repo, hours_before=48, hours_after=48
        )
        await calc.run([_event()])
        # The range call's start should be 2024-03-18 00:00 UTC.
        start, end = repo.range_calls[0]
        assert start.date() == date(2024, 3, 18)
        assert end.date() == date(2024, 3, 22)