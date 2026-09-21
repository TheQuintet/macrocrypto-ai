"""Unit tests for market condition classification.

Test organization:
    - TestCumulativeReturnPct: cumulative return helper
    - TestReturnVolatilityPct: volatility helper
    - TestClassifyMarketCondition: the classifier
    - TestClassifyMarketConditionSafe: exception-swallowing wrapper
    - TestMarketConstants: module constants
"""

import pytest

from app.prediction.market import (
    ALL_CONDITIONS,
    CONDITION_BEAR,
    CONDITION_BULL,
    CONDITION_NEUTRAL,
    CONDITION_PRIORITY,
    CONDITION_VOLATILE,
    classify_market_condition,
    classify_market_condition_safe,
    cumulative_return_pct,
    return_volatility_pct,
)


# ============================================================
# CUMULATIVE RETURN
# ============================================================
class TestCumulativeReturnPct:
    """Tests for cumulative_return_pct()."""

    def test_positive_return(self) -> None:
        """Test a simple positive return."""
        assert cumulative_return_pct([100.0, 110.0]) == pytest.approx(10.0)

    def test_negative_return(self) -> None:
        """Test a simple negative return."""
        assert cumulative_return_pct([100.0, 90.0]) == pytest.approx(-10.0)

    def test_zero_return(self) -> None:
        """Test an unchanged price."""
        assert cumulative_return_pct([100.0, 100.0]) == 0.0

    def test_large_return(self) -> None:
        """Test a 100% return."""
        assert cumulative_return_pct([100.0, 200.0]) == pytest.approx(100.0)

    def test_multi_point_uses_first_and_last(self) -> None:
        """Test that the return is end-vs-start, ignoring middle values."""
        assert cumulative_return_pct(
            [100.0, 200.0, 50.0, 130.0]
        ) == pytest.approx(30.0)

    def test_none_returns_none(self) -> None:
        """Test that None returns None."""
        assert cumulative_return_pct(None) is None  # type: ignore[arg-type]

    def test_empty_returns_none(self) -> None:
        """Test that an empty sequence returns None."""
        assert cumulative_return_pct([]) is None

    def test_single_point_returns_none(self) -> None:
        """Test that a single price returns None."""
        assert cumulative_return_pct([100.0]) is None

    def test_zero_start_returns_none(self) -> None:
        """Test that a zero starting price returns None."""
        assert cumulative_return_pct([0.0, 100.0]) is None

    def test_negative_start_returns_none(self) -> None:
        """Test that a negative starting price returns None."""
        assert cumulative_return_pct([-10.0, 100.0]) is None


# ============================================================
# VOLATILITY
# ============================================================
class TestReturnVolatilityPct:
    """Tests for return_volatility_pct()."""

    def test_constant_returns_zero_volatility(self) -> None:
        """Test that identical prices give zero volatility."""
        # pct_change of [100, 100, 100] = [0, 0] → std = 0
        assert return_volatility_pct([100.0, 100.0, 100.0]) == 0.0

    def test_smooth_growth_low_volatility(self) -> None:
        """Test that smooth growth has low volatility."""
        # Returns are all 10% → std = 0
        assert return_volatility_pct([100.0, 110.0, 121.0]) == 0.0

    def test_high_volatility(self) -> None:
        """Test a volatile series produces a large std."""
        vol = return_volatility_pct(
            [100.0, 150.0, 75.0, 120.0, 60.0, 130.0]
        )
        assert vol is not None
        assert vol > 0.20  # 20%+ std

    def test_none_returns_none(self) -> None:
        """Test that None returns None."""
        assert return_volatility_pct(None) is None  # type: ignore[arg-type]

    def test_empty_returns_none(self) -> None:
        """Test that an empty sequence returns None."""
        assert return_volatility_pct([]) is None

    def test_two_points_returns_none(self) -> None:
        """Test that 2 points can't produce a meaningful std."""
        # pct_change gives 1 return → std would be undefined
        assert return_volatility_pct([100.0, 110.0]) is None

    def test_three_points_produces_std(self) -> None:
        """Test that 3 points produce a valid std."""
        vol = return_volatility_pct([100.0, 105.0, 100.0])
        assert vol is not None
        assert vol > 0.0

    def test_zero_price_returns_none(self) -> None:
        """Test that a zero price makes pct_change undefined."""
        assert return_volatility_pct([100.0, 0.0, 100.0]) is None

    def test_negative_price_returns_none(self) -> None:
        """Test that a negative price makes pct_change undefined."""
        assert return_volatility_pct([100.0, -50.0, 100.0]) is None


# ============================================================
# CLASSIFIER
# ============================================================
class TestClassifyMarketCondition:
    """Tests for classify_market_condition()."""

    # ---- Directional ----

    def test_bull_above_threshold(self) -> None:
        """Test a low-volatility rise is classified as bull.

        Uses a smooth 7-point climb so the per-step returns are
        similar (low std → doesn't trigger volatility). Cumulative
        return is +30%, above the 20% bull threshold.
        """
        prices = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0]
        assert classify_market_condition(prices) == CONDITION_BULL

    def test_bear_below_threshold(self) -> None:
        """Test a low-volatility fall is classified as bear.

        Uses a smooth 4-point decline so the per-step returns are
        similar (low std → doesn't trigger volatility). Cumulative
        return is -30%, below the -20% bear threshold.
        """
        prices = [130.0, 120.0, 110.0, 100.0]
        assert classify_market_condition(prices) == CONDITION_BEAR

    def test_neutral_within_threshold(self) -> None:
        """Test a small move is neutral."""
        assert classify_market_condition([100.0, 102.0, 101.0]) == CONDITION_NEUTRAL

    def test_exactly_at_bull_threshold_is_neutral(self) -> None:
        """Test that exactly +20% is neutral (strict inequality)."""
        assert classify_market_condition([100.0, 120.0]) == CONDITION_NEUTRAL

    def test_exactly_at_bear_threshold_is_neutral(self) -> None:
        """Test that exactly -20% is neutral (strict inequality)."""
        assert classify_market_condition([100.0, 80.0]) == CONDITION_NEUTRAL

    def test_slightly_above_bull_threshold_is_bull(self) -> None:
        """Test that +20.1% is bull."""
        assert classify_market_condition([100.0, 120.1]) == CONDITION_BULL

    def test_slightly_below_bear_threshold_is_bear(self) -> None:
        """Test that -20.1% is bear."""
        assert classify_market_condition([100.0, 79.9]) == CONDITION_BEAR

    # ---- Volatility priority ----

    def test_volatile_wins_over_bull(self) -> None:
        """Test that high volatility + bull direction → volatile."""
        # Huge swings with a net positive direction
        prices = [100.0, 200.0, 50.0, 250.0, 300.0]
        assert classify_market_condition(prices) == CONDITION_VOLATILE

    def test_volatile_wins_over_bear(self) -> None:
        """Test that high volatility + bear direction → volatile."""
        prices = [300.0, 100.0, 250.0, 50.0, 40.0]
        assert classify_market_condition(prices) == CONDITION_VOLATILE

    def test_volatile_wins_over_neutral(self) -> None:
        """Test that high volatility + small net move → volatile."""
        prices = [100.0, 150.0, 70.0, 130.0, 100.0]
        assert classify_market_condition(prices) == CONDITION_VOLATILE

    # ---- Insufficient data ----

    def test_empty_returns_none(self) -> None:
        """Test that an empty sequence returns None."""
        assert classify_market_condition([]) is None

    def test_single_point_returns_none(self) -> None:
        """Test that a single price returns None."""
        assert classify_market_condition([100.0]) is None

    def test_two_points_can_be_directional(self) -> None:
        """Test that 2 points can classify direction (no volatility)."""
        # 2 points have no returns, so volatility = None → falls
        # through to directional classification
        assert classify_market_condition([100.0, 130.0]) == CONDITION_BULL
        assert classify_market_condition([100.0, 70.0]) == CONDITION_BEAR
        assert classify_market_condition([100.0, 105.0]) == CONDITION_NEUTRAL

    # ---- Threshold overrides ----

    def test_custom_bull_threshold(self) -> None:
        """Test a custom bull threshold is honored."""
        # +10% with default threshold → neutral
        assert classify_market_condition([100.0, 110.0]) == CONDITION_NEUTRAL
        # +10% with a 5% threshold → bull
        assert (
            classify_market_condition(
                [100.0, 110.0], bull_threshold_pct=5.0
            )
            == CONDITION_BULL
        )

    def test_custom_bear_threshold(self) -> None:
        """Test a custom bear threshold is honored."""
        assert (
            classify_market_condition(
                [100.0, 90.0], bear_threshold_pct=5.0
            )
            == CONDITION_BEAR
        )

    def test_custom_volatility_threshold(self) -> None:
        """Test a custom volatility threshold is honored."""
        # Modest moves with a very tight threshold → volatile
        prices = [100.0, 103.0, 100.0, 103.0]
        assert (
            classify_market_condition(
                prices, volatility_threshold=0.005
            )
            == CONDITION_VOLATILE
        )
        # Same prices with a loose threshold → not volatile
        assert (
            classify_market_condition(
                prices, volatility_threshold=0.50
            )
            == CONDITION_NEUTRAL
        )

    # ---- Realistic scenarios ----

    def test_realistic_bull_run(self) -> None:
        """Test a realistic gradual bull run."""
        prices = [
            50_000.0, 51_000.0, 52_000.0, 53_000.0, 54_000.0,
            55_000.0, 56_000.0, 57_000.0, 58_000.0, 59_000.0,
            60_000.0, 61_000.0, 62_000.0, 63_000.0, 64_000.0,
        ]
        # +28% with small per-step moves
        assert classify_market_condition(prices) == CONDITION_BULL

    def test_realistic_bear_run(self) -> None:
        """Test a realistic gradual bear run."""
        prices = [100_000.0 - i * 2_000.0 for i in range(15)]
        assert classify_market_condition(prices) == CONDITION_BEAR

    def test_realistic_choppy_market(self) -> None:
        """Test a choppy market with high volatility."""
        prices = [
            50_000.0, 55_000.0, 48_000.0, 56_000.0, 47_000.0,
            57_000.0, 46_000.0, 58_000.0, 45_000.0, 59_000.0,
        ]
        assert classify_market_condition(prices) == CONDITION_VOLATILE

    def test_realistic_flat_market(self) -> None:
        """Test a flat market is neutral."""
        prices = [
            50_000.0, 50_100.0, 49_900.0, 50_050.0, 50_020.0,
            49_980.0, 50_010.0, 50_030.0, 49_990.0, 50_005.0,
        ]
        assert classify_market_condition(prices) == CONDITION_NEUTRAL


# ============================================================
# SAFE WRAPPER
# ============================================================
class TestClassifyMarketConditionSafe:
    """Tests for classify_market_condition_safe()."""

    def test_valid_input_delegates(self) -> None:
        """Test that valid input is passed through."""
        assert (
            classify_market_condition_safe([100.0, 130.0]) == CONDITION_BULL
        )

    def test_short_input_returns_none(self) -> None:
        """Test that too-short input returns None (no exception)."""
        assert classify_market_condition_safe([100.0]) is None

    def test_empty_returns_none(self) -> None:
        """Test that an empty list returns None."""
        assert classify_market_condition_safe([]) is None

    def test_bad_input_does_not_raise(self) -> None:
        """Test that non-numeric input is caught by the wrapper."""
        # The classifier might raise on non-numeric input; the safe
        # wrapper should swallow it.
        result = classify_market_condition_safe(["a", "b", "c"])  # type: ignore
        assert result is None


# ============================================================
# CONSTANTS
# ============================================================
class TestMarketConstants:
    """Tests for module constants."""

    def test_all_conditions(self) -> None:
        """Test that ALL_CONDITIONS has the four labels."""
        assert set(ALL_CONDITIONS) == {"bull", "bear", "volatile", "neutral"}

    def test_individual_constants(self) -> None:
        """Test the individual label constants."""
        assert CONDITION_BULL == "bull"
        assert CONDITION_BEAR == "bear"
        assert CONDITION_VOLATILE == "volatile"
        assert CONDITION_NEUTRAL == "neutral"

    def test_priority_order(self) -> None:
        """Test that volatile has the highest priority."""
        assert CONDITION_PRIORITY[0] == CONDITION_VOLATILE
        assert CONDITION_BULL in CONDITION_PRIORITY
        assert CONDITION_BEAR in CONDITION_PRIORITY
        assert CONDITION_NEUTRAL in CONDITION_PRIORITY