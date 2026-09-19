"""Unit tests for app.schemas.correlation.

Covers:
    - CorrelationEntry: field shapes, defaults, serialization,
      the color and arrow fields populated from the calculator
      helpers, the A1.4 significance and confidence fields, the
      history field, and the OpenAPI example.
    - CorrelationHistoryPoint: shape and defaults.
    - CorrelationResponse: envelope shape and defaults.
    - CorrelationErrorResponse: shape and defaults.

No I/O — these tests only exercise the Pydantic models.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.correlation.calculator import (
    classify_direction,
    classify_strength,
    confidence_from_p_value,
    derive_significance,
    direction_arrow,
    strength_color,
)
from app.schemas.correlation import (
    CorrelationEntry,
    CorrelationErrorResponse,
    CorrelationHistoryPoint,
    CorrelationResponse,
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
        is_significant=True,
        confidence_level=97.0,
        calculated_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return CorrelationEntry(**defaults)


def _make_history_point(**overrides) -> CorrelationHistoryPoint:
    """Build a valid CorrelationHistoryPoint with defaults."""
    defaults = dict(
        calculated_at=datetime.now(timezone.utc),
        correlation_coefficient=-0.40,
        strength="medium",
        strength_color="yellow",
        direction="negative",
        direction_arrow="↓",
        p_value=0.04,
        is_significant=True,
        confidence_level=96.0,
    )
    defaults.update(overrides)
    return CorrelationHistoryPoint(**defaults)


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
        assert entry.is_significant is True
        assert entry.confidence_level == 97.0
        assert entry.history == []

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

    def test_is_significant_default_is_false(self) -> None:
        """is_significant defaults to False when omitted."""
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
        assert entry.is_significant is False

    def test_confidence_level_default_is_none(self) -> None:
        """confidence_level defaults to None when omitted."""
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
        assert entry.confidence_level is None

    def test_history_default_is_empty_list(self) -> None:
        """history defaults to an empty list when omitted."""
        entry = _make_entry()
        assert entry.history == []

    def test_history_accepts_points(self) -> None:
        """history accepts a list of CorrelationHistoryPoint objects."""
        hp = _make_history_point()
        entry = _make_entry(history=[hp])
        assert len(entry.history) == 1
        assert entry.history[0].correlation_coefficient == -0.40

    def test_model_dump_keys(self) -> None:
        """model_dump returns every field, including history."""
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
            "is_significant",
            "confidence_level",
            "calculated_at",
            "history",
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
        """The color and arrow fields can be populated from the helpers."""
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

    def test_integration_with_significance_helpers(self) -> None:
        """The is_significant and confidence_level fields populate from A1.4 helpers."""
        p_value = 0.03
        entry = CorrelationEntry(
            indicator_name="inflation",
            window_days=90,
            correlation_coefficient=-0.42,
            strength="medium",
            strength_color="yellow",
            direction="negative",
            direction_arrow="↓",
            p_value=p_value,
            is_significant=derive_significance(p_value),
            confidence_level=confidence_from_p_value(p_value),
            calculated_at=datetime.now(timezone.utc),
        )

        assert entry.is_significant is True
        assert entry.confidence_level == pytest.approx(97.0)

    def test_integration_with_none_p_value(self) -> None:
        """When p_value is None, is_significant is False and confidence is None."""
        entry = CorrelationEntry(
            indicator_name="inflation",
            window_days=90,
            correlation_coefficient=-0.42,
            strength="medium",
            strength_color="yellow",
            direction="negative",
            direction_arrow="↓",
            p_value=None,
            is_significant=derive_significance(None),
            confidence_level=confidence_from_p_value(None),
            calculated_at=datetime.now(timezone.utc),
        )

        assert entry.is_significant is False
        assert entry.confidence_level is None

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
        assert entry.is_significant is True
        assert entry.confidence_level == pytest.approx(97.0)
        # The example includes a history point
        assert len(entry.history) == 1
        assert entry.history[0].is_significant is True


# ============================================================
# CorrelationHistoryPoint
# ============================================================
class TestCorrelationHistoryPoint:
    """Tests for the CorrelationHistoryPoint model."""

    def test_construction(self) -> None:
        """A fully populated point constructs."""
        hp = _make_history_point()
        assert hp.correlation_coefficient == -0.40
        assert hp.strength == "medium"
        assert hp.strength_color == "yellow"
        assert hp.direction == "negative"
        assert hp.direction_arrow == "↓"
        assert hp.is_significant is True
        assert hp.confidence_level == 96.0

    def test_has_no_identifier_fields(self) -> None:
        """History points do NOT carry indicator_name or window_days."""
        hp = _make_history_point()
        d = hp.model_dump()
        assert "indicator_name" not in d
        assert "window_days" not in d

    def test_model_dump_keys(self) -> None:
        """model_dump returns every field."""
        hp = _make_history_point()
        d = hp.model_dump()
        expected = {
            "calculated_at",
            "correlation_coefficient",
            "strength",
            "strength_color",
            "direction",
            "direction_arrow",
            "p_value",
            "is_significant",
            "confidence_level",
        }
        assert set(d.keys()) == expected

    def test_p_value_defaults_to_none(self) -> None:
        """p_value defaults to None when omitted."""
        hp = CorrelationHistoryPoint(
            calculated_at=datetime.now(timezone.utc),
            correlation_coefficient=0.3,
            strength="medium",
            strength_color="yellow",
            direction="positive",
            direction_arrow="↑",
        )
        assert hp.p_value is None
        assert hp.is_significant is False
        assert hp.confidence_level is None

    def test_missing_required_field_raises(self) -> None:
        """Omitting a required field raises ValidationError."""
        with pytest.raises(ValidationError):
            CorrelationHistoryPoint(  # type: ignore[call-arg]
                # calculated_at missing
                correlation_coefficient=0.3,
                strength="medium",
                strength_color="yellow",
                direction="positive",
                direction_arrow="↑",
            )


# ============================================================
# CorrelationResponse
# ============================================================
class TestCorrelationResponse:
    """Tests for the CorrelationResponse envelope."""

    def test_construction(self) -> None:
        """A fully populated response constructs."""
        resp = CorrelationResponse(
            window_days=90,
            generated_at=datetime.now(timezone.utc),
            entries=[_make_entry()],
        )
        assert resp.window_days == 90
        assert len(resp.entries) == 1

    def test_empty_entries_default(self) -> None:
        """entries defaults to an empty list when omitted."""
        resp = CorrelationResponse(
            window_days=30,
            generated_at=datetime.now(timezone.utc),
        )
        assert resp.entries == []

    def test_model_dump_keys(self) -> None:
        """model_dump returns the three expected keys."""
        resp = CorrelationResponse(
            window_days=90,
            generated_at=datetime.now(timezone.utc),
            entries=[],
        )
        d = resp.model_dump()
        assert set(d.keys()) == {
            "window_days",
            "generated_at",
            "entries",
        }

    def test_openapi_example_is_valid(self) -> None:
        """The embedded JSON example in model_config is valid."""
        example = CorrelationResponse.model_config["json_schema_extra"][
            "examples"
        ][0]
        resp = CorrelationResponse(**example)
        assert resp.window_days == 90
        assert len(resp.entries) == 1
        assert resp.entries[0].indicator_name == "inflation"


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