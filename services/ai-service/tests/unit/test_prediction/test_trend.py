"""Unit tests for the trend direction calculator.

Test organization:
    - TestCalculatePriceChangePct: percentage change helper
    - TestCalculateTrend: trend direction classification
    - TestCalculateTrendAndChange: combined helper
    - TestTrendConstants: module constants
"""

import pytest

from app.prediction.trend import (
    TREND_THRESHOLD_24H,
    TREND_THRESHOLD_7D,
    TREND_THRESHOLD_DEFAULT,
    TREND_THRESHOLDS,
    calculate_price_change_pct,
    calculate_trend,
    calculate_trend_and_change,
)
from app.schemas import TrendDirection


# ============================================================
# PERCENTAGE CHANGE TESTS
# ============================================================
class TestCalculatePriceChangePct:
    """Tests for calculate_price_change_pct()."""

    def test_positive_change(self) -> None:
        """Test a simple positive change."""
        assert calculate_price_change_pct(100.0, 101.0) == 1.0

    def test_negative_change(self) -> None:
        """Test a simple negative change."""
        assert calculate_price_change_pct(100.0, 99.0) == -1.0

    def test_zero_change(self) -> None:
        """Test that an unchanged price yields 0.0."""
        assert calculate_price_change_pct(100.0, 100.0) == 0.0

    def test_large_change(self) -> None:
        """Test a large change."""
        assert calculate_price_change_pct(100.0, 200.0) == 100.0

    def test_none_current_returns_none(self) -> None:
        """Test that None current price returns None."""
        assert calculate_price_change_pct(None, 100.0) is None

    def test_zero_current_returns_none(self) -> None:
        """Test that zero current price returns None (can't divide by zero)."""
        assert calculate_price_change_pct(0.0, 100.0) is None

    def test_negative_current_returns_none(self) -> None:
        """Test that negative current price returns None."""
        assert calculate_price_change_pct(-10.0, 100.0) is None

    def test_returns_float(self) -> None:
        """Test that the result is a float."""
        result = calculate_price_change_pct(100.0, 101.0)
        assert isinstance(result, float)

    def test_small_change(self) -> None:
        """Test a very small change."""
        assert calculate_price_change_pct(100.0, 100.1) == pytest.approx(0.1)


# ============================================================
# TREND CLASSIFICATION TESTS
# ============================================================
class TestCalculateTrend:
    """Tests for calculate_trend()."""

    # ---- 24h horizon (threshold 0.5%) ----

    def test_up_above_threshold_24h(self) -> None:
        """Test UP classification above 0.5% for 24h."""
        assert calculate_trend(100.0, 101.0, "24h") == TrendDirection.UP

    def test_down_below_threshold_24h(self) -> None:
        """Test DOWN classification below -0.5% for 24h."""
        assert calculate_trend(100.0, 99.0, "24h") == TrendDirection.DOWN

    def test_neutral_within_threshold_24h(self) -> None:
        """Test NEUTRAL for a small change within ±0.5% for 24h."""
        assert calculate_trend(100.0, 100.2, "24h") == TrendDirection.NEUTRAL

    def test_exactly_at_positive_threshold_is_neutral(self) -> None:
        """Test that exactly +0.5% is NEUTRAL (strict inequality)."""
        # 0.5% of 100 = 0.5, so 100.5
        assert calculate_trend(100.0, 100.5, "24h") == TrendDirection.NEUTRAL

    def test_exactly_at_negative_threshold_is_neutral(self) -> None:
        """Test that exactly -0.5% is NEUTRAL (strict inequality)."""
        assert calculate_trend(100.0, 99.5, "24h") == TrendDirection.NEUTRAL

    def test_just_above_positive_threshold_is_up(self) -> None:
        """Test that slightly above +0.5% is UP."""
        # 0.51% of 100 = 0.51
        assert calculate_trend(100.0, 100.51, "24h") == TrendDirection.UP

    def test_just_below_negative_threshold_is_down(self) -> None:
        """Test that slightly below -0.5% is DOWN."""
        assert calculate_trend(100.0, 99.49, "24h") == TrendDirection.DOWN

    # ---- 7d horizon (threshold 1.0%) ----

    def test_up_above_threshold_7d(self) -> None:
        """Test UP classification above 1.0% for 7d."""
        assert calculate_trend(100.0, 101.5, "7d") == TrendDirection.UP

    def test_down_below_threshold_7d(self) -> None:
        """Test DOWN classification below -1.0% for 7d."""
        assert calculate_trend(100.0, 98.5, "7d") == TrendDirection.DOWN

    def test_neutral_within_threshold_7d(self) -> None:
        """Test that +0.8% is NEUTRAL for 7d (above 24h threshold, below 7d)."""
        assert calculate_trend(100.0, 100.8, "7d") == TrendDirection.NEUTRAL

    def test_7d_neutral_but_24h_up(self) -> None:
        """Test that +0.8% is UP for 24h but NEUTRAL for 7d."""
        assert calculate_trend(100.0, 100.8, "24h") == TrendDirection.UP
        assert calculate_trend(100.0, 100.8, "7d") == TrendDirection.NEUTRAL

    # ---- Edge cases ----

    def test_none_current_returns_neutral(self) -> None:
        """Test that None current price returns NEUTRAL."""
        assert calculate_trend(None, 100.0, "24h") == TrendDirection.NEUTRAL

    def test_zero_current_returns_neutral(self) -> None:
        """Test that zero current price returns NEUTRAL."""
        assert calculate_trend(0.0, 100.0, "24h") == TrendDirection.NEUTRAL

    def test_unknown_horizon_uses_default(self) -> None:
        """Test that an unknown horizon falls back to the default threshold."""
        # 1.0% should be UP for the default (24h) threshold
        assert calculate_trend(100.0, 101.0, "bogus") == TrendDirection.UP

    def test_default_horizon_is_24h(self) -> None:
        """Test that the default horizon is 24h."""
        # Should match the explicit 24h call
        assert calculate_trend(100.0, 101.0) == calculate_trend(100.0, 101.0, "24h")


# ============================================================
# COMBINED HELPER TESTS
# ============================================================
class TestCalculateTrendAndChange:
    """Tests for calculate_trend_and_change()."""

    def test_returns_tuple(self) -> None:
        """Test that the function returns a (trend, change) tuple."""
        result = calculate_trend_and_change(100.0, 101.0, "24h")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_up_case(self) -> None:
        """Test a clear UP case."""
        trend, change = calculate_trend_and_change(100.0, 101.0, "24h")
        assert trend == TrendDirection.UP
        assert change == 1.0

    def test_down_case(self) -> None:
        """Test a clear DOWN case."""
        trend, change = calculate_trend_and_change(100.0, 99.0, "24h")
        assert trend == TrendDirection.DOWN
        assert change == -1.0

    def test_neutral_case(self) -> None:
        """Test a NEUTRAL case with a computed change."""
        trend, change = calculate_trend_and_change(100.0, 100.2, "24h")
        assert trend == TrendDirection.NEUTRAL
        assert change == pytest.approx(0.2)

    def test_none_current_returns_neutral_and_none(self) -> None:
        """Test that None current yields NEUTRAL and None change."""
        trend, change = calculate_trend_and_change(None, 100.0, "24h")
        assert trend == TrendDirection.NEUTRAL
        assert change is None

    def test_matches_individual_calls(self) -> None:
        """Test that the combined helper agrees with individual calls."""
        for current, predicted in [
            (100.0, 101.0),
            (100.0, 99.0),
            (100.0, 100.2),
            (None, 100.0),
            (0.0, 100.0),
        ]:
            combined_trend, combined_change = calculate_trend_and_change(
                current, predicted, "24h"
            )
            assert combined_trend == calculate_trend(current, predicted, "24h")
            assert combined_change == calculate_price_change_pct(
                current, predicted
            )


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestTrendConstants:
    """Tests for module constants."""

    def test_24h_threshold_is_0_5(self) -> None:
        """Test that the 24h threshold is 0.5."""
        assert TREND_THRESHOLD_24H == 0.5

    def test_7d_threshold_is_1_0(self) -> None:
        """Test that the 7d threshold is 1.0."""
        assert TREND_THRESHOLD_7D == 1.0

    def test_default_threshold(self) -> None:
        """Test that the default threshold equals the 24h threshold."""
        assert TREND_THRESHOLD_DEFAULT == TREND_THRESHOLD_24H

    def test_thresholds_map(self) -> None:
        """Test the TREND_THRESHOLDS map."""
        assert TREND_THRESHOLDS["24h"] == 0.5
        assert TREND_THRESHOLDS["7d"] == 1.0
        assert len(TREND_THRESHOLDS) == 2