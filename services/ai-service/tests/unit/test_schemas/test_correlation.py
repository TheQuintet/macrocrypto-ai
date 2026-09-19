"""Unit tests for app.schemas.correlation.

Covers:
    - CorrelationEntry: field shapes, defaults, serialization,
      the color and arrow fields populated from the calculator
      helpers, and the OpenAPI example.
    - CorrelationErrorResponse: shape and defaults.

No I/O — these tests only exercise the Pydantic models.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.correlation.calculator import (
    classify_direction,
    classify_strength,
    direction_arrow,
    strength_color,
)
from app.schemas.correlation import (
    CorrelationEntry,
    CorrelationErrorResponse,
)


# ============================================================
# HELPERS
# ============================================================
def _make_entry(**overrides) -> CorrelationEntry:
    """Build a valid CorrelationEntry with sensible defaults."""
    defaults = dict(
        indicator_name="inflation",
        window_days=90,
        correlation_coefficient=-0.42,
        strength="medium",
        strength_color="yellow",
        direction="negative",
        direction_arrow="↓",
        p_value=0.03,
        calculated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return CorrelationEntry(**defaults)


# ============================================================
# CorrelationEntry
# ============================================================
class TestCorrelationEntry:
    """Tests for the CorrelationEntry model."""

    def test_construction(self) -> None:
        """A fully populated entry constructs."""
        entry = _make_entry()
        assert entry.indicator_name == "inflation"
        assert entry.window_days == 90
        assert entry.correlation_coefficient == -0.42
        assert entry.strength == "medium"
        assert entry.strength_color == "yellow"
        assert entry.direction == "negative"
        assert entry.direction_arrow == "↓"
        assert entry.p_value == 0.03

    def test_p_value_default_is_none(self) -> None:
        """p_value defaults to None when omitted."""
        entry = CorrelationEntry(
            indicator_name="rates",
            window_days=30,
            correlation_coefficient=0.5,
            strength="medium",
            strength_color="yellow",
            direction="positive",
            direction_arrow="↑",
            calculated_at=datetime.now(timezone.utc),
        )
        assert entry.p_value is None

    def test_model_dump_keys(self) -> None:
        """model_dump returns every field."""
        entry = _make_entry()
        d = entry.model_dump()
        expected = {
            "indicator_name",
            "window_days",
            "correlation_coefficient",
            "strength",
            "strength_color",
            "direction",
            "direction_arrow",
            "p_value",
            "calculated_at",
        }
        assert set(d.keys()) == expected

    def test_model_dump_mode_json(self) -> None:
        """model_dump(mode='json') serializes the timestamp."""
        entry = _make_entry()
        d = entry.model_dump(mode="json")
        assert isinstance(d["calculated_at"], str)

    def test_all_valid_indicator_names(self) -> None:
        """Every indicator label the schema documents is accepted."""
        for name in ("inflation", "rates", "gdp", "unemployment"):
            entry = _make_entry(indicator_name=name)
            assert entry.indicator_name == name

    def test_all_valid_windows(self) -> None:
        """Every window the schema documents is accepted."""
        for window in (30, 90, 365):
            entry = _make_entry(window_days=window)
            assert entry.window_days == window

    def test_all_valid_strengths(self) -> None:
        """Every strength the schema documents is accepted."""
        for s in ("strong", "medium", "weak"):
            entry = _make_entry(strength=s)
            assert entry.strength == s

    def test_all_valid_colors(self) -> None:
        """Every color the schema documents is accepted."""
        for c in ("green", "yellow", "red"):
            entry = _make_entry(strength_color=c)
            assert entry.strength_color == c

    def test_all_valid_directions(self) -> None:
        """Every direction the schema documents is accepted."""
        for d in ("positive", "negative"):
            entry = _make_entry(direction=d)
            assert entry.direction == d

    def test_all_valid_arrows(self) -> None:
        """Every arrow the schema documents is accepted."""
        for arrow in ("↑", "↓"):
            entry = _make_entry(direction_arrow=arrow)
            assert entry.direction_arrow == arrow

    def test_missing_required_field_raises(self) -> None:
        """Omitting a required field raises ValidationError."""
        with pytest.raises(ValidationError):
            CorrelationEntry(  # type: ignore[call-arg]
                indicator_name="inflation",
                window_days=90,
                # correlation_coefficient missing
                strength="medium",
                strength_color="yellow",
                direction="negative",
                direction_arrow="↓",
                calculated_at=datetime.now(timezone.utc),
            )

    def test_integration_with_classifier_helpers(self) -> None:
        """The color and arrow fields can be populated from the helpers.

        This locks in the intended usage: the API layer (A1.6) will
        build a CorrelationEntry from a stored row by calling
        strength_color() and direction_arrow() on the stored labels.
        """
        coefficient = -0.85
        strength = classify_strength(coefficient)
        direction = classify_direction(coefficient)

        entry = CorrelationEntry(
            indicator_name="inflation",
            window_days=90,
            correlation_coefficient=coefficient,
            strength=strength,
            strength_color=strength_color(strength),
            direction=direction,
            direction_arrow=direction_arrow(direction),
            calculated_at=datetime.now(timezone.utc),
        )

        assert entry.strength == "strong"
        assert entry.strength_color == "green"
        assert entry.direction == "negative"
        assert entry.direction_arrow == "↓"

    def test_openapi_example_is_valid(self) -> None:
        """The embedded JSON example in model_config is a valid entry."""
        example = CorrelationEntry.model_config["json_schema_extra"][
            "examples"
        ][0]
        # Should construct without error
        entry = CorrelationEntry(**example)
        assert entry.indicator_name == "inflation"
        assert entry.strength_color == "yellow"
        assert entry.direction_arrow == "↓"


# ============================================================
# CorrelationErrorResponse
# ============================================================
class TestCorrelationErrorResponse:
    """Tests for the CorrelationErrorResponse model."""

    def test_construction(self) -> None:
        """A minimal error response constructs."""
        err = CorrelationErrorResponse(
            error="no_data",
            message="No correlation data available.",
        )
        assert err.error == "no_data"
        assert err.message == "No correlation data available."
        assert err.detail is None

    def test_detail_optional(self) -> None:
        """detail can be set explicitly."""
        err = CorrelationErrorResponse(
            error="invalid_window",
            message="Bad window.",
            detail="Must be one of 30, 90, 365.",
        )
        assert err.detail == "Must be one of 30, 90, 365."

    def test_model_dump_keys(self) -> None:
        """model_dump returns the three expected fields."""
        err = CorrelationErrorResponse(error="e", message="m")
        d = err.model_dump()
        assert set(d.keys()) == {"error", "message", "detail"}

    def test_missing_required_field_raises(self) -> None:
        """Omitting a required field raises ValidationError."""
        with pytest.raises(ValidationError):
            CorrelationErrorResponse(message="m")  # type: ignore[call-arg]