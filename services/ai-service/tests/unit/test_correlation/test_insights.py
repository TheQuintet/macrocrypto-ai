"""Unit tests for app.correlation.insights.

Covers:
    - generate_insight(): sentence shape for every direction ×
      strength combination, with and without a p-value
    - Confidence formatting: integers drop the decimal, non-integers
      keep one decimal
    - Invalid direction raises ValueError
    - Integration with the calculator's helper functions so the
      sentence is consistent with the entry's fields

Pure-function tests — no I/O, no mocks.
"""

from datetime import datetime, timezone
from typing import Optional

import pytest

from app.correlation.insights import (
    _direction_verb,
    _format_confidence,
    generate_insight,
)


# ============================================================
# Sentence shape
# ============================================================
class TestGenerateInsightSentence:
    """Tests for the sentence template."""

    def test_positive_direction_says_rises(self) -> None:
        """A positive direction produces the 'rises' verb."""
        sentence = generate_insight(
            indicator_name="inflation",
            coefficient=0.5,
            strength="medium",
            direction="positive",
            p_value=0.03,
        )
        assert "When inflation rises, BTC typically rises" in sentence

    def test_negative_direction_says_falls(self) -> None:
        """A negative direction produces the 'falls' verb."""
        sentence = generate_insight(
            indicator_name="inflation",
            coefficient=-0.5,
            strength="medium",
            direction="negative",
            p_value=0.03,
        )
        assert "When inflation rises, BTC typically falls" in sentence

    def test_contains_strength_label(self) -> None:
        """The sentence embeds the strength label."""
        sentence = generate_insight(
            "rates", 0.85, "strong", "positive", 0.001
        )
        assert "strong" in sentence

    def test_contains_direction_label(self) -> None:
        """The sentence embeds the direction label."""
        sentence = generate_insight(
            "rates", -0.85, "strong", "negative", 0.001
        )
        assert "negative" in sentence

    def test_contains_confidence_when_p_value_set(self) -> None:
        """A non-None p_value yields a confidence clause."""
        sentence = generate_insight(
            "inflation", -0.42, "medium", "negative", 0.03
        )
        # p=0.03 → 97.0 → formatted as "97"
        assert "97% confidence" in sentence

    def test_drops_confidence_when_p_value_none(self) -> None:
        """A None p_value omits the confidence clause."""
        sentence = generate_insight(
            "gdp", 0.15, "weak", "positive", None
        )
        assert "confidence" not in sentence
        # But the base sentence is still there
        assert "weak positive correlation" in sentence

    def test_ends_with_period(self) -> None:
        """The sentence ends with a period."""
        sentence = generate_insight(
            "inflation", -0.42, "medium", "negative", 0.03
        )
        assert sentence.endswith(".")


# ============================================================
# Every direction × strength combination
# ============================================================
class TestGenerateInsightCombinations:
    """Every direction × strength produces a well-formed sentence."""

    @pytest.mark.parametrize(
        "direction,verb",
        [("positive", "rises"), ("negative", "falls")],
    )
    @pytest.mark.parametrize(
        "strength", ["strong", "medium", "weak"]
    )
    def test_every_combination(
        self, direction: str, verb: str, strength: str
    ) -> None:
        """Each combination produces a valid sentence."""
        sentence = generate_insight(
            "inflation",
            -0.42 if direction == "negative" else 0.42,
            strength,
            direction,
            0.03,
        )
        assert "inflation" in sentence
        assert verb in sentence
        assert strength in sentence
        assert direction in sentence
        assert "confidence" in sentence


# ============================================================
# Confidence formatting
# ============================================================
class TestGenerateInsightConfidenceFormatting:
    """Tests for how the confidence value is rendered."""

    def test_confidence_99_is_integer(self) -> None:
        """p=0.01 → 99.0 → rendered as '99'."""
        sentence = generate_insight(
            "rates", 0.9, "strong", "positive", 0.01
        )
        assert "99% confidence" in sentence
        assert "99.0%" not in sentence

    def test_confidence_95_is_integer(self) -> None:
        """p=0.05 → 95.0 → rendered as '95'."""
        sentence = generate_insight(
            "rates", 0.5, "medium", "positive", 0.05
        )
        assert "95% confidence" in sentence

    def test_confidence_97_point_5_keeps_one_decimal(self) -> None:
        """p=0.025 → 97.5 → rendered as '97.5'."""
        sentence = generate_insight(
            "rates", 0.5, "medium", "positive", 0.025
        )
        assert "97.5% confidence" in sentence

    def test_confidence_99_point_9(self) -> None:
        """p=0.001 → 99.9 → rendered as '99.9'."""
        sentence = generate_insight(
            "rates", 0.85, "strong", "positive", 0.001
        )
        assert "99.9% confidence" in sentence


# ============================================================
# Direction raise
# ============================================================
class TestGenerateInsightRaise:
    """Tests for the ValueError on unknown direction."""

    def test_unknown_direction_raises(self) -> None:
        """An unknown direction label raises ValueError."""
        with pytest.raises(ValueError, match="Unknown direction label"):
            generate_insight(
                "inflation", 0.5, "medium", "neutral", 0.03
            )

    def test_empty_direction_raises(self) -> None:
        """An empty direction label raises ValueError."""
        with pytest.raises(ValueError, match="Unknown direction label"):
            generate_insight("inflation", 0.5, "medium", "", 0.03)


# ============================================================
# Internal helpers
# ============================================================
class TestDirectionVerb:
    """Tests for the internal _direction_verb helper."""

    def test_positive(self) -> None:
        assert _direction_verb("positive") == "rises"

    def test_negative(self) -> None:
        assert _direction_verb("negative") == "falls"

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown direction label"):
            _direction_verb("neutral")


class TestFormatConfidence:
    """Tests for the internal _format_confidence helper."""

    def test_none_returns_none(self) -> None:
        assert _format_confidence(None) is None

    def test_integer_drops_decimal(self) -> None:
        assert _format_confidence(97.0) == "97"

    def test_zero_integer_drops_decimal(self) -> None:
        assert _format_confidence(0.0) == "0"

    def test_hundred_integer_drops_decimal(self) -> None:
        assert _format_confidence(100.0) == "100"

    def test_non_integer_keeps_one_decimal(self) -> None:
        assert _format_confidence(97.34) == "97.3"

    def test_non_integer_rounds(self) -> None:
        assert _format_confidence(97.36) == "97.4"

    def test_ninety_nine_point_nine(self) -> None:
        assert _format_confidence(99.9) == "99.9"


# ============================================================
# Integration with the calculator's labels
# ============================================================
class TestGenerateInsightIntegration:
    """The insight is consistent with the labels the calculator produces."""

    def test_matches_classify_strength_output(self) -> None:
        """Feeding a coefficient through classify_strength yields a
        sentence whose strength matches."""
        from app.correlation.calculator import classify_strength

        coefficient = -0.85
        strength = classify_strength(coefficient)
        sentence = generate_insight(
            "inflation", coefficient, strength, "negative", 0.001
        )
        assert strength in sentence

    def test_matches_classify_direction_output(self) -> None:
        """Feeding a coefficient through classify_direction yields a
        sentence whose verb matches."""
        from app.correlation.calculator import classify_direction

        # Negative coefficient → direction "negative" → verb "falls"
        direction = classify_direction(-0.5)
        sentence = generate_insight(
            "inflation", -0.5, "medium", direction, 0.03
        )
        assert "falls" in sentence

    def test_confidence_matches_confidence_from_p_value(self) -> None:
        """The rendered confidence matches (1 - p_value) * 100."""
        from app.correlation.calculator import (
            confidence_from_p_value,
        )

        p_value = 0.03
        expected_confidence = confidence_from_p_value(p_value)  # 97.0
        sentence = generate_insight(
            "inflation", -0.42, "medium", "negative", p_value
        )
        # 97.0 is an integer → rendered as "97"
        assert f"{int(expected_confidence)}% confidence" in sentence