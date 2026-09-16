"""Unit tests for app.events.metrics (A5.3).

Covers:
    - The pure aggregation functions: mean_change,
      mean_volatility, direction_frequencies, min_max_change,
      confidence_interval
    - Event-type normalization (normalize_event_type)
    - The constants (CANONICAL_EVENT_TYPES, CONFIDENCE_LEVEL,
      EVENT_TYPE_ALIASES, MIN_EVENTS_FOR_METRICS)
    - The EventTypeMetrics and MetricsCalculationResult dataclasses
    - aggregate_event_type and aggregate_by_type
    - The EventMetricsCalculator orchestrator against a fake
      EventImpactRepository:
        - reads rows and returns a MetricsCalculationResult
        - forwards impact_level and limit to the repository
        - empty repository yields an empty result
        - insufficient groups are reported, not aggregated

Pure-function tests have no I/O. The orchestrator tests use a
local fake repository that records its calls and returns canned
rows, so no real database is needed.
"""

from datetime import datetime, timezone

import pytest

from app.events.metrics import (
    CANONICAL_EVENT_TYPES,
    CONFIDENCE_LEVEL,
    EVENT_TYPE_ALIASES,
    MIN_EVENTS_FOR_METRICS,
    EventMetricsCalculator,
    EventTypeMetrics,
    MetricsCalculationResult,
    aggregate_by_type,
    aggregate_event_type,
    confidence_interval,
    direction_frequencies,
    mean_change,
    mean_volatility,
    min_max_change,
    normalize_event_type,
)


# ============================================================
# HELPERS
# ============================================================
def _row(
    name: str,
    change: float,
    vol: float = 1.0,
    direction: str = "up",
) -> dict:
    """Build a dict shaped like a historical_event_impacts row."""
    return {
        "event_name": name,
        "event_date": None,
        "price_change_percent": change,
        "volatility": vol,
        "direction": direction,
    }


# ============================================================
# CONSTANTS
# ============================================================
class TestConstants:
    """The module's public constants are what the A5.3 spec says."""

    def test_canonical_event_types(self) -> None:
        assert CANONICAL_EVENT_TYPES == ("fed", "cpi", "gdp", "employment")

    def test_confidence_level(self) -> None:
        assert CONFIDENCE_LEVEL == 0.95

    def test_min_events_for_metrics(self) -> None:
        assert MIN_EVENTS_FOR_METRICS == 3

    def test_alias_table_covers_canonical_types(self) -> None:
        # Every canonical type must be reachable from at least one
        # alias — otherwise the type is unfindable from free-form names.
        reachable = set(EVENT_TYPE_ALIASES.values())
        for canonical in CANONICAL_EVENT_TYPES:
            assert canonical in reachable

    def test_alias_values_are_canonical_types(self) -> None:
        # Every alias must resolve to one of the canonical types.
        # (If a future branch adds an alias to a non-canonical key,
        # this test will catch it.)
        for value in EVENT_TYPE_ALIASES.values():
            assert value in CANONICAL_EVENT_TYPES


# ============================================================
# normalize_event_type
# ============================================================
class TestNormalizeEventType:
    """Tests for normalize_event_type()."""

    def test_fomc_variants_map_to_fed(self) -> None:
        for name in ("FOMC", "Fed", "FOMC Meeting", "FOMC Decision"):
            assert normalize_event_type(name) == "fed"

    def test_cpi_variants_map_to_cpi(self) -> None:
        for name in ("CPI", "CPI Release", "Inflation"):
            assert normalize_event_type(name) == "cpi"

    def test_gdp_variants_map_to_gdp(self) -> None:
        for name in ("GDP", "GDP Report", "Gross Domestic Product"):
            assert normalize_event_type(name) == "gdp"

    def test_employment_variants_map_to_employment(self) -> None:
        for name in ("NFP", "Non-Farm Payrolls", "Jobs Report", "Unemployment"):
            assert normalize_event_type(name) == "employment"

    def test_case_insensitive(self) -> None:
        assert normalize_event_type("fomc") == "fed"
        assert normalize_event_type("FOMC") == "fed"
        assert normalize_event_type("Fomc") == "fed"

    def test_whitespace_collapsed(self) -> None:
        assert normalize_event_type("FOMC  Meeting") == "fed"
        assert normalize_event_type("  FOMC Meeting  ") == "fed"
        assert normalize_event_type("FOMC\tMeeting") == "fed"

    def test_unknown_name_is_its_own_key(self) -> None:
        assert normalize_event_type("ECB Rate Decision") == "ecb rate decision"

    def test_unknown_name_normalized_consistently(self) -> None:
        # Two variants of the same unknown name must produce the
        # same key, so they aggregate together.
        assert normalize_event_type("ECB  Rate   Decision") == normalize_event_type(
            "ecb rate decision"
        )

    def test_none_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be None"):
            normalize_event_type(None)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            normalize_event_type("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            normalize_event_type("   ")


# ============================================================
# mean_change
# ============================================================
class TestMeanChange:
    """Tests for mean_change()."""

    def test_simple_mean(self) -> None:
        rows = [_row("FOMC", 1.0), _row("Fed", 2.0), _row("FOMC Meeting", 3.0)]
        assert mean_change(rows) == pytest.approx(2.0)

    def test_negative_values(self) -> None:
        rows = [_row("FOMC", -1.0), _row("Fed", -2.0), _row("FOMC Meeting", -3.0)]
        assert mean_change(rows) == pytest.approx(-2.0)

    def test_mixed_signs(self) -> None:
        rows = [_row("FOMC", 5.0), _row("Fed", -5.0)]
        assert mean_change(rows) == pytest.approx(0.0)

    def test_single_row(self) -> None:
        assert mean_change([_row("FOMC", 3.5)]) == pytest.approx(3.5)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one row"):
            mean_change([])

    def test_reads_dataclass_rows(self) -> None:
        from dataclasses import dataclass

        @dataclass
        class _R:
            price_change_percent: float

        rows = [_R(1.0), _R(3.0)]
        assert mean_change(rows) == pytest.approx(2.0)


# ============================================================
# mean_volatility
# ============================================================
class TestMeanVolatility:
    """Tests for mean_volatility()."""

    def test_simple_mean(self) -> None:
        rows = [_row("FOMC", 0.0, vol=1.0), _row("Fed", 0.0, vol=3.0)]
        assert mean_volatility(rows) == pytest.approx(2.0)

    def test_single_row(self) -> None:
        assert mean_volatility([_row("FOMC", 0.0, vol=1.5)]) == pytest.approx(1.5)

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one row"):
            mean_volatility([])


# ============================================================
# direction_frequencies
# ============================================================
class TestDirectionFrequencies:
    """Tests for direction_frequencies()."""

    def test_all_up(self) -> None:
        rows = [_row("FOMC", 0.0, direction="up") for _ in range(4)]
        freqs = direction_frequencies(rows)
        assert freqs == {"up": 1.0, "down": 0.0, "neutral": 0.0}

    def test_even_split(self) -> None:
        rows = [
            _row("A", 0.0, direction="up"),
            _row("B", 0.0, direction="down"),
            _row("C", 0.0, direction="neutral"),
            _row("D", 0.0, direction="up"),
        ]
        freqs = direction_frequencies(rows)
        assert freqs["up"] == pytest.approx(0.5)
        assert freqs["down"] == pytest.approx(0.25)
        assert freqs["neutral"] == pytest.approx(0.25)

    def test_sums_to_one(self) -> None:
        rows = [
            _row("A", 0.0, direction="up"),
            _row("B", 0.0, direction="up"),
            _row("C", 0.0, direction="down"),
        ]
        assert sum(direction_frequencies(rows).values()) == pytest.approx(1.0)

    def test_unknown_direction_is_ignored(self) -> None:
        # Defensive: A5.1's CHECK prevents this, but a fake row
        # could carry anything. Unknown values are not counted,
        # so the sum can be < 1.0.
        rows = [
            _row("A", 0.0, direction="up"),
            _row("B", 0.0, direction="sideways"),
        ]
        freqs = direction_frequencies(rows)
        assert freqs["up"] == pytest.approx(0.5)
        assert freqs["down"] == 0.0
        assert freqs["neutral"] == 0.0

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one row"):
            direction_frequencies([])


# ============================================================
# min_max_change
# ============================================================
class TestMinMaxChange:
    """Tests for min_max_change()."""

    def test_returns_tuple(self) -> None:
        rows = [_row("A", 1.0), _row("B", -2.0), _row("C", 5.0)]
        lo, hi = min_max_change(rows)
        assert lo == -2.0
        assert hi == 5.0

    def test_single_row(self) -> None:
        lo, hi = min_max_change([_row("A", 3.5)])
        assert lo == 3.5
        assert hi == 3.5

    def test_all_same(self) -> None:
        rows = [_row("A", 2.0), _row("B", 2.0), _row("C", 2.0)]
        lo, hi = min_max_change(rows)
        assert lo == 2.0
        assert hi == 2.0

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one row"):
            min_max_change([])


# ============================================================
# confidence_interval
# ============================================================
class TestConfidenceInterval:
    """Tests for confidence_interval()."""

    def test_single_value_returns_point(self) -> None:
        assert confidence_interval([7.0]) == (7.0, 7.0)

    def test_constant_sample_returns_point(self) -> None:
        assert confidence_interval([5.0, 5.0, 5.0, 5.0]) == (5.0, 5.0)

    def test_interval_contains_mean(self) -> None:
        values = [3.0, -1.5, 4.5, 0.1, 2.0]
        lo, hi = confidence_interval(values)
        mean = sum(values) / len(values)
        assert lo <= mean <= hi

    def test_lower_less_than_upper(self) -> None:
        lo, hi = confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0])
        assert lo < hi

    def test_wider_interval_for_smaller_sample(self) -> None:
        # Same mean, smaller n → wider interval.
        big = confidence_interval([4.9, 5.0, 5.1, 4.95, 5.05, 4.99, 5.01, 5.02, 4.98, 5.03])
        small = confidence_interval([4.9, 5.0, 5.1])
        assert (small[1] - small[0]) > (big[1] - big[0])

    def test_custom_confidence_level(self) -> None:
        # 99% interval is wider than 90%.
        narrow = confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0], confidence=0.90)
        wide = confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0], confidence=0.99)
        assert (wide[1] - wide[0]) > (narrow[1] - narrow[0])

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one value"):
            confidence_interval([])

    def test_bad_confidence_raises_above_one(self) -> None:
        with pytest.raises(ValueError, match=r"must be in \(0, 1\)"):
            confidence_interval([1.0, 2.0], confidence=1.5)

    def test_bad_confidence_raises_at_zero(self) -> None:
        with pytest.raises(ValueError, match=r"must be in \(0, 1\)"):
            confidence_interval([1.0, 2.0], confidence=0.0)

    def test_bad_confidence_raises_at_one(self) -> None:
        with pytest.raises(ValueError, match=r"must be in \(0, 1\)"):
            confidence_interval([1.0, 2.0], confidence=1.0)


# ============================================================
# EventTypeMetrics
# ============================================================
class TestEventTypeMetrics:
    """The EventTypeMetrics dataclass."""

    def test_to_dict_keys(self) -> None:
        m = EventTypeMetrics(
            event_type="fed",
            n_events=4,
            mean_change=1.5,
            mean_volatility=1.1,
            direction_frequencies={"up": 0.5, "down": 0.25, "neutral": 0.25},
            min_change=-1.0,
            max_change=4.0,
            mean_change_ci=(-0.5, 3.5),
        )
        d = m.to_dict()
        expected = {
            "event_type",
            "n_events",
            "mean_change",
            "mean_volatility",
            "direction_frequencies",
            "min_change",
            "max_change",
            "mean_change_ci",
            "confidence_level",
        }
        assert set(d.keys()) == expected

    def test_to_dict_ci_is_list(self) -> None:
        m = EventTypeMetrics(
            event_type="fed",
            n_events=3,
            mean_change=1.0,
            mean_volatility=1.0,
            direction_frequencies={"up": 1.0, "down": 0.0, "neutral": 0.0},
            min_change=1.0,
            max_change=1.0,
            mean_change_ci=(0.5, 1.5),
        )
        assert isinstance(m.to_dict()["mean_change_ci"], list)

    def test_repr(self) -> None:
        m = EventTypeMetrics(
            event_type="fed",
            n_events=4,
            mean_change=1.525,
            mean_volatility=1.175,
            direction_frequencies={"up": 1.0, "down": 0.0, "neutral": 0.0},
            min_change=1.5,
            max_change=1.6,
            mean_change_ci=(1.0, 2.0),
        )
        text = repr(m)
        assert "EventTypeMetrics" in text
        assert "event_type='fed'" in text
        assert "n_events=4" in text


# ============================================================
# MetricsCalculationResult
# ============================================================
class TestMetricsCalculationResult:
    """The MetricsCalculationResult dataclass."""

    def test_to_dict_includes_by_type(self) -> None:
        m = EventTypeMetrics(
            event_type="fed",
            n_events=3,
            mean_change=1.0,
            mean_volatility=1.0,
            direction_frequencies={"up": 1.0, "down": 0.0, "neutral": 0.0},
            min_change=1.0,
            max_change=1.0,
            mean_change_ci=(0.5, 1.5),
        )
        r = MetricsCalculationResult(
            calculated_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
            by_type={"fed": m},
            total_rows=3,
        )
        d = r.to_dict()
        assert d["total_rows"] == 3
        assert "fed" in d["by_type"]
        assert d["by_type"]["fed"]["n_events"] == 3

    def test_repr(self) -> None:
        r = MetricsCalculationResult(
            calculated_at=datetime(2026, 9, 16, tzinfo=timezone.utc),
        )
        text = repr(r)
        assert "MetricsCalculationResult" in text
        assert "types=0" in text


# ============================================================
# aggregate_event_type
# ============================================================
class TestAggregateEventType:
    """Tests for aggregate_event_type()."""

    def test_returns_metrics_when_enough(self) -> None:
        rows = [
            _row("A", 1.0, vol=0.5, direction="up"),
            _row("B", 2.0, vol=0.6, direction="up"),
            _row("C", 3.0, vol=0.7, direction="down"),
        ]
        m = aggregate_event_type("fed", rows)
        assert m is not None
        assert m.event_type == "fed"
        assert m.n_events == 3
        assert m.mean_change == pytest.approx(2.0)

    def test_returns_none_when_too_few(self) -> None:
        rows = [_row("A", 1.0), _row("B", 2.0)]
        assert aggregate_event_type("fed", rows) is None

    def test_exactly_min_is_enough(self) -> None:
        rows = [_row("A", 1.0) for _ in range(MIN_EVENTS_FOR_METRICS)]
        assert aggregate_event_type("fed", rows) is not None

    def test_ci_populated(self) -> None:
        rows = [
            _row("A", 1.0),
            _row("B", 2.0),
            _row("C", 3.0),
        ]
        m = aggregate_event_type("fed", rows)
        assert m is not None
        assert len(m.mean_change_ci) == 2
        assert m.mean_change_ci[0] <= m.mean_change <= m.mean_change_ci[1]


# ============================================================
# aggregate_by_type
# ============================================================
class TestAggregateByType:
    """Tests for aggregate_by_type()."""

    def test_groups_by_canonical_type(self) -> None:
        rows = [
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
            _row("CPI", 1.5),
            _row("CPI Release", 2.5),
            _row("Inflation", 3.5),
        ]
        by_type, unmapped, insufficient = aggregate_by_type(rows)
        assert set(by_type.keys()) == {"fed", "cpi"}
        assert by_type["fed"].n_events == 3
        assert by_type["cpi"].n_events == 3
        assert unmapped == []
        assert insufficient == []

    def test_insufficient_groups_reported(self) -> None:
        rows = [
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
            _row("GDP", 1.0),
            _row("GDP Report", 2.0),
        ]
        by_type, unmapped, insufficient = aggregate_by_type(rows)
        assert "fed" in by_type
        assert "gdp" not in by_type
        assert "gdp" in insufficient

    def test_unmapped_names_reported(self) -> None:
        rows = [
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
            _row("ECB Rate Decision", 1.0),
            _row("ECB Rate Decision", 2.0),
            _row("ECB Rate Decision", 3.0),
        ]
        by_type, unmapped, insufficient = aggregate_by_type(rows)
        assert "fed" in by_type
        assert "ecb rate decision" in by_type
        assert "ECB Rate Decision" in unmapped

    def test_empty_input(self) -> None:
        by_type, unmapped, insufficient = aggregate_by_type([])
        assert by_type == {}
        assert unmapped == []
        assert insufficient == []

    def test_row_without_event_name_skipped(self) -> None:
        # Defensive: A5.1 prevents this, but a hand-inserted row
        # could leak through. The aggregator skips rather than
        # raising, so one bad row doesn't kill the whole pass.
        rows = [
            {"event_name": None, "price_change_percent": 1.0,
             "volatility": 1.0, "direction": "up"},
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
        ]
        by_type, _, _ = aggregate_by_type(rows)
        assert by_type["fed"].n_events == 3

    def test_unknown_names_aggregate_together(self) -> None:
        # Two events both named "ECB Rate Decision" with different
        # casing/whitespace should aggregate into one group.
        rows = [
            _row("ECB Rate Decision", 1.0),
            _row("ecb rate decision", 2.0),
            _row("ECB  Rate   Decision", 3.0),
        ]
        by_type, _, _ = aggregate_by_type(rows)
        assert "ecb rate decision" in by_type
        assert by_type["ecb rate decision"].n_events == 3


# ============================================================
# FAKE EVENT IMPACT REPOSITORY
# ============================================================
class _FakeRepo:
    """Fake EventImpactRepository for orchestrator tests.

    Returns canned rows from fetch_all and records every call so
    tests can assert on the arguments.
    """

    def __init__(self, rows=None):
        self._rows = rows if rows is not None else []
        self.calls = []

    async def fetch_all(self, impact_level=None, limit=1000):
        self.calls.append((impact_level, limit))
        return list(self._rows)


# ============================================================
# EventMetricsCalculator — orchestrator
# ============================================================
class TestEventMetricsCalculator:
    """The EventMetricsCalculator orchestrator."""

    @pytest.mark.asyncio
    async def test_returns_metrics_calculation_result(self) -> None:
        repo = _FakeRepo([
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
        ])
        calc = EventMetricsCalculator(repo)
        result = await calc.run()

        assert isinstance(result, MetricsCalculationResult)
        assert result.total_rows == 3
        assert "fed" in result.by_type

    @pytest.mark.asyncio
    async def test_calls_repo_with_defaults(self) -> None:
        repo = _FakeRepo([])
        calc = EventMetricsCalculator(repo)
        await calc.run()
        assert repo.calls == [(None, 1000)]

    @pytest.mark.asyncio
    async def test_forwards_impact_level_and_limit(self) -> None:
        repo = _FakeRepo([])
        calc = EventMetricsCalculator(repo)
        await calc.run(impact_level="high", limit=500)
        assert repo.calls == [("high", 500)]

    @pytest.mark.asyncio
    async def test_empty_repo_returns_empty_result(self) -> None:
        repo = _FakeRepo([])
        calc = EventMetricsCalculator(repo)
        result = await calc.run()

        assert result.total_rows == 0
        assert result.by_type == {}
        assert result.insufficient == []
        assert result.unmapped_names == []

    @pytest.mark.asyncio
    async def test_insufficient_groups_reported(self) -> None:
        repo = _FakeRepo([
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
            _row("GDP", 1.0),
            _row("GDP Report", 2.0),
        ])
        calc = EventMetricsCalculator(repo)
        result = await calc.run()

        assert "fed" in result.by_type
        assert "gdp" not in result.by_type
        assert "gdp" in result.insufficient

    @pytest.mark.asyncio
    async def test_unmapped_names_reported(self) -> None:
        repo = _FakeRepo([
            _row("FOMC", 1.0),
            _row("Fed", 2.0),
            _row("FOMC Meeting", 3.0),
            _row("ECB Rate Decision", 1.0),
            _row("ECB Rate Decision", 2.0),
            _row("ECB Rate Decision", 3.0),
        ])
        calc = EventMetricsCalculator(repo)
        result = await calc.run()

        assert "ECB Rate Decision" in result.unmapped_names
        assert "ecb rate decision" in result.by_type

    @pytest.mark.asyncio
    async def test_elapsed_seconds_recorded(self) -> None:
        repo = _FakeRepo([_row("FOMC", 1.0)])
        calc = EventMetricsCalculator(repo)
        result = await calc.run()
        assert result.elapsed_seconds >= 0.0

    @pytest.mark.asyncio
    async def test_calculated_at_is_utc_datetime(self) -> None:
        repo = _FakeRepo([])
        calc = EventMetricsCalculator(repo)
        result = await calc.run()
        assert isinstance(result.calculated_at, datetime)
        assert result.calculated_at.tzinfo is not None