"""Unit tests for the threshold checker.

Test organization:
    - TestThresholdCheckResult: dataclass behavior
    - TestNormalizeUsdToPct: USD → % conversion helper
    - TestCheckThresholds: main checker
    - TestFilterBreaches: breach filtering
    - TestThresholdConstants: module constants
    - TestStreakInfo: StreakInfo dataclass (T5.6)
    - TestStreakWarningResult: StreakWarningResult dataclass (T5.6)
    - TestEvaluateStreaks: evaluate_streaks() (T5.6)
    - TestConsecutiveDaysToMetricMap: row → metric map helper (T5.6)
"""

import logging
from typing import Any, Dict

import pytest

from app.ai.thresholds import (
    ALL_METRICS,
    DIRECTION_ABOVE,
    DIRECTION_BELOW,
    METRIC_DIRECTIONAL,
    METRIC_MAE_PCT,
    METRIC_MAPE,
    METRIC_RMSE_PCT,
    METRIC_UNIT_PERCENT,
    StreakInfo,
    StreakWarningResult,
    ThresholdCheckResult,
    check_thresholds,
    consecutive_days_to_metric_map,
    evaluate_streaks,
    filter_breaches,
    normalize_usd_to_pct,
)


# ============================================================
# DATACLASS TESTS
# ============================================================
class TestThresholdCheckResult:
    """Tests for the ThresholdCheckResult dataclass."""

    def test_construction(self) -> None:
        """Test constructing a result."""
        r = ThresholdCheckResult(
            metric=METRIC_MAE_PCT,
            metric_unit=METRIC_UNIT_PERCENT,
            value=12.5,
            threshold=10.0,
            breached=True,
            breach_direction=DIRECTION_ABOVE,
        )
        assert r.metric == METRIC_MAE_PCT
        assert r.breached is True

    def test_to_dict(self) -> None:
        """Test to_dict returns expected keys."""
        r = ThresholdCheckResult(
            metric=METRIC_MAE_PCT,
            metric_unit=METRIC_UNIT_PERCENT,
            value=12.5,
            threshold=10.0,
            breached=True,
            breach_direction=DIRECTION_ABOVE,
        )
        d = r.to_dict()
        expected = {
            "metric",
            "metric_unit",
            "value",
            "threshold",
            "breached",
            "breach_direction",
        }
        assert set(d.keys()) == expected

    def test_repr_breach(self) -> None:
        """Test __repr__ says BREACH when breached."""
        r = ThresholdCheckResult(
            metric=METRIC_MAE_PCT,
            metric_unit=METRIC_UNIT_PERCENT,
            value=12.5,
            threshold=10.0,
            breached=True,
            breach_direction=DIRECTION_ABOVE,
        )
        assert "BREACH" in repr(r)

    def test_repr_ok(self) -> None:
        """Test __repr__ says ok when not breached."""
        r = ThresholdCheckResult(
            metric=METRIC_MAE_PCT,
            metric_unit=METRIC_UNIT_PERCENT,
            value=5.0,
            threshold=10.0,
            breached=False,
            breach_direction=DIRECTION_ABOVE,
        )
        assert "ok" in repr(r)
        assert "BREACH" not in repr(r)


# ============================================================
# NORMALIZATION TESTS
# ============================================================
class TestNormalizeUsdToPct:
    """Tests for normalize_usd_to_pct()."""

    def test_simple_conversion(self) -> None:
        """Test 500 USD on 50000 mean → 1%."""
        assert normalize_usd_to_pct(500.0, 50_000.0) == pytest.approx(1.0)

    def test_zero_error(self) -> None:
        """Test zero error → 0%."""
        assert normalize_usd_to_pct(0.0, 50_000.0) == 0.0

    def test_large_error(self) -> None:
        """Test large error → high %."""
        assert normalize_usd_to_pct(5_000.0, 50_000.0) == pytest.approx(10.0)

    def test_none_usd_returns_none(self) -> None:
        """Test None USD returns None."""
        assert normalize_usd_to_pct(None, 50_000.0) is None

    def test_none_price_returns_none(self) -> None:
        """Test None mean price returns None."""
        assert normalize_usd_to_pct(500.0, None) is None

    def test_zero_price_returns_none(self) -> None:
        """Test zero mean price returns None (avoid div by zero)."""
        assert normalize_usd_to_pct(500.0, 0.0) is None

    def test_negative_price_returns_none(self) -> None:
        """Test negative mean price returns None."""
        assert normalize_usd_to_pct(500.0, -100.0) is None


# ============================================================
# CHECKER TESTS
# ============================================================
class TestCheckThresholds:
    """Tests for check_thresholds()."""

    # ---- Baseline behaviour ----

    def test_all_below_threshold(self) -> None:
        """Test metrics under all thresholds → no breaches."""
        results = check_thresholds(
            mae=100.0,
            rmse=150.0,
            mape=2.0,
            directional_accuracy=70.0,
            mean_actual_price=50_000.0,
        )
        assert all(not r.breached for r in results)

    def test_returns_one_result_per_provided_metric(self) -> None:
        """Test that every provided metric produces one result."""
        results = check_thresholds(
            mae=100.0,
            rmse=150.0,
            mape=2.0,
            directional_accuracy=70.0,
            mean_actual_price=50_000.0,
        )
        assert len(results) == 4
        metrics = {r.metric for r in results}
        assert metrics == {
            METRIC_MAE_PCT,
            METRIC_RMSE_PCT,
            METRIC_MAPE,
            METRIC_DIRECTIONAL,
        }

    # ---- MAE breaches ----

    def test_mae_above_threshold(self) -> None:
        """Test MAE > 10% triggers a breach."""
        # 6000 USD / 50000 mean = 12% > 10%
        results = check_thresholds(
            mae=6_000.0,
            rmse=None,
            mape=None,
            directional_accuracy=None,
            mean_actual_price=50_000.0,
        )
        mae_result = next(r for r in results if r.metric == METRIC_MAE_PCT)
        assert mae_result.breached is True
        assert mae_result.value == pytest.approx(12.0)
        assert mae_result.threshold == 10.0

    def test_mae_exactly_at_threshold_is_not_breached(self) -> None:
        """Test MAE == 10% is not a breach (strict >)."""
        results = check_thresholds(
            mae=5_000.0,  # exactly 10%
            rmse=None,
            mape=None,
            directional_accuracy=None,
            mean_actual_price=50_000.0,
        )
        mae_result = next(r for r in results if r.metric == METRIC_MAE_PCT)
        assert mae_result.breached is False

    # ---- RMSE breaches ----

    def test_rmse_above_threshold(self) -> None:
        """Test RMSE > 15% triggers a breach."""
        # 8000 USD / 50000 mean = 16% > 15%
        results = check_thresholds(
            mae=None,
            rmse=8_000.0,
            mape=None,
            directional_accuracy=None,
            mean_actual_price=50_000.0,
        )
        rmse_result = next(r for r in results if r.metric == METRIC_RMSE_PCT)
        assert rmse_result.breached is True
        assert rmse_result.value == pytest.approx(16.0)

    # ---- MAPE breaches ----

    def test_mape_above_threshold(self) -> None:
        """Test MAPE > 10% triggers a breach."""
        results = check_thresholds(
            mae=None,
            rmse=None,
            mape=12.5,
            directional_accuracy=None,
            mean_actual_price=None,
        )
        mape_result = next(r for r in results if r.metric == METRIC_MAPE)
        assert mape_result.breached is True

    def test_mape_does_not_need_mean_price(self) -> None:
        """Test MAPE can be checked without mean_actual_price."""
        results = check_thresholds(
            mae=None,
            rmse=None,
            mape=12.5,
            directional_accuracy=None,
            mean_actual_price=None,
        )
        assert len(results) == 1
        assert results[0].metric == METRIC_MAPE

    # ---- Directional accuracy breaches ----

    def test_directional_below_threshold(self) -> None:
        """Test directional accuracy < 55% triggers a breach."""
        results = check_thresholds(
            mae=None,
            rmse=None,
            mape=None,
            directional_accuracy=50.0,
            mean_actual_price=None,
        )
        dir_result = next(
            r for r in results if r.metric == METRIC_DIRECTIONAL
        )
        assert dir_result.breached is True
        assert dir_result.breach_direction == DIRECTION_BELOW

    def test_directional_above_threshold(self) -> None:
        """Test directional accuracy >= 55% is not a breach."""
        results = check_thresholds(
            mae=None,
            rmse=None,
            mape=None,
            directional_accuracy=60.0,
            mean_actual_price=None,
        )
        dir_result = next(
            r for r in results if r.metric == METRIC_DIRECTIONAL
        )
        assert dir_result.breached is False

    # ---- Skipping metrics ----

    def test_mae_skipped_without_mean_price(self) -> None:
        """Test MAE check is skipped when mean_actual_price is None."""
        results = check_thresholds(
            mae=6_000.0,
            rmse=None,
            mape=None,
            directional_accuracy=None,
            mean_actual_price=None,
        )
        assert len(results) == 0

    def test_none_metrics_are_skipped(self) -> None:
        """Test None metrics produce no result entries."""
        results = check_thresholds(
            mae=None,
            rmse=None,
            mape=None,
            directional_accuracy=None,
            mean_actual_price=50_000.0,
        )
        assert results == []

    # ---- Custom thresholds ----

    def test_custom_thresholds_override(self) -> None:
        """Test passing custom thresholds changes the checks."""
        results = check_thresholds(
            mae=3_000.0,  # 6% of 50000
            rmse=None,
            mape=None,
            directional_accuracy=None,
            mean_actual_price=50_000.0,
            thresholds={
                METRIC_MAE_PCT: 5.0,  # tighter than default
                METRIC_RMSE_PCT: 15.0,
                METRIC_MAPE: 10.0,
                METRIC_DIRECTIONAL: 55.0,
            },
        )
        mae_result = next(r for r in results if r.metric == METRIC_MAE_PCT)
        assert mae_result.breached is True
        assert mae_result.threshold == 5.0

    # ---- Realistic scenario ----

    def test_realistic_degraded_model(self) -> None:
        """Test a realistic scenario where everything breaches."""
        results = check_thresholds(
            mae=7_000.0,          # 14% > 10%
            rmse=9_000.0,         # 18% > 15%
            mape=12.0,            # > 10%
            directional_accuracy=48.0,  # < 55%
            mean_actual_price=50_000.0,
        )
        assert len(results) == 4
        assert all(r.breached for r in results)


# ============================================================
# FILTER TESTS
# ============================================================
class TestFilterBreaches:
    """Tests for filter_breaches()."""

    def test_filters_only_breaches(self) -> None:
        """Test that only breached results survive."""
        results = [
            ThresholdCheckResult(
                metric=METRIC_MAE_PCT,
                metric_unit=METRIC_UNIT_PERCENT,
                value=12.0,
                threshold=10.0,
                breached=True,
                breach_direction=DIRECTION_ABOVE,
            ),
            ThresholdCheckResult(
                metric=METRIC_MAPE,
                metric_unit=METRIC_UNIT_PERCENT,
                value=5.0,
                threshold=10.0,
                breached=False,
                breach_direction=DIRECTION_ABOVE,
            ),
        ]
        filtered = filter_breaches(results)
        assert len(filtered) == 1
        assert filtered[0].metric == METRIC_MAE_PCT

    def test_empty_list_returns_empty(self) -> None:
        """Test that filtering an empty list returns empty."""
        assert filter_breaches([]) == []

    def test_no_breaches_returns_empty(self) -> None:
        """Test that a list with no breaches returns empty."""
        results = [
            ThresholdCheckResult(
                metric=METRIC_MAPE,
                metric_unit=METRIC_UNIT_PERCENT,
                value=5.0,
                threshold=10.0,
                breached=False,
                breach_direction=DIRECTION_ABOVE,
            ),
        ]
        assert filter_breaches(results) == []


# ============================================================
# CONSTANTS
# ============================================================
class TestThresholdConstants:
    """Tests for module constants."""

    def test_all_metrics(self) -> None:
        """Test ALL_METRICS contains the four identifiers."""
        assert set(ALL_METRICS) == {
            "mae_pct",
            "rmse_pct",
            "mape",
            "directional_accuracy",
        }

    def test_metric_identifiers(self) -> None:
        """Test the individual metric constants."""
        assert METRIC_MAE_PCT == "mae_pct"
        assert METRIC_RMSE_PCT == "rmse_pct"
        assert METRIC_MAPE == "mape"
        assert METRIC_DIRECTIONAL == "directional_accuracy"

    def test_metric_unit(self) -> None:
        """Test METRIC_UNIT_PERCENT."""
        assert METRIC_UNIT_PERCENT == "percent"

    def test_directions(self) -> None:
        """Test the direction constants."""
        assert DIRECTION_ABOVE == "above"
        assert DIRECTION_BELOW == "below"


# ============================================================
# STREAK INFO (T5.6)
# ============================================================
class TestStreakInfo:
    """Tests for the StreakInfo dataclass."""

    def test_construction(self) -> None:
        """Test constructing a StreakInfo."""
        info = StreakInfo(
            metric=METRIC_MAE_PCT,
            consecutive_days=3,
            warning=True,
        )
        assert info.metric == METRIC_MAE_PCT
        assert info.consecutive_days == 3
        assert info.warning is True

    def test_defaults(self) -> None:
        """Test defaults: 0 days, no warning."""
        info = StreakInfo(metric=METRIC_MAE_PCT)
        assert info.consecutive_days == 0
        assert info.warning is False

    def test_to_dict(self) -> None:
        """Test to_dict returns the three expected keys."""
        info = StreakInfo(
            metric=METRIC_MAPE,
            consecutive_days=5,
            warning=True,
        )
        d = info.to_dict()
        assert d == {
            "metric": METRIC_MAPE,
            "consecutive_days": 5,
            "warning": True,
        }

    def test_repr_contains_metric(self) -> None:
        """Test __repr__ mentions the metric."""
        info = StreakInfo(
            metric=METRIC_RMSE_PCT,
            consecutive_days=4,
            warning=True,
        )
        assert METRIC_RMSE_PCT in repr(info)

    def test_repr_warning_status(self) -> None:
        """Test __repr__ says WARNING when warning is True."""
        info = StreakInfo(
            metric=METRIC_MAE_PCT,
            consecutive_days=3,
            warning=True,
        )
        assert "WARNING" in repr(info)

    def test_repr_ok_status(self) -> None:
        """Test __repr__ says ok when warning is False."""
        info = StreakInfo(
            metric=METRIC_MAE_PCT,
            consecutive_days=1,
            warning=False,
        )
        assert "ok" in repr(info)
        assert "WARNING" not in repr(info)


# ============================================================
# STREAK WARNING RESULT (T5.6)
# ============================================================
class TestStreakWarningResult:
    """Tests for the StreakWarningResult dataclass.

    Note: `any_warning` and `warning_count` are stored fields, not
    computed properties. `evaluate_streaks()` is what populates
    them. Direct construction requires passing them explicitly.
    """

    def test_defaults(self) -> None:
        """Test the default-constructed result is empty and healthy."""
        result = StreakWarningResult()
        assert result.streaks == {}
        assert result.any_warning is False
        assert result.warning_count == 0
        assert result.warning_threshold == 3

    def test_any_warning_true(self) -> None:
        """Test any_warning reflects the stored field."""
        result = StreakWarningResult(
            streaks={
                METRIC_MAE_PCT: StreakInfo(
                    METRIC_MAE_PCT, 3, True
                ),
                METRIC_MAPE: StreakInfo(METRIC_MAPE, 1, False),
            },
            any_warning=True,
            warning_count=1,
            warning_threshold=3,
        )
        assert result.any_warning is True
        assert result.warning_count == 1

    def test_to_dict_nests_per_metric(self) -> None:
        """Test to_dict nests per-metric dicts."""
        result = StreakWarningResult(
            streaks={
                METRIC_MAE_PCT: StreakInfo(
                    METRIC_MAE_PCT, 3, True
                )
            },
            any_warning=True,
            warning_count=1,
            warning_threshold=3,
        )
        d = result.to_dict()
        assert "streaks" in d
        assert "any_warning" in d
        assert "warning_count" in d
        assert "warning_threshold" in d
        assert d["warning_count"] == 1
        assert d["any_warning"] is True
        assert d["warning_threshold"] == 3
        assert d["streaks"][METRIC_MAE_PCT]["consecutive_days"] == 3

    def test_repr_returns_string(self) -> None:
        """Test __repr__ returns a string."""
        result = StreakWarningResult()
        assert isinstance(repr(result), str)

    def test_repr_warning_status(self) -> None:
        """Test __repr__ says WARNING when any_warning is True."""
        result = StreakWarningResult(
            any_warning=True, warning_count=1
        )
        assert "WARNING" in repr(result)

    def test_repr_ok_status(self) -> None:
        """Test __repr__ says ok when no warning is active."""
        result = StreakWarningResult()
        assert "ok" in repr(result)


# ============================================================
# EVALUATE STREAKS (T5.6)
# ============================================================
class TestEvaluateStreaks:
    """Tests for evaluate_streaks()."""

    def test_empty_map_seeds_all_metrics(self) -> None:
        """Test empty input still produces one StreakInfo per known metric.

        `evaluate_streaks()` seeds every metric in ALL_METRICS with
        consecutive_days=0 so the API response shape is stable —
        every metric key is always present.
        """
        result = evaluate_streaks({})
        assert set(result.streaks.keys()) == set(ALL_METRICS)
        assert all(
            info.consecutive_days == 0
            for info in result.streaks.values()
        )
        assert result.any_warning is False
        assert result.warning_count == 0

    def test_below_threshold_no_warning(self) -> None:
        """Test streak of 2 with default threshold 3 → no warning."""
        result = evaluate_streaks({METRIC_MAE_PCT: 2})
        assert result.any_warning is False
        assert result.warning_count == 0
        assert result.streaks[METRIC_MAE_PCT].warning is False
        assert result.streaks[METRIC_MAE_PCT].consecutive_days == 2

    def test_exactly_at_threshold_warns(self) -> None:
        """Test streak of exactly 3 → warning (>= semantics)."""
        result = evaluate_streaks({METRIC_MAE_PCT: 3})
        assert result.any_warning is True
        assert result.warning_count == 1
        assert result.streaks[METRIC_MAE_PCT].warning is True

    def test_above_threshold_warns(self) -> None:
        """Test streak of 5 → warning."""
        result = evaluate_streaks({METRIC_MAE_PCT: 5})
        assert result.any_warning is True
        assert result.streaks[METRIC_MAE_PCT].consecutive_days == 5

    def test_multiple_metrics_partial(self) -> None:
        """Test one metric warns, another does not."""
        result = evaluate_streaks({METRIC_MAE_PCT: 3, METRIC_MAPE: 1})
        assert result.any_warning is True
        assert result.warning_count == 1
        assert result.streaks[METRIC_MAE_PCT].warning is True
        assert result.streaks[METRIC_MAPE].warning is False

    def test_multiple_warned_metrics(self) -> None:
        """Test two metrics warn → warning_count == 2."""
        result = evaluate_streaks(
            {METRIC_MAE_PCT: 3, METRIC_RMSE_PCT: 5}
        )
        assert result.any_warning is True
        assert result.warning_count == 2

    def test_custom_threshold(self) -> None:
        """Test a custom warning_threshold overrides the default."""
        result = evaluate_streaks(
            {METRIC_MAE_PCT: 2}, warning_threshold=2
        )
        assert result.any_warning is True
        assert result.warning_threshold == 2

    def test_custom_threshold_not_met(self) -> None:
        """Test a custom threshold of 5 not met by streak of 4."""
        result = evaluate_streaks(
            {METRIC_MAE_PCT: 4}, warning_threshold=5
        )
        assert result.any_warning is False

    def test_logs_warning_when_triggered(self, caplog) -> None:
        """Test a WARNING log is emitted when a streak triggers."""
        with caplog.at_level(logging.WARNING):
            evaluate_streaks({METRIC_MAE_PCT: 3})
        assert any(
            rec.levelno == logging.WARNING
            for rec in caplog.records
        )

    def test_zero_streak_no_warning(self) -> None:
        """Test a metric with 0 consecutive days produces no warning."""
        result = evaluate_streaks({METRIC_MAE_PCT: 0})
        assert result.any_warning is False
        assert result.streaks[METRIC_MAE_PCT].consecutive_days == 0

    def test_unknown_metric_ignored(self) -> None:
        """Test a metric not in ALL_METRICS does not appear."""
        result = evaluate_streaks({"unknown_metric": 99})
        assert "unknown_metric" not in result.streaks
        assert set(result.streaks.keys()) == set(ALL_METRICS)

    def test_warning_threshold_reflected_in_result(self) -> None:
        """Test the result carries the threshold used."""
        result = evaluate_streaks({}, warning_threshold=7)
        assert result.warning_threshold == 7


# ============================================================
# CONSECUTIVE DAYS MAP (T5.6)
# ============================================================
class TestConsecutiveDaysToMetricMap:
    """Tests for consecutive_days_to_metric_map()."""

    def test_empty_rows(self) -> None:
        """Test empty input → empty dict."""
        assert consecutive_days_to_metric_map([]) == {}

    def test_single_row(self) -> None:
        """Test one row maps metric → consecutive_days."""
        rows = [{"metric": METRIC_MAE_PCT, "consecutive_days": 3}]
        assert consecutive_days_to_metric_map(rows) == {
            METRIC_MAE_PCT: 3
        }

    def test_duplicate_metric_takes_max(self) -> None:
        """Test duplicate metric keys keep the max consecutive_days."""
        rows = [
            {"metric": METRIC_MAE_PCT, "consecutive_days": 2},
            {"metric": METRIC_MAE_PCT, "consecutive_days": 5},
        ]
        assert consecutive_days_to_metric_map(rows) == {
            METRIC_MAE_PCT: 5
        }

    def test_zero_consecutive_days_skipped(self) -> None:
        """Test rows with consecutive_days=0 are skipped entirely."""
        rows = [{"metric": METRIC_MAE_PCT, "consecutive_days": 0}]
        assert consecutive_days_to_metric_map(rows) == {}

    def test_missing_consecutive_days_skipped(self) -> None:
        """Test rows without consecutive_days are skipped.

        `consecutive_days_to_metric_map` treats a missing value as 0
        and skips it, so no key appears for the metric.
        """
        rows = [{"metric": METRIC_MAE_PCT}]
        assert consecutive_days_to_metric_map(rows) == {}

    def test_none_metric_skipped(self) -> None:
        """Test rows with metric=None are skipped."""
        rows = [{"metric": None, "consecutive_days": 3}]
        assert consecutive_days_to_metric_map(rows) == {}

    def test_multiple_metrics(self) -> None:
        """Test multiple distinct metrics all appear."""
        rows = [
            {"metric": METRIC_MAE_PCT, "consecutive_days": 3},
            {"metric": METRIC_RMSE_PCT, "consecutive_days": 2},
        ]
        assert consecutive_days_to_metric_map(rows) == {
            METRIC_MAE_PCT: 3,
            METRIC_RMSE_PCT: 2,
        }

    def test_mixed_zero_and_positive(self) -> None:
        """Test only the positive streaks survive."""
        rows = [
            {"metric": METRIC_MAE_PCT, "consecutive_days": 0},
            {"metric": METRIC_RMSE_PCT, "consecutive_days": 4},
        ]
        assert consecutive_days_to_metric_map(rows) == {
            METRIC_RMSE_PCT: 4
        }