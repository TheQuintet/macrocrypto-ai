"""Unit tests for database validators.

Test organization:
    - TestValidatePredictionRow: single prediction row validation
    - TestValidatePredictionRows: prediction batch validation
    - TestValidatePerformanceRow: single performance row validation
    - TestValidatePerformanceRows: performance batch validation
    - TestValidatorConstants: module constants
"""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from app.database.repositories.prediction_repository import PredictionRow
from app.database.validators import (
    VALID_CONFIDENCE_LEVELS,
    VALID_HORIZONS,
    VALID_MARKET_CONDITIONS,
    validate_performance_row,
    validate_performance_rows,
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


def _make_perf_dict(**overrides) -> Dict[str, Any]:
    """Build a valid prediction_performance row as a dict."""
    defaults = {
        "prediction_id": 1,
        "horizon": "24h",
        "model_name": "prophet",
        "model_version": "1.0.0",
        "forecast_date": datetime.now(timezone.utc),
        "predicted_price": 50_000.0,
        "actual_price": 50_500.0,
        "mae": 500.0,
        "rmse": 500.0,
        "mape": 0.99,
        "market_condition": "bull",
    }
    defaults.update(overrides)
    return defaults


class _PerfObj:
    """A minimal object shape for testing the validator's attribute path."""

    def __init__(self, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


# ============================================================
# PREDICTION ROW TESTS
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
# PREDICTION BATCH TESTS
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
# PERFORMANCE ROW TESTS
# ============================================================
class TestValidatePerformanceRow:
    """Tests for validate_performance_row()."""

    def test_valid_dict_passes(self) -> None:
        """Test that a valid performance row dict passes."""
        validate_performance_row(_make_perf_dict())

    def test_valid_object_passes(self) -> None:
        """Test that a valid object-shaped row passes."""
        validate_performance_row(_PerfObj(**_make_perf_dict()))

    # ---- prediction_id ----

    def test_none_prediction_id_fails(self) -> None:
        """Test that a None prediction_id fails."""
        with pytest.raises(ValueError, match="prediction_id"):
            validate_performance_row(_make_perf_dict(prediction_id=None))

    def test_non_integer_prediction_id_fails(self) -> None:
        """Test that a non-integer prediction_id fails."""
        with pytest.raises(ValueError, match="prediction_id"):
            validate_performance_row(
                _make_perf_dict(prediction_id="not-an-int")
            )

    def test_zero_prediction_id_fails(self) -> None:
        """Test that a zero prediction_id fails."""
        with pytest.raises(ValueError, match="prediction_id must be positive"):
            validate_performance_row(_make_perf_dict(prediction_id=0))

    def test_negative_prediction_id_fails(self) -> None:
        """Test that a negative prediction_id fails."""
        with pytest.raises(ValueError, match="prediction_id must be positive"):
            validate_performance_row(_make_perf_dict(prediction_id=-5))

    # ---- horizon ----

    def test_invalid_horizon_fails(self) -> None:
        """Test that an invalid horizon fails."""
        with pytest.raises(ValueError, match="invalid horizon"):
            validate_performance_row(_make_perf_dict(horizon="1h"))

    def test_7d_horizon_passes(self) -> None:
        """Test that '7d' horizon passes."""
        validate_performance_row(_make_perf_dict(horizon="7d"))

    # ---- model_name / model_version ----

    def test_empty_model_name_fails(self) -> None:
        """Test that an empty model_name fails."""
        with pytest.raises(ValueError, match="model_name"):
            validate_performance_row(_make_perf_dict(model_name=""))

    def test_empty_model_version_fails(self) -> None:
        """Test that an empty model_version fails."""
        with pytest.raises(ValueError, match="model_version"):
            validate_performance_row(_make_perf_dict(model_version=""))

    # ---- forecast_date ----

    def test_none_forecast_date_fails(self) -> None:
        """Test that a None forecast_date fails."""
        with pytest.raises(ValueError, match="forecast_date"):
            validate_performance_row(_make_perf_dict(forecast_date=None))

    # ---- prices ----

    def test_nan_predicted_price_fails(self) -> None:
        """Test that a NaN predicted_price fails."""
        with pytest.raises(ValueError, match="predicted_price"):
            validate_performance_row(
                _make_perf_dict(predicted_price=float("nan"))
            )

    def test_zero_predicted_price_fails(self) -> None:
        """Test that a zero predicted_price fails."""
        with pytest.raises(ValueError, match="predicted_price must be positive"):
            validate_performance_row(_make_perf_dict(predicted_price=0.0))

    def test_negative_actual_price_fails(self) -> None:
        """Test that a negative actual_price fails."""
        with pytest.raises(ValueError, match="actual_price must be positive"):
            validate_performance_row(_make_perf_dict(actual_price=-100.0))

    # ---- metrics ----

    def test_null_metrics_pass(self) -> None:
        """Test that None metrics are allowed (not yet computed)."""
        validate_performance_row(
            _make_perf_dict(mae=None, rmse=None, mape=None)
        )

    def test_negative_mae_fails(self) -> None:
        """Test that a negative mae fails."""
        with pytest.raises(ValueError, match="mae must be >= 0"):
            validate_performance_row(_make_perf_dict(mae=-1.0))

    def test_negative_rmse_fails(self) -> None:
        """Test that a negative rmse fails."""
        with pytest.raises(ValueError, match="rmse must be >= 0"):
            validate_performance_row(_make_perf_dict(rmse=-1.0))

    def test_negative_mape_fails(self) -> None:
        """Test that a negative mape fails."""
        with pytest.raises(ValueError, match="mape must be >= 0"):
            validate_performance_row(_make_perf_dict(mape=-1.0))

    def test_infinite_mae_fails(self) -> None:
        """Test that an infinite mae fails."""
        with pytest.raises(ValueError, match="mae"):
            validate_performance_row(
                _make_perf_dict(mae=float("inf"))
            )

    def test_zero_metrics_pass(self) -> None:
        """Test that zero metrics are valid."""
        validate_performance_row(
            _make_perf_dict(mae=0.0, rmse=0.0, mape=0.0)
        )

    # ---- market_condition ----

    def test_null_market_condition_passes(self) -> None:
        """Test that None market_condition is allowed."""
        validate_performance_row(
            _make_perf_dict(market_condition=None)
        )

    def test_all_valid_market_conditions_pass(self) -> None:
        """Test that all four market conditions pass."""
        for cond in ("bull", "bear", "volatile", "neutral"):
            validate_performance_row(
                _make_perf_dict(market_condition=cond)
            )

    def test_invalid_market_condition_fails(self) -> None:
        """Test that an unknown market_condition fails."""
        with pytest.raises(ValueError, match="invalid market_condition"):
            validate_performance_row(
                _make_perf_dict(market_condition="sideways")
            )

    # ---- error message ----

    def test_error_message_includes_index(self) -> None:
        """Test that error messages include the row index."""
        with pytest.raises(ValueError, match="Row 7"):
            validate_performance_row(
                _make_perf_dict(prediction_id=0), index=7
            )


# ============================================================
# PERFORMANCE BATCH TESTS
# ============================================================
class TestValidatePerformanceRows:
    """Tests for validate_performance_rows()."""

    def test_empty_list_passes(self) -> None:
        """Test that an empty list passes."""
        validate_performance_rows([])

    def test_all_valid_dicts_pass(self) -> None:
        """Test that a batch of valid rows passes."""
        rows = [_make_perf_dict() for _ in range(5)]
        validate_performance_rows(rows)

    def test_single_invalid_row_in_batch_fails(self) -> None:
        """Test that one invalid row in a batch raises."""
        rows = [
            _make_perf_dict(),
            _make_perf_dict(),
            _make_perf_dict(horizon="bogus"),  # index 2
            _make_perf_dict(),
        ]
        with pytest.raises(ValueError, match="Row 2"):
            validate_performance_rows(rows)


# ============================================================
# CONSTANTS
# ============================================================
class TestValidatorConstants:
    """Tests for module-level constants."""

    def test_valid_horizons(self) -> None:
        """Test that VALID_HORIZONS contains 24h and 7d."""
        assert VALID_HORIZONS == ("24h", "7d")

    def test_valid_confidence_levels(self) -> None:
        """Test that VALID_CONFIDENCE_LEVELS contains the expected levels."""
        assert VALID_CONFIDENCE_LEVELS == (0.70, 0.85, 0.95)

    def test_valid_market_conditions(self) -> None:
        """Test that VALID_MARKET_CONDITIONS contains the four states."""
        assert VALID_MARKET_CONDITIONS == (
            "bull",
            "bear",
            "volatile",
            "neutral",
        )