"""Unit tests for the threshold checker.

Test organization:
    - TestThresholdCheckResult: dataclass behavior
    - TestNormalizeUsdToPct: USD → % conversion helper
    - TestCheckThresholds: main checker
    - TestFilterBreaches: breach filtering
    - TestThresholdConstants: module constants
"""

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
    ThresholdCheckResult,
    check_thresholds,
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