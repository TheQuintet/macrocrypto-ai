"""Unit tests for app.correlation.calculator.

Covers:
    - pearson_correlation(): happy paths, edge cases, boundaries
    - classify_strength(): threshold boundaries
    - classify_direction(): sign boundaries
    - strength_color(): label → color mapping (A1.3)
    - direction_arrow(): label → arrow mapping (A1.3)
    - resample_btc_to_daily(): column naming, dedup, sorting
    - CalculationResult: dataclass behavior
    - CorrelationCalculator: construction guards, run() paths,
      per-pair error isolation, and persistence

All tests are pure or mock-based — no live database is required.
The repository calls are mocked with AsyncMock so the calculator's
orchestration logic is exercised in isolation.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest

from app.correlation.calculator import (
    INDICATOR_SOURCE_COLUMNS,
    MEDIUM_THRESHOLD,
    MIN_SAMPLES,
    STRONG_THRESHOLD,
    WINDOWS,
    CalculationResult,
    CorrelationCalculator,
    classify_direction,
    classify_strength,
    direction_arrow,
    pearson_correlation,
    resample_btc_to_daily,
    strength_color,
)


# ============================================================
# HELPERS
# ============================================================
def _hourly_btc_frame(days: int, base_price: float = 50_000.0) -> pd.DataFrame:
    """Build an hourly BTC frame spanning `days` UTC days.

    Columns match PredictionRepository.fetch_recent_btc_data:
    time, close (plus columns that the calculator ignores).
    Values increase linearly, so the last close of each day is
    predictable: base_price + (i * 24 + 23) for day i.
    """
    now = datetime.now(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )
    start = now - timedelta(days=days)

    rows: List[Dict[str, Any]] = []
    for h in range(days * 24):
        ts = start + timedelta(hours=h)
        rows.append(
            {
                "time": ts,
                "close": base_price + h,
                "volume": 1_000_000.0,
                "volatility": 0.01,
                "dominance": 50.0,
                "active_addresses": 1_000_000.0,
                "price_lag_7d": base_price,
            }
        )
    return pd.DataFrame(rows)


def _daily_macro_frame(
    days: int,
    cpi: Optional[float] = 3.2,
    interest_rate: Optional[float] = 4.5,
    vary: bool = True,
) -> pd.DataFrame:
    """Build a daily macro frame spanning `days` UTC days.

    Columns match PredictionRepository.fetch_recent_macro_data.
    Missing columns can be simulated by passing None.

    By default, `cpi` and `interest_rate` vary linearly so Pearson
    correlation can be computed. Pass `vary=False` to force constant
    values (useful for testing zero-variance behavior).
    """
    now = datetime.now(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )
    start = now - timedelta(days=days)

    rows: List[Dict[str, Any]] = []
    for d in range(days):
        if vary:
            cpi_val = cpi + d * 0.01 if cpi is not None else None
            rate_val = (
                interest_rate + d * 0.005
                if interest_rate is not None
                else None
            )
        else:
            cpi_val = cpi
            rate_val = interest_rate

        rows.append(
            {
                "time": start + timedelta(days=d),
                "cpi": cpi_val,
                "interest_rate": rate_val,
                "m2_growth": 2.8,
                "dxy": 102.5,
                "treasury_yield": 4.2,
            }
        )
    return pd.DataFrame(rows)


def _mock_correlation_repo(saved_count: int = 0) -> MagicMock:
    """Build a mocked CorrelationRepository."""
    repo = MagicMock()
    repo.save_rows = AsyncMock(return_value=saved_count)
    return repo


def _mock_prediction_repo(
    btc_frame: Optional[pd.DataFrame] = None,
    macro_frame: Optional[pd.DataFrame] = None,
    btc_raises: Optional[Exception] = None,
    macro_raises: Optional[Exception] = None,
) -> MagicMock:
    """Build a mocked PredictionRepository.

    Only fetch_recent_btc_data and fetch_recent_macro_data are used
    by the calculator. Other methods remain as default MagicMocks.
    """
    repo = MagicMock()

    if btc_raises is not None:
        repo.fetch_recent_btc_data = AsyncMock(side_effect=btc_raises)
    else:
        repo.fetch_recent_btc_data = AsyncMock(
            return_value=btc_frame if btc_frame is not None else pd.DataFrame()
        )

    if macro_raises is not None:
        repo.fetch_recent_macro_data = AsyncMock(side_effect=macro_raises)
    else:
        repo.fetch_recent_macro_data = AsyncMock(
            return_value=macro_frame if macro_frame is not None else pd.DataFrame()
        )

    return repo


# ============================================================
# PURE: pearson_correlation
# ============================================================
class TestPearsonCorrelation:
    """Tests for pearson_correlation()."""

    def test_perfect_positive(self) -> None:
        """Perfectly co-linear increasing series → coefficient 1."""
        coefficient, n = pearson_correlation(
            [1, 2, 3, 4, 5], [2, 4, 6, 8, 10]
        )
        assert coefficient == pytest.approx(1.0)
        assert n == 5

    def test_perfect_negative(self) -> None:
        """Perfectly co-linear decreasing series → coefficient -1."""
        coefficient, n = pearson_correlation(
            [1, 2, 3, 4, 5], [10, 8, 6, 4, 2]
        )
        assert coefficient == pytest.approx(-1.0)
        assert n == 5

    def test_no_correlation(self) -> None:
        """A constant series has zero variance → None."""
        # Note: we can't easily construct "true zero correlation" with
        # small integers without luck; use a case we know returns None.
        coefficient, n = pearson_correlation(
            [1, 1, 1, 1, 1], [1, 2, 3, 4, 5]
        )
        assert coefficient is None
        assert n == 5

    def test_mismatched_lengths(self) -> None:
        """Different-length series → None with n=0."""
        coefficient, n = pearson_correlation([1, 2, 3], [1, 2])
        assert coefficient is None
        assert n == 0

    def test_none_input(self) -> None:
        """None input → None with n=0."""
        coefficient, n = pearson_correlation(None, [1, 2, 3])
        assert coefficient is None
        assert n == 0

    def test_too_few_samples(self) -> None:
        """Below MIN_SAMPLES → None with n=len."""
        assert MIN_SAMPLES == 3
        coefficient, n = pearson_correlation([1, 2], [1, 2])
        assert coefficient is None
        assert n == 2

    def test_exactly_min_samples(self) -> None:
        """Exactly MIN_SAMPLES → coefficient computed."""
        coefficient, n = pearson_correlation(
            [1, 2, 3], [2, 4, 6]
        )
        assert coefficient == pytest.approx(1.0)
        assert n == 3

    def test_zero_variance_x(self) -> None:
        """Constant x → None."""
        coefficient, n = pearson_correlation(
            [5, 5, 5, 5], [1, 2, 3, 4]
        )
        assert coefficient is None
        assert n == 4

    def test_zero_variance_y(self) -> None:
        """Constant y → None."""
        coefficient, n = pearson_correlation(
            [1, 2, 3, 4], [5, 5, 5, 5]
        )
        assert coefficient is None
        assert n == 4

    def test_nan_in_x(self) -> None:
        """NaN in x → None."""
        coefficient, n = pearson_correlation(
            [1, 2, float("nan"), 4], [1, 2, 3, 4]
        )
        assert coefficient is None
        assert n == 4

    def test_nan_in_y(self) -> None:
        """NaN in y → None."""
        coefficient, n = pearson_correlation(
            [1, 2, 3, 4], [1, 2, float("nan"), 4]
        )
        assert coefficient is None
        assert n == 4

    def test_inf_in_x(self) -> None:
        """Infinity in x → None."""
        coefficient, n = pearson_correlation(
            [1, 2, float("inf"), 4], [1, 2, 3, 4]
        )
        assert coefficient is None
        assert n == 4

    def test_coefficient_bounded(self) -> None:
        """Result is always in [-1, 1] even with floating-point drift."""
        coefficient, _ = pearson_correlation(
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            [1, 4, 9, 16, 25, 36, 49, 64, 81, 100],
        )
        assert coefficient is not None
        assert -1.0 <= coefficient <= 1.0


# ============================================================
# PURE: classify_strength
# ============================================================
class TestClassifyStrength:
    """Tests for classify_strength()."""

    def test_strong_above_threshold(self) -> None:
        """Above STRONG_THRESHOLD → strong."""
        assert STRONG_THRESHOLD == 0.7
        assert classify_strength(0.85) == "strong"
        assert classify_strength(-0.85) == "strong"

    def test_strong_boundary(self) -> None:
        """Exactly at STRONG_THRESHOLD → medium (strictly > to be strong)."""
        assert classify_strength(0.7) == "medium"
        assert classify_strength(-0.7) == "medium"

    def test_medium_in_range(self) -> None:
        """Between MEDIUM_THRESHOLD and STRONG_THRESHOLD → medium."""
        assert classify_strength(0.5) == "medium"
        assert classify_strength(-0.5) == "medium"

    def test_medium_boundary(self) -> None:
        """Exactly at MEDIUM_THRESHOLD → medium (>= to be medium)."""
        assert MEDIUM_THRESHOLD == 0.3
        assert classify_strength(0.3) == "medium"
        assert classify_strength(-0.3) == "medium"

    def test_weak_below_threshold(self) -> None:
        """Below MEDIUM_THRESHOLD → weak."""
        assert classify_strength(0.1) == "weak"
        assert classify_strength(-0.1) == "weak"
        assert classify_strength(0.0) == "weak"

    def test_uses_absolute_value(self) -> None:
        """Negative coefficients classify by magnitude, not sign."""
        assert classify_strength(-0.9) == "strong"
        assert classify_strength(-0.5) == "medium"
        assert classify_strength(-0.1) == "weak"


# ============================================================
# PURE: classify_direction
# ============================================================
class TestClassifyDirection:
    """Tests for classify_direction()."""

    def test_positive(self) -> None:
        """Coefficient > 0 → positive."""
        assert classify_direction(0.5) == "positive"
        assert classify_direction(0.0001) == "positive"

    def test_negative(self) -> None:
        """Coefficient < 0 → negative."""
        assert classify_direction(-0.5) == "negative"
        assert classify_direction(-0.0001) == "negative"

    def test_zero_is_positive(self) -> None:
        """Coefficient exactly 0 → positive (>= 0)."""
        assert classify_direction(0.0) == "positive"


# ============================================================
# PURE: strength_color (A1.3)
# ============================================================
class TestStrengthColor:
    """Tests for strength_color()."""

    def test_strong_is_green(self) -> None:
        """'strong' maps to 'green'."""
        assert strength_color("strong") == "green"

    def test_medium_is_yellow(self) -> None:
        """'medium' maps to 'yellow'."""
        assert strength_color("medium") == "yellow"

    def test_weak_is_red(self) -> None:
        """'weak' maps to 'red'."""
        assert strength_color("weak") == "red"

    def test_unknown_label_raises(self) -> None:
        """An unknown label raises ValueError."""
        with pytest.raises(ValueError, match="Unknown strength label"):
            strength_color("enormous")

    def test_empty_string_raises(self) -> None:
        """An empty string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown strength label"):
            strength_color("")

    def test_case_sensitive(self) -> None:
        """Labels are case-sensitive — 'Strong' is not 'strong'."""
        with pytest.raises(ValueError, match="Unknown strength label"):
            strength_color("Strong")

    def test_covers_all_strength_labels(self) -> None:
        """Every label produced by classify_strength has a color."""
        for label in ("strong", "medium", "weak"):
            color = strength_color(label)
            assert color in ("green", "yellow", "red")

    def test_pairs_with_classify_strength(self) -> None:
        """The output of classify_strength feeds directly into strength_color."""
        # A few representative coefficients
        for coefficient, expected_color in [
            (0.9, "green"),
            (-0.9, "green"),
            (0.5, "yellow"),
            (-0.5, "yellow"),
            (0.1, "red"),
            (-0.1, "red"),
        ]:
            label = classify_strength(coefficient)
            assert strength_color(label) == expected_color


# ============================================================
# PURE: direction_arrow (A1.3)
# ============================================================
class TestDirectionArrow:
    """Tests for direction_arrow()."""

    def test_positive_is_up_arrow(self) -> None:
        """'positive' maps to '↑'."""
        assert direction_arrow("positive") == "↑"

    def test_negative_is_down_arrow(self) -> None:
        """'negative' maps to '↓'."""
        assert direction_arrow("negative") == "↓"

    def test_unknown_label_raises(self) -> None:
        """An unknown label raises ValueError."""
        with pytest.raises(ValueError, match="Unknown direction label"):
            direction_arrow("neutral")

    def test_empty_string_raises(self) -> None:
        """An empty string raises ValueError."""
        with pytest.raises(ValueError, match="Unknown direction label"):
            direction_arrow("")

    def test_case_sensitive(self) -> None:
        """Labels are case-sensitive — 'Positive' is not 'positive'."""
        with pytest.raises(ValueError, match="Unknown direction label"):
            direction_arrow("Positive")

    def test_covers_all_direction_labels(self) -> None:
        """Every label produced by classify_direction has an arrow."""
        for label in ("positive", "negative"):
            arrow = direction_arrow(label)
            assert arrow in ("↑", "↓")

    def test_pairs_with_classify_direction(self) -> None:
        """The output of classify_direction feeds directly into direction_arrow."""
        assert direction_arrow(classify_direction(0.5)) == "↑"
        assert direction_arrow(classify_direction(-0.5)) == "↓"
        assert direction_arrow(classify_direction(0.0)) == "↑"


# ============================================================
# PURE: resample_btc_to_daily
# ============================================================
class TestResampleBtcToDaily:
    """Tests for resample_btc_to_daily()."""

    def test_empty_frame(self) -> None:
        """Empty input → empty output with expected columns."""
        result = resample_btc_to_daily(pd.DataFrame())
        assert result.empty
        assert list(result.columns) == ["date", "close"]

    def test_none_input(self) -> None:
        """None input → empty output."""
        result = resample_btc_to_daily(None)
        assert result.empty

    def test_missing_columns(self) -> None:
        """Frame without time/close → empty output."""
        df = pd.DataFrame({"foo": [1, 2, 3]})
        result = resample_btc_to_daily(df)
        assert result.empty

    def test_single_day(self) -> None:
        """A single day of hourly data → one daily row (last close)."""
        day = datetime(2026, 9, 1, tzinfo=timezone.utc)
        df = pd.DataFrame(
            {
                "time": [day + timedelta(hours=h) for h in range(24)],
                "close": [100.0 + h for h in range(24)],
            }
        )
        result = resample_btc_to_daily(df)
        assert len(result) == 1
        assert result.iloc[0]["date"] == date(2026, 9, 1)
        assert result.iloc[0]["close"] == 123.0

    def test_multiple_days(self) -> None:
        """Multiple days → one row per day."""
        start = datetime(2026, 9, 1, tzinfo=timezone.utc)
        df = pd.DataFrame(
            {
                "time": [start + timedelta(hours=h) for h in range(72)],
                "close": [100.0 + h for h in range(72)],
            }
        )
        result = resample_btc_to_daily(df)
        assert len(result) == 3
        assert list(result["date"]) == [
            date(2026, 9, 1),
            date(2026, 9, 2),
            date(2026, 9, 3),
        ]
        # Last close of each day
        assert result.iloc[0]["close"] == 123.0
        assert result.iloc[1]["close"] == 147.0
        assert result.iloc[2]["close"] == 171.0

    def test_accepts_ds_and_y_columns(self) -> None:
        """The function accepts the training-frame naming (ds, y)."""
        day = datetime(2026, 9, 1, tzinfo=timezone.utc)
        df = pd.DataFrame(
            {
                "ds": [day + timedelta(hours=h) for h in range(24)],
                "y": [100.0 + h for h in range(24)],
            }
        )
        result = resample_btc_to_daily(df)
        assert len(result) == 1
        assert result.iloc[0]["close"] == 123.0

    def test_sorted_ascending(self) -> None:
        """Output is sorted by date ascending even for unordered input."""
        start = datetime(2026, 9, 1, tzinfo=timezone.utc)
        # Build hourly rows but shuffle them
        rows = [
            {
                "time": start + timedelta(hours=h),
                "close": 100.0 + h,
            }
            for h in range(48)
        ]
        df = pd.DataFrame(rows).sample(frac=1, random_state=42)
        result = resample_btc_to_daily(df)
        assert list(result["date"]) == sorted(result["date"])


# ============================================================
# RESULT DATACLASS
# ============================================================
class TestCalculationResult:
    """Tests for the CalculationResult dataclass."""

    def test_defaults(self) -> None:
        """Freshly constructed result has zero counters and empty lists."""
        now = datetime.now(timezone.utc)
        result = CalculationResult(calculated_at=now)
        assert result.calculated_at == now
        assert result.rows_built == 0
        assert result.rows_written == 0
        assert result.skipped == []
        assert result.errors == []
        assert result.elapsed_seconds == 0.0

    def test_to_dict(self) -> None:
        """to_dict returns the expected keys."""
        now = datetime.now(timezone.utc)
        result = CalculationResult(
            calculated_at=now,
            rows_built=3,
            rows_written=3,
            skipped=[{"indicator": "gdp", "window_days": 30, "reason": "x"}],
            errors=[],
            elapsed_seconds=0.5,
        )
        d = result.to_dict()
        assert set(d.keys()) == {
            "calculated_at",
            "rows_built",
            "rows_written",
            "skipped",
            "errors",
            "elapsed_seconds",
        }
        assert d["rows_built"] == 3
        assert d["calculated_at"] == now.isoformat()

    def test_repr(self) -> None:
        """__repr__ returns a string with the counters."""
        result = CalculationResult(
            calculated_at=datetime.now(timezone.utc),
            rows_built=2,
            rows_written=2,
        )
        r = repr(result)
        assert "CalculationResult" in r
        assert "built=2" in r
        assert "written=2" in r


# ============================================================
# CALCULATOR — CONSTRUCTION
# ============================================================
class TestCalculatorConstruction:
    """Tests for CorrelationCalculator.__init__()."""

    def test_empty_windows_raises(self) -> None:
        """Empty windows tuple raises ValueError."""
        with pytest.raises(ValueError, match="windows must not be empty"):
            CorrelationCalculator(
                correlation_repo=None,
                prediction_repo=None,
                windows=(),
            )

    def test_non_positive_window_raises(self) -> None:
        """A non-positive window raises ValueError."""
        with pytest.raises(ValueError, match="must all be positive"):
            CorrelationCalculator(
                correlation_repo=None,
                prediction_repo=None,
                windows=(30, 0),
            )

    def test_default_windows(self) -> None:
        """Default windows is WINDOWS = (30, 90, 365)."""
        calc = CorrelationCalculator(
            correlation_repo=None,
            prediction_repo=None,
        )
        assert calc.windows == WINDOWS

    def test_repr(self) -> None:
        """__repr__ mentions the windows and indicator names."""
        calc = CorrelationCalculator(
            correlation_repo=None,
            prediction_repo=None,
        )
        r = repr(calc)
        assert "CorrelationCalculator" in r
        assert "windows=" in r
        assert "inflation" in r


# ============================================================
# CALCULATOR — run() HAPPY PATHS
# ============================================================
class TestCalculatorRunHappyPath:
    """Tests for run() on the happy path."""

    @pytest.mark.asyncio
    async def test_full_run_builds_and_persists_two_rows(self) -> None:
        """inflation and rates are computed; gdp and unemployment skipped.

        With a full BTC history and macro data present, only the two
        indicators with a configured source column produce rows. The
        two unconfigured indicators are skipped once per window.
        """
        btc = _hourly_btc_frame(days=400)
        macro = _daily_macro_frame(days=400)
        pred_repo = _mock_prediction_repo(btc, macro)
        corr_repo = _mock_correlation_repo(saved_count=6)

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        # 2 configured indicators × 3 windows = 6 rows
        assert result.rows_built == 6
        assert result.rows_written == 6

        # 2 unconfigured indicators × 3 windows = 6 skips
        skipped_indicators = {s["indicator"] for s in result.skipped}
        assert skipped_indicators == {"gdp", "unemployment"}
        assert len(result.skipped) == 6

        # save_rows was called once with 6 rows
        assert corr_repo.save_rows.call_count == 1
        saved_rows = corr_repo.save_rows.call_args.args[0]
        assert len(saved_rows) == 6

    @pytest.mark.asyncio
    async def test_rows_have_expected_fields(self) -> None:
        """Built rows have expected fields, shared calculated_at, None p_value."""
        btc = _hourly_btc_frame(days=400)
        macro = _daily_macro_frame(days=400)
        pred_repo = _mock_prediction_repo(btc, macro)
        corr_repo = _mock_correlation_repo(saved_count=6)

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        await calc.run()

        saved_rows = corr_repo.save_rows.call_args.args[0]
        calculated_ats = {row.calculated_at for row in saved_rows}
        assert len(calculated_ats) == 1  # all rows share one timestamp

        for row in saved_rows:
            assert row.indicator_name in ("inflation", "rates")
            assert row.window_days in (30, 90, 365)
            assert row.strength in ("strong", "medium", "weak")
            assert row.direction in ("positive", "negative")
            assert row.p_value is None
            assert -1.0 <= row.correlation_coefficient <= 1.0

    @pytest.mark.asyncio
    async def test_all_windows_are_attempted(self) -> None:
        """Every (indicator, window) pair appears in rows or skips."""
        btc = _hourly_btc_frame(days=400)
        macro = _daily_macro_frame(days=400)
        pred_repo = _mock_prediction_repo(btc, macro)
        corr_repo = _mock_correlation_repo(saved_count=6)

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        saved_rows = corr_repo.save_rows.call_args.args[0]
        built_keys = {
            (row.indicator_name, row.window_days) for row in saved_rows
        }
        skipped_keys = {
            (s["indicator"], s["window_days"]) for s in result.skipped
        }
        all_keys = built_keys | skipped_keys

        expected = {
            (ind, window)
            for ind in INDICATOR_SOURCE_COLUMNS.keys()
            for window in WINDOWS
        }
        assert all_keys == expected


# ============================================================
# CALCULATOR — run() SKIP PATHS
# ============================================================
class TestCalculatorRunSkipPaths:
    """Tests for run()'s skip conditions."""

    @pytest.mark.asyncio
    async def test_empty_btc_returns_no_rows(self) -> None:
        """Empty BTC frame → no rows built, no exception."""
        pred_repo = _mock_prediction_repo(
            btc_frame=pd.DataFrame(),
            macro_frame=_daily_macro_frame(days=400),
        )
        corr_repo = _mock_correlation_repo()

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        assert result.rows_built == 0
        assert result.rows_written == 0
        assert corr_repo.save_rows.call_count == 0

    @pytest.mark.asyncio
    async def test_empty_macro_skips_all_indicators(self) -> None:
        """Empty macro frame → all configured indicators skipped."""
        pred_repo = _mock_prediction_repo(
            btc_frame=_hourly_btc_frame(days=400),
            macro_frame=pd.DataFrame(),
        )
        corr_repo = _mock_correlation_repo()

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        # inflation + rates are configured, so they reach the
        # "no_macro_data" branch: 2 × 3 = 6 skips for those.
        # gdp + unemployment are skipped as unconfigured: 2 × 3 = 6.
        # Total 12 skips. No rows.
        assert result.rows_built == 0
        assert len(result.skipped) == 12

    @pytest.mark.asyncio
    async def test_insufficient_btc_history_skips_long_windows(self) -> None:
        """BTC history of 45 days → 30d works, 90d and 365d skip."""
        # Only 45 days of BTC, so 30d can be computed (needs 30),
        # but 90d and 365d cannot.
        pred_repo = _mock_prediction_repo(
            btc_frame=_hourly_btc_frame(days=45),
            macro_frame=_daily_macro_frame(days=45),
        )
        corr_repo = _mock_correlation_repo(saved_count=2)

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        saved_rows = corr_repo.save_rows.call_args.args[0]
        built_keys = {
            (row.indicator_name, row.window_days) for row in saved_rows
        }
        # Only the 30d window is buildable for the two configured indicators
        assert built_keys == {
            ("inflation", 30),
            ("rates", 30),
        }

        # 90d and 365d skipped for insufficient history
        skipped_reasons = {s["reason"] for s in result.skipped}
        assert "insufficient_btc_history" in skipped_reasons

    @pytest.mark.asyncio
    async def test_macro_column_missing_skips_indicator(self) -> None:
        """Macro frame missing a source column → that indicator skipped."""
        # Drop the interest_rate column from the macro frame.
        macro = _daily_macro_frame(days=400).drop(columns=["interest_rate"])
        pred_repo = _mock_prediction_repo(
            btc_frame=_hourly_btc_frame(days=400),
            macro_frame=macro,
        )
        corr_repo = _mock_correlation_repo(saved_count=3)

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        # Only inflation × 3 windows are built
        saved_rows = corr_repo.save_rows.call_args.args[0]
        built_keys = {
            (row.indicator_name, row.window_days) for row in saved_rows
        }
        assert built_keys == {
            ("inflation", 30),
            ("inflation", 90),
            ("inflation", 365),
        }

        # rates skipped with macro_column_missing
        reasons = {s["reason"] for s in result.skipped}
        assert any("macro_column_missing" in r for r in reasons)

    @pytest.mark.asyncio
    async def test_gdp_and_unemployment_skip_with_source_column_reason(
        self,
    ) -> None:
        """Unconfigured indicators skip with a specific reason string."""
        pred_repo = _mock_prediction_repo(
            btc_frame=_hourly_btc_frame(days=400),
            macro_frame=_daily_macro_frame(days=400),
        )
        corr_repo = _mock_correlation_repo()

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        # Find skips for gdp and unemployment
        for indicator in ("gdp", "unemployment"):
            reasons = [
                s["reason"]
                for s in result.skipped
                if s["indicator"] == indicator
            ]
            assert reasons
            assert all(
                r == "source_column_not_configured" for r in reasons
            ), f"unexpected reasons for {indicator}: {reasons}"


# ============================================================
# CALCULATOR — run() ERROR ISOLATION
# ============================================================
class TestCalculatorRunErrorIsolation:
    """Tests for run()'s per-pair error handling."""

    @pytest.mark.asyncio
    async def test_btc_fetch_failure_returns_empty_result(self) -> None:
        """BTC fetch raising does not propagate; result is empty."""
        pred_repo = _mock_prediction_repo(
            btc_raises=RuntimeError("DB down"),
            macro_frame=_daily_macro_frame(days=400),
        )
        corr_repo = _mock_correlation_repo()

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        assert result.rows_built == 0
        assert result.rows_written == 0

    @pytest.mark.asyncio
    async def test_macro_fetch_failure_returns_empty_result(self) -> None:
        """Macro fetch raising does not propagate; result is empty."""
        pred_repo = _mock_prediction_repo(
            btc_frame=_hourly_btc_frame(days=400),
            macro_raises=RuntimeError("DB down"),
        )
        corr_repo = _mock_correlation_repo()

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        assert result.rows_built == 0
        assert result.rows_written == 0

    @pytest.mark.asyncio
    async def test_save_failure_captured_in_errors(self) -> None:
        """save_rows raising is captured in errors; result still returned."""
        pred_repo = _mock_prediction_repo(
            btc_frame=_hourly_btc_frame(days=400),
            macro_frame=_daily_macro_frame(days=400),
        )
        corr_repo = MagicMock()
        corr_repo.save_rows = AsyncMock(
            side_effect=RuntimeError("insert failed")
        )

        calc = CorrelationCalculator(
            correlation_repo=corr_repo,
            prediction_repo=pred_repo,
        )
        result = await calc.run()

        # Rows were built in memory but the save failed
        assert result.rows_built == 6
        assert result.rows_written == 0
        assert len(result.errors) >= 1
        assert any("save_rows failed" in e["error"] for e in result.errors)


# ============================================================
# CALCULATOR — INTERNAL HELPERS
# ============================================================
class TestPrepareMacroDaily:
    """Tests for CorrelationCalculator._prepare_macro_daily()."""

    def test_empty_input(self) -> None:
        """Empty frame → empty output."""
        calc = CorrelationCalculator(None, None)
        result = calc._prepare_macro_daily(pd.DataFrame())
        assert result.empty

    def test_none_input(self) -> None:
        """None input → empty output."""
        calc = CorrelationCalculator(None, None)
        result = calc._prepare_macro_daily(None)
        assert result.empty

    def test_adds_date_column(self) -> None:
        """Output has a `date` column derived from `time`."""
        macro = _daily_macro_frame(days=5)
        calc = CorrelationCalculator(None, None)
        result = calc._prepare_macro_daily(macro)

        assert "date" in result.columns
        assert "time" not in result.columns
        assert len(result) == 5

    def test_dedups_on_date(self) -> None:
        """Multiple rows per date collapse to one (last value)."""
        now = datetime.now(timezone.utc)
        macro = pd.DataFrame(
            {
                "time": [now, now, now],
                "cpi": [3.0, 3.1, 3.2],
                "interest_rate": [4.0, 4.1, 4.2],
                "m2_growth": [2.0, 2.1, 2.2],
                "dxy": [100.0, 100.1, 100.2],
                "treasury_yield": [4.0, 4.1, 4.2],
            }
        )
        calc = CorrelationCalculator(None, None)
        result = calc._prepare_macro_daily(macro)

        assert len(result) == 1
        # .last() keeps the last row per date
        assert result.iloc[0]["cpi"] == 3.2


class TestComputeOne:
    """Direct tests for CorrelationCalculator._compute_one()."""

    def test_source_column_none_skips(self) -> None:
        """source_col=None → skip with source_column_not_configured."""
        calc = CorrelationCalculator(None, None)
        skipped: List[Dict[str, Any]] = []
        row = calc._compute_one(
            indicator="gdp",
            source_col=None,
            window_days=30,
            btc_daily=pd.DataFrame({"date": [], "close": []}),
            macro_daily=pd.DataFrame(),
            calculated_at=datetime.now(timezone.utc),
            skipped=skipped,
        )
        assert row is None
        assert len(skipped) == 1
        assert skipped[0]["reason"] == "source_column_not_configured"

    def test_insufficient_btc_skips(self) -> None:
        """Fewer BTC days than window → insufficient_btc_history."""
        calc = CorrelationCalculator(None, None)
        skipped: List[Dict[str, Any]] = []
        btc_daily = pd.DataFrame(
            {
                "date": [date(2026, 9, i) for i in range(1, 11)],
                "close": [100.0] * 10,
            }
        )
        macro_daily = pd.DataFrame(
            {
                "date": [date(2026, 9, i) for i in range(1, 11)],
                "cpi": [3.2] * 10,
            }
        )
        row = calc._compute_one(
            indicator="inflation",
            source_col="cpi",
            window_days=30,
            btc_daily=btc_daily,
            macro_daily=macro_daily,
            calculated_at=datetime.now(timezone.utc),
            skipped=skipped,
        )
        assert row is None
        assert skipped[0]["reason"] == "insufficient_btc_history"

    def test_no_macro_data_skips(self) -> None:
        """Empty macro frame → no_macro_data."""
        calc = CorrelationCalculator(None, None)
        skipped: List[Dict[str, Any]] = []
        btc_daily = pd.DataFrame(
            {
                "date": [
                    date(2026, 9, 1) + timedelta(days=i)
                    for i in range(31)
                ],
                "close": [float(i) for i in range(1, 32)],
            }
        )
        row = calc._compute_one(
            indicator="inflation",
            source_col="cpi",
            window_days=30,
            btc_daily=btc_daily,
            macro_daily=pd.DataFrame(),
            calculated_at=datetime.now(timezone.utc),
            skipped=skipped,
        )
        assert row is None
        assert skipped[0]["reason"] == "no_macro_data"

    def test_missing_macro_column_skips(self) -> None:
        """Macro frame without the source column → macro_column_missing."""
        calc = CorrelationCalculator(None, None)
        skipped: List[Dict[str, Any]] = []
        btc_daily = pd.DataFrame(
            {
                "date": [
                    date(2026, 9, 1) + timedelta(days=i)
                    for i in range(31)
                ],
                "close": [float(i) for i in range(1, 32)],
            }
        )
        macro_daily = pd.DataFrame(
            {
                "date": [
                    date(2026, 9, 1) + timedelta(days=i)
                    for i in range(31)
                ],
                # Note: no 'cpi' column
                "interest_rate": [4.5] * 31,
            }
        )
        row = calc._compute_one(
            indicator="inflation",
            source_col="cpi",
            window_days=30,
            btc_daily=btc_daily,
            macro_daily=macro_daily,
            calculated_at=datetime.now(timezone.utc),
            skipped=skipped,
        )
        assert row is None
        assert "macro_column_missing" in skipped[0]["reason"]

    def test_happy_path_returns_correlation_row(self) -> None:
        """A well-formed pair returns a CorrelationRow."""
        calc = CorrelationCalculator(None, None)
        skipped: List[Dict[str, Any]] = []
        n = 40
        btc_daily = pd.DataFrame(
            {
                "date": [date(2026, 9, 1) + timedelta(days=i) for i in range(n)],
                "close": [100.0 + i for i in range(n)],
            }
        )
        macro_daily = pd.DataFrame(
            {
                "date": [date(2026, 9, 1) + timedelta(days=i) for i in range(n)],
                "cpi": [3.0 + 0.01 * i for i in range(n)],
            }
        )
        calculated_at = datetime.now(timezone.utc)
        row = calc._compute_one(
            indicator="inflation",
            source_col="cpi",
            window_days=30,
            btc_daily=btc_daily,
            macro_daily=macro_daily,
            calculated_at=calculated_at,
            skipped=skipped,
        )
        assert row is not None
        assert row.indicator_name == "inflation"
        assert row.window_days == 30
        assert row.calculated_at == calculated_at
        assert -1.0 <= row.correlation_coefficient <= 1.0
        assert row.strength in ("strong", "medium", "weak")
        assert row.direction in ("positive", "negative")
        assert row.p_value is None
        assert skipped == []