"""Unit tests for database validators.

Test organization:
    - TestValidatePredictionRow: single-row validation
    - TestValidatePredictionRows: batch validation
    - TestValidatorConstants: module constants
"""

from datetime import datetime, timezone

import pytest

from app.database.repositories.prediction_repository import PredictionRow
from app.database.validators import (
    VALID_CONFIDENCE_LEVELS,
    VALID_HORIZONS,
    validate_prediction_row,
    validate_prediction_rows,
)


# ============================================================
# HELPERS
# ============================================================
def _make_row(
    horizon: str = "24h",
    model_name: str = "prophet",
    confidence: float = 0.85,
    predicted_price: float = 50_000.0,
    lower_bound: float = 49_000.0,
    upper_bound: float = 51_000.0,
) -> PredictionRow:
    """Build a valid PredictionRow by default; override for tests."""
    now = datetime.now(timezone.utc)
    return PredictionRow(
        time=now,
        prediction_time=now,
        horizon=horizon,
        model_name=model_name,
        confidence=confidence,
        predicted_price=predicted_price,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )


# ============================================================
# SINGLE ROW TESTS
# ============================================================
class TestValidatePredictionRow:
    """Tests for validate_prediction_row()."""

    def test_valid_row_passes(self) -> None:
        """Test that a well-formed row passes validation."""
        validate_prediction_row(_make_row())

    def test_empty_model_name_fails(self) -> None:
        """Test that an empty model_name fails."""
        with pytest.raises(ValueError, match="model_name must be non-empty"):
            validate_prediction_row(_make_row(model_name=""))

    def test_whitespace_model_name_fails(self) -> None:
        """Test that a whitespace-only model_name fails."""
        with pytest.raises(ValueError, match="model_name must be non-empty"):
            validate_prediction_row(_make_row(model_name="   "))

    def test_invalid_horizon_fails(self) -> None:
        """Test that an invalid horizon fails."""
        with pytest.raises(ValueError, match="invalid horizon"):
            validate_prediction_row(_make_row(horizon="1h"))

    def test_24h_horizon_passes(self) -> None:
        """Test that '24h' is a valid horizon."""
        validate_prediction_row(_make_row(horizon="24h"))

    def test_7d_horizon_passes(self) -> None:
        """Test that '7d' is a valid horizon."""
        validate_prediction_row(_make_row(horizon="7d"))

    def test_invalid_confidence_fails(self) -> None:
        """Test that an invalid confidence fails."""
        with pytest.raises(ValueError, match="invalid confidence"):
            validate_prediction_row(_make_row(confidence=0.50))

    def test_all_valid_confidence_levels_pass(self) -> None:
        """Test all three valid confidence levels pass."""
        for level in (0.70, 0.85, 0.95):
            validate_prediction_row(_make_row(confidence=level))

    def test_lower_bound_greater_than_predicted_fails(self) -> None:
        """Test that lower > predicted fails."""
        with pytest.raises(ValueError, match="lower_bound"):
            validate_prediction_row(
                _make_row(lower_bound=51_000.0, predicted_price=50_000.0)
            )

    def test_predicted_greater_than_upper_fails(self) -> None:
        """Test that predicted > upper fails."""
        with pytest.raises(ValueError, match="upper_bound"):
            validate_prediction_row(
                _make_row(predicted_price=52_000.0, upper_bound=51_000.0)
            )

    def test_equal_bounds_pass(self) -> None:
        """Test that equal lower=predicted=upper passes."""
        validate_prediction_row(
            _make_row(
                predicted_price=50_000.0,
                lower_bound=50_000.0,
                upper_bound=50_000.0,
            )
        )

    def test_nan_predicted_price_fails(self) -> None:
        """Test that NaN predicted_price fails."""
        with pytest.raises(ValueError, match="predicted_price"):
            validate_prediction_row(_make_row(predicted_price=float("nan")))

    def test_infinite_lower_bound_fails(self) -> None:
        """Test that an infinite lower_bound fails."""
        with pytest.raises(ValueError, match="lower_bound"):
            validate_prediction_row(
                _make_row(lower_bound=float("-inf"))
            )

    def test_infinite_upper_bound_fails(self) -> None:
        """Test that an infinite upper_bound fails."""
        with pytest.raises(ValueError, match="upper_bound"):
            validate_prediction_row(
                _make_row(upper_bound=float("inf"))
            )

    def test_error_message_includes_index(self) -> None:
        """Test that error messages include the row index."""
        with pytest.raises(ValueError, match="Row 42"):
            validate_prediction_row(_make_row(horizon="bogus"), index=42)


# ============================================================
# BATCH TESTS
# ============================================================
class TestValidatePredictionRows:
    """Tests for validate_prediction_rows()."""

    def test_empty_list_passes(self) -> None:
        """Test that an empty list passes validation."""
        validate_prediction_rows([])

    def test_all_valid_rows_pass(self) -> None:
        """Test that a batch of valid rows passes."""
        rows = [_make_row() for _ in range(10)]
        validate_prediction_rows(rows)

    def test_single_invalid_row_in_batch_fails(self) -> None:
        """Test that one invalid row in a batch raises."""
        rows = [
            _make_row(),
            _make_row(),
            _make_row(horizon="bogus"),  # index 2
            _make_row(),
        ]
        with pytest.raises(ValueError, match="Row 2"):
            validate_prediction_rows(rows)

    def test_validation_stops_at_first_error(self) -> None:
        """Test that validation stops at the first invalid row."""
        rows = [
            _make_row(horizon="bogus"),  # index 0 — fails
            _make_row(confidence=0.50),  # index 1 — would fail too
        ]
        with pytest.raises(ValueError, match="Row 0"):
            validate_prediction_rows(rows)


# ============================================================
# CONSTANTS TESTS
# ============================================================
class TestValidatorConstants:
    """Tests for module-level constants."""

    def test_valid_horizons(self) -> None:
        """Test that VALID_HORIZONS contains 24h and 7d."""
        assert VALID_HORIZONS == ("24h", "7d")

    def test_valid_confidence_levels(self) -> None:
        """Test that VALID_CONFIDENCE_LEVELS contains the expected levels."""
        assert VALID_CONFIDENCE_LEVELS == (0.70, 0.85, 0.95)