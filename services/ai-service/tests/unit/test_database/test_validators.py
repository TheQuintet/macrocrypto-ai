"""Unit tests for database validators.

Test organization:
    - TestValidatePredictionRow: single prediction row validation
    - TestValidatePredictionRows: prediction batch validation
    - TestValidatePerformanceRow: single performance row validation
    - TestValidatePerformanceRows: performance batch validation
    - TestValidateModelPerformanceRow: single model performance row (M7)
    - TestValidateModelPerformanceRows: model performance batch (M7)
    - TestValidateCorrelationRow: single correlation row (A1.1)
    - TestValidateCorrelationRows: correlation batch (A1.1)
    - TestValidateExportHistoryRow: single export history row (A2.1)
    - TestValidateExportHistoryRows: export history batch (A2.1)
    - TestValidatorConstants: module constants
"""

from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from app.database.repositories.prediction_repository import PredictionRow
from app.database.validators import (
    VALID_CONFIDENCE_LEVELS,
    VALID_CORRELATION_DIRECTIONS,
    VALID_CORRELATION_STRENGTHS,
    VALID_CORRELATION_WINDOWS,
    VALID_DATA_TYPE_NAMES,
    VALID_EXPORT_STATUSES,
    VALID_EXPORT_TIMEFRAMES,
    VALID_EXPORT_TYPES,
    VALID_HORIZONS,
    VALID_INDICATOR_NAMES,
    VALID_MARKET_CONDITIONS,
    validate_correlation_row,
    validate_correlation_rows,
    validate_export_history_row,
    validate_export_history_rows,
    validate_model_performance_row,
    validate_model_performance_rows,
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


def _make_model_perf_dict(**overrides) -> Dict[str, Any]:
    """Build a valid model_performance row as a dict."""
    defaults = {
        "model_name": "prophet_fresh",
        "horizon": "24h",
        "mae": 100.0,
        "rmse": 120.0,
        "mape": 1.5,
        "directional_accuracy": 62.0,
        "sample_size": 480,
        "calculated_at": datetime.now(timezone.utc),
    }
    defaults.update(overrides)
    return defaults


def _make_correlation_dict(**overrides) -> Dict[str, Any]:
    """Build a valid btc_macro_correlation row as a dict."""
    defaults = {
        "indicator_name": "inflation",
        "window_days": 90,
        "calculated_at": datetime.now(timezone.utc),
        "correlation_coefficient": -0.42,
        "strength": "medium",
        "direction": "negative",
        "p_value": 0.03,
    }
    defaults.update(overrides)
    return defaults


def _make_export_history_dict(**overrides) -> Dict[str, Any]:
    """Build a valid export_history row as a dict."""
    defaults = {
        "user_id": "analyst-42",
        "export_type": "csv",
        "data_types": ["btc_price"],
        "timeframe": "90d",
        "file_name": "macro-crypto-btc_price-90d-2026-09-15.csv",
        "file_size": 2048,
        "status": "pending",
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

    def test_none_prediction_id_passes(self) -> None:
        """Test that a None prediction_id passes (backtest rows).

        Migration 005 made prediction_id nullable so walk-forward
        backtest rows (which have no corresponding btc_predictions
        entry) can be stored. The validator must accept None.
        """
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
# MODEL PERFORMANCE ROW TESTS (M7)
# ============================================================
class TestValidateModelPerformanceRow:
    """Tests for validate_model_performance_row()."""

    def test_valid_dict_passes(self) -> None:
        """Test that a fully valid dict passes."""
        validate_model_performance_row(_make_model_perf_dict())

    def test_valid_object_passes(self) -> None:
        """Test that a valid object-shaped row passes."""
        validate_model_performance_row(
            _PerfObj(**_make_model_perf_dict())
        )

    def test_all_metrics_null_passes(self) -> None:
        """Test that a row with all metric fields None still passes."""
        validate_model_performance_row(
            _make_model_perf_dict(
                mae=None, rmse=None, mape=None, directional_accuracy=None
            )
        )

    # ---- model_name ----

    def test_empty_model_name_fails(self) -> None:
        """Test that an empty model_name fails."""
        with pytest.raises(ValueError, match="model_name must be non-empty"):
            validate_model_performance_row(
                _make_model_perf_dict(model_name="")
            )

    def test_whitespace_model_name_fails(self) -> None:
        """Test that a whitespace-only model_name fails."""
        with pytest.raises(ValueError, match="model_name must be non-empty"):
            validate_model_performance_row(
                _make_model_perf_dict(model_name="   ")
            )

    # ---- horizon ----

    def test_invalid_horizon_fails(self) -> None:
        """Test that an invalid horizon fails."""
        with pytest.raises(ValueError, match="invalid horizon"):
            validate_model_performance_row(
                _make_model_perf_dict(horizon="1h")
            )

    def test_7d_horizon_passes(self) -> None:
        """Test that '7d' horizon passes."""
        validate_model_performance_row(
            _make_model_perf_dict(horizon="7d")
        )

    # ---- sample_size ----

    def test_missing_sample_size_fails(self) -> None:
        """Test that a missing sample_size fails."""
        row = _make_model_perf_dict()
        del row["sample_size"]
        with pytest.raises(ValueError, match="sample_size must be set"):
            validate_model_performance_row(row)

    def test_non_integer_sample_size_fails(self) -> None:
        """Test that a non-integer sample_size fails."""
        with pytest.raises(ValueError, match="sample_size must be an integer"):
            validate_model_performance_row(
                _make_model_perf_dict(sample_size=10.5)
            )

    def test_boolean_sample_size_fails(self) -> None:
        """Test that a bool sample_size fails (bool is an int subclass)."""
        with pytest.raises(ValueError, match="sample_size must be an integer"):
            validate_model_performance_row(
                _make_model_perf_dict(sample_size=True)
            )

    def test_zero_sample_size_fails(self) -> None:
        """Test that a zero sample_size fails."""
        with pytest.raises(ValueError, match="sample_size must be positive"):
            validate_model_performance_row(
                _make_model_perf_dict(sample_size=0)
            )

    def test_negative_sample_size_fails(self) -> None:
        """Test that a negative sample_size fails."""
        with pytest.raises(ValueError, match="sample_size must be positive"):
            validate_model_performance_row(
                _make_model_perf_dict(sample_size=-5)
            )

    # ---- calculated_at ----

    def test_missing_calculated_at_fails(self) -> None:
        """Test that a missing calculated_at fails."""
        row = _make_model_perf_dict()
        del row["calculated_at"]
        with pytest.raises(ValueError, match="calculated_at must be set"):
            validate_model_performance_row(row)

    def test_none_calculated_at_fails(self) -> None:
        """Test that a None calculated_at fails."""
        with pytest.raises(ValueError, match="calculated_at must be set"):
            validate_model_performance_row(
                _make_model_perf_dict(calculated_at=None)
            )

    # ---- metrics ----

    def test_negative_mae_fails(self) -> None:
        """Test that a negative MAE fails."""
        with pytest.raises(ValueError, match="mae must be >= 0"):
            validate_model_performance_row(
                _make_model_perf_dict(mae=-1.0)
            )

    def test_negative_rmse_fails(self) -> None:
        """Test that a negative RMSE fails."""
        with pytest.raises(ValueError, match="rmse must be >= 0"):
            validate_model_performance_row(
                _make_model_perf_dict(rmse=-1.0)
            )

    def test_negative_mape_fails(self) -> None:
        """Test that a negative MAPE fails."""
        with pytest.raises(ValueError, match="mape must be >= 0"):
            validate_model_performance_row(
                _make_model_perf_dict(mape=-1.0)
            )

    def test_non_finite_mae_fails(self) -> None:
        """Test that an infinite MAE fails."""
        with pytest.raises(ValueError, match="mae must be finite when set"):
            validate_model_performance_row(
                _make_model_perf_dict(mae=float("inf"))
            )

    def test_zero_metrics_pass(self) -> None:
        """Test that zero metrics are valid."""
        validate_model_performance_row(
            _make_model_perf_dict(mae=0.0, rmse=0.0, mape=0.0)
        )

    # ---- directional_accuracy ----

    def test_directional_accuracy_below_0_fails(self) -> None:
        """Test that directional_accuracy < 0 fails."""
        with pytest.raises(
            ValueError, match="directional_accuracy must be in"
        ):
            validate_model_performance_row(
                _make_model_perf_dict(directional_accuracy=-0.1)
            )

    def test_directional_accuracy_above_100_fails(self) -> None:
        """Test that directional_accuracy > 100 fails."""
        with pytest.raises(
            ValueError, match="directional_accuracy must be in"
        ):
            validate_model_performance_row(
                _make_model_perf_dict(directional_accuracy=100.1)
            )

    def test_directional_accuracy_exactly_0_passes(self) -> None:
        """Test that directional_accuracy == 0 passes (boundary)."""
        validate_model_performance_row(
            _make_model_perf_dict(directional_accuracy=0.0)
        )

    def test_directional_accuracy_exactly_100_passes(self) -> None:
        """Test that directional_accuracy == 100 passes (boundary)."""
        validate_model_performance_row(
            _make_model_perf_dict(directional_accuracy=100.0)
        )

    def test_non_finite_directional_accuracy_fails(self) -> None:
        """Test that an infinite directional_accuracy fails."""
        with pytest.raises(
            ValueError, match="directional_accuracy must be finite"
        ):
            validate_model_performance_row(
                _make_model_perf_dict(
                    directional_accuracy=float("inf")
                )
            )

    # ---- error message ----

    def test_error_message_includes_index(self) -> None:
        """Test that error messages include the row index."""
        with pytest.raises(ValueError, match="Row 7"):
            validate_model_performance_row(
                _make_model_perf_dict(horizon="bogus"), index=7
            )


# ============================================================
# MODEL PERFORMANCE BATCH TESTS (M7)
# ============================================================
class TestValidateModelPerformanceRows:
    """Tests for validate_model_performance_rows()."""

    def test_empty_list_passes(self) -> None:
        """Test that an empty list passes."""
        validate_model_performance_rows([])

    def test_all_valid_rows_pass(self) -> None:
        """Test that a batch of valid rows passes."""
        rows = [_make_model_perf_dict() for _ in range(5)]
        validate_model_performance_rows(rows)

    def test_single_invalid_row_in_batch_fails(self) -> None:
        """Test that one invalid row in a batch raises with its index."""
        rows = [
            _make_model_perf_dict(),
            _make_model_perf_dict(),
            _make_model_perf_dict(sample_size=0),  # index 2
            _make_model_perf_dict(),
        ]
        with pytest.raises(ValueError, match="Row 2"):
            validate_model_performance_rows(rows)

    def test_validation_stops_at_first_error(self) -> None:
        """Test that validation stops at the first invalid row."""
        rows = [
            _make_model_perf_dict(horizon="bogus"),  # index 0 — fails
            _make_model_perf_dict(mae=-1.0),  # index 1 — would fail too
        ]
        with pytest.raises(ValueError, match="Row 0"):
            validate_model_performance_rows(rows)


# ============================================================
# CORRELATION ROW TESTS (A1.1)
# ============================================================
class TestValidateCorrelationRow:
    """Tests for validate_correlation_row()."""

    def test_valid_dict_passes(self) -> None:
        """Test that a fully valid dict passes."""
        validate_correlation_row(_make_correlation_dict())

    def test_valid_object_passes(self) -> None:
        """Test that a valid object-shaped row passes."""
        validate_correlation_row(
            _PerfObj(**_make_correlation_dict())
        )

    def test_none_p_value_passes(self) -> None:
        """Test that None p_value passes (A1.4 not yet run)."""
        validate_correlation_row(
            _make_correlation_dict(p_value=None)
        )

    # ---- indicator_name ----

    def test_invalid_indicator_raises(self) -> None:
        """Test that an invalid indicator name raises."""
        with pytest.raises(ValueError, match="invalid indicator_name"):
            validate_correlation_row(
                _make_correlation_dict(indicator_name="bogus")
            )

    def test_all_valid_indicators_pass(self) -> None:
        """Test that all four valid indicator names pass."""
        for name in ("inflation", "rates", "gdp", "unemployment"):
            validate_correlation_row(
                _make_correlation_dict(indicator_name=name)
            )

    # ---- window_days ----

    def test_invalid_window_raises(self) -> None:
        """Test that an invalid window raises."""
        with pytest.raises(ValueError, match="invalid window_days"):
            validate_correlation_row(
                _make_correlation_dict(window_days=45)
            )

    def test_all_valid_windows_pass(self) -> None:
        """Test that all three valid windows pass."""
        for window in (30, 90, 365):
            validate_correlation_row(
                _make_correlation_dict(window_days=window)
            )

    # ---- calculated_at ----

    def test_missing_calculated_at_raises(self) -> None:
        """Test that a missing calculated_at raises."""
        row = _make_correlation_dict()
        del row["calculated_at"]
        with pytest.raises(ValueError, match="calculated_at must be set"):
            validate_correlation_row(row)

    def test_none_calculated_at_raises(self) -> None:
        """Test that a None calculated_at raises."""
        with pytest.raises(ValueError, match="calculated_at must be set"):
            validate_correlation_row(
                _make_correlation_dict(calculated_at=None)
            )

    # ---- correlation_coefficient ----

    def test_coefficient_above_one_raises(self) -> None:
        """Test that a coefficient > 1 raises."""
        with pytest.raises(
            ValueError, match="correlation_coefficient must be in"
        ):
            validate_correlation_row(
                _make_correlation_dict(correlation_coefficient=1.01)
            )

    def test_coefficient_below_minus_one_raises(self) -> None:
        """Test that a coefficient < -1 raises."""
        with pytest.raises(
            ValueError, match="correlation_coefficient must be in"
        ):
            validate_correlation_row(
                _make_correlation_dict(correlation_coefficient=-1.01)
            )

    def test_none_coefficient_raises(self) -> None:
        """Test that a None coefficient raises."""
        with pytest.raises(
            ValueError, match="correlation_coefficient must be a finite"
        ):
            validate_correlation_row(
                _make_correlation_dict(correlation_coefficient=None)
            )

    def test_nan_coefficient_raises(self) -> None:
        """Test that a NaN coefficient raises."""
        with pytest.raises(
            ValueError, match="correlation_coefficient must be a finite"
        ):
            validate_correlation_row(
                _make_correlation_dict(
                    correlation_coefficient=float("nan")
                )
            )

    def test_inf_coefficient_raises(self) -> None:
        """Test that an infinite coefficient raises."""
        with pytest.raises(
            ValueError, match="correlation_coefficient must be a finite"
        ):
            validate_correlation_row(
                _make_correlation_dict(
                    correlation_coefficient=float("inf")
                )
            )

    def test_boundary_coefficient_minus_one_passes(self) -> None:
        """Test that -1.0 is a valid coefficient (boundary)."""
        validate_correlation_row(
            _make_correlation_dict(correlation_coefficient=-1.0)
        )

    def test_boundary_coefficient_plus_one_passes(self) -> None:
        """Test that +1.0 is a valid coefficient (boundary)."""
        validate_correlation_row(
            _make_correlation_dict(correlation_coefficient=1.0)
        )

    def test_boundary_coefficient_zero_passes(self) -> None:
        """Test that 0.0 is a valid coefficient."""
        validate_correlation_row(
            _make_correlation_dict(correlation_coefficient=0.0)
        )

    # ---- strength ----

    def test_invalid_strength_raises(self) -> None:
        """Test that an invalid strength raises."""
        with pytest.raises(ValueError, match="invalid strength"):
            validate_correlation_row(
                _make_correlation_dict(strength="enormous")
            )

    def test_all_valid_strengths_pass(self) -> None:
        """Test that all three valid strengths pass."""
        for s in ("strong", "medium", "weak"):
            validate_correlation_row(
                _make_correlation_dict(strength=s)
            )

    # ---- direction ----

    def test_invalid_direction_raises(self) -> None:
        """Test that an invalid direction raises."""
        with pytest.raises(ValueError, match="invalid direction"):
            validate_correlation_row(
                _make_correlation_dict(direction="neutral")
            )

    def test_all_valid_directions_pass(self) -> None:
        """Test that both valid directions pass."""
        for d in ("positive", "negative"):
            validate_correlation_row(
                _make_correlation_dict(direction=d)
            )

    # ---- p_value ----

    def test_p_value_above_one_raises(self) -> None:
        """Test that a p_value > 1 raises."""
        with pytest.raises(ValueError, match="p_value must be in"):
            validate_correlation_row(
                _make_correlation_dict(p_value=1.5)
            )

    def test_p_value_below_zero_raises(self) -> None:
        """Test that a p_value < 0 raises."""
        with pytest.raises(ValueError, match="p_value must be in"):
            validate_correlation_row(
                _make_correlation_dict(p_value=-0.1)
            )

    def test_boundary_p_value_zero_passes(self) -> None:
        """Test that p_value == 0 passes (boundary)."""
        validate_correlation_row(
            _make_correlation_dict(p_value=0.0)
        )

    def test_boundary_p_value_one_passes(self) -> None:
        """Test that p_value == 1 passes (boundary)."""
        validate_correlation_row(
            _make_correlation_dict(p_value=1.0)
        )

    def test_nan_p_value_raises(self) -> None:
        """Test that a NaN p_value raises."""
        with pytest.raises(
            ValueError, match="p_value must be finite when set"
        ):
            validate_correlation_row(
                _make_correlation_dict(p_value=float("nan"))
            )

    # ---- error message ----

    def test_error_message_includes_index(self) -> None:
        """Test that error messages include the row index."""
        with pytest.raises(ValueError, match="Row 7"):
            validate_correlation_row(
                _make_correlation_dict(indicator_name="bogus"), index=7
            )


# ============================================================
# CORRELATION BATCH TESTS (A1.1)
# ============================================================
class TestValidateCorrelationRows:
    """Tests for validate_correlation_rows()."""

    def test_empty_list_passes(self) -> None:
        """Test that an empty list passes."""
        validate_correlation_rows([])

    def test_all_valid_rows_pass(self) -> None:
        """Test that a batch of valid rows passes."""
        rows = [_make_correlation_dict() for _ in range(5)]
        validate_correlation_rows(rows)

    def test_single_invalid_row_in_batch_fails(self) -> None:
        """Test that one invalid row in a batch raises with its index."""
        rows = [
            _make_correlation_dict(),
            _make_correlation_dict(),
            _make_correlation_dict(indicator_name="bogus"),  # index 2
            _make_correlation_dict(),
        ]
        with pytest.raises(ValueError, match="Row 2"):
            validate_correlation_rows(rows)

    def test_validation_stops_at_first_error(self) -> None:
        """Test that validation stops at the first invalid row."""
        rows = [
            _make_correlation_dict(indicator_name="bogus"),  # index 0
            _make_correlation_dict(window_days=45),  # index 1 — would fail
        ]
        with pytest.raises(ValueError, match="Row 0"):
            validate_correlation_rows(rows)


# ============================================================
# EXPORT HISTORY ROW TESTS (A2.1)
# ============================================================
class TestValidateExportHistoryRow:
    """Tests for validate_export_history_row()."""

    def test_valid_dict_passes(self) -> None:
        """Test that a fully valid dict passes."""
        validate_export_history_row(_make_export_history_dict())

    def test_valid_object_passes(self) -> None:
        """Test that a valid object-shaped row passes."""
        validate_export_history_row(
            _PerfObj(**_make_export_history_dict())
        )

    def test_empty_data_types_passes(self) -> None:
        """Test that an empty data_types list is allowed."""
        validate_export_history_row(
            _make_export_history_dict(data_types=[])
        )

    def test_none_user_id_passes(self) -> None:
        """Test that a None user_id is allowed (system-triggered)."""
        validate_export_history_row(
            _make_export_history_dict(user_id=None)
        )

    def test_none_file_size_passes(self) -> None:
        """Test that a None file_size is allowed (pending exports)."""
        validate_export_history_row(
            _make_export_history_dict(file_size=None)
        )

    # ---- export_type ----

    def test_invalid_export_type_raises(self) -> None:
        """Test that an unknown export_type raises."""
        with pytest.raises(ValueError, match="invalid export_type"):
            validate_export_history_row(
                _make_export_history_dict(export_type="xlsx")
            )

    def test_all_valid_export_types_pass(self) -> None:
        """Test that all three valid export types pass."""
        for t in ("csv", "png", "pdf"):
            validate_export_history_row(
                _make_export_history_dict(export_type=t)
            )

    # ---- timeframe ----

    def test_invalid_timeframe_raises(self) -> None:
        """Test that an unknown timeframe raises."""
        with pytest.raises(ValueError, match="invalid timeframe"):
            validate_export_history_row(
                _make_export_history_dict(timeframe="7d")
            )

    def test_all_valid_timeframes_pass(self) -> None:
        """Test that all four valid timeframes pass."""
        for tf in ("30d", "90d", "1y", "5y"):
            validate_export_history_row(
                _make_export_history_dict(timeframe=tf)
            )

    # ---- file_name ----

    def test_empty_file_name_raises(self) -> None:
        """Test that an empty file_name raises."""
        with pytest.raises(ValueError, match="file_name must be non-empty"):
            validate_export_history_row(
                _make_export_history_dict(file_name="")
            )

    def test_whitespace_file_name_raises(self) -> None:
        """Test that a whitespace-only file_name raises."""
        with pytest.raises(ValueError, match="file_name must be non-empty"):
            validate_export_history_row(
                _make_export_history_dict(file_name="   ")
            )

    # ---- status ----

    def test_invalid_status_raises(self) -> None:
        """Test that an unknown status raises."""
        with pytest.raises(ValueError, match="invalid status"):
            validate_export_history_row(
                _make_export_history_dict(status="running")
            )

    def test_all_valid_statuses_pass(self) -> None:
        """Test that all three valid statuses pass."""
        for s in ("pending", "completed", "failed"):
            validate_export_history_row(
                _make_export_history_dict(status=s)
            )

    # ---- data_types ----

    def test_missing_data_types_raises(self) -> None:
        """Test that a missing data_types raises."""
        row = _make_export_history_dict()
        del row["data_types"]
        with pytest.raises(ValueError, match="data_types must be set"):
            validate_export_history_row(row)

    def test_none_data_types_raises(self) -> None:
        """Test that a None data_types raises."""
        with pytest.raises(ValueError, match="data_types must be set"):
            validate_export_history_row(
                _make_export_history_dict(data_types=None)
            )

    def test_non_list_data_types_raises(self) -> None:
        """Test that a non-list data_types raises."""
        with pytest.raises(ValueError, match="data_types must be a list"):
            validate_export_history_row(
                _make_export_history_dict(data_types="btc_price")
            )

    def test_unknown_data_type_raises(self) -> None:
        """Test that an unknown data-type string raises."""
        with pytest.raises(ValueError, match="invalid data_type"):
            validate_export_history_row(
                _make_export_history_dict(data_types=["btc_price", "bogus"])
            )

    def test_duplicate_data_type_raises(self) -> None:
        """Test that duplicate data-type strings raise."""
        with pytest.raises(ValueError, match="duplicate data_type"):
            validate_export_history_row(
                _make_export_history_dict(
                    data_types=["btc_price", "btc_price"]
                )
            )

    def test_non_string_data_type_raises(self) -> None:
        """Test that a non-string entry in data_types raises."""
        with pytest.raises(
            ValueError, match="data_types entries must be strings"
        ):
            validate_export_history_row(
                _make_export_history_dict(data_types=[123])
            )

    def test_all_valid_data_types_pass(self) -> None:
        """Test that every known data-type name passes."""
        for dt in VALID_DATA_TYPE_NAMES:
            validate_export_history_row(
                _make_export_history_dict(data_types=[dt])
            )

    # ---- user_id ----

    def test_empty_user_id_raises(self) -> None:
        """Test that an empty user_id raises."""
        with pytest.raises(ValueError, match="user_id must be a non-empty"):
            validate_export_history_row(
                _make_export_history_dict(user_id="")
            )

    def test_whitespace_user_id_raises(self) -> None:
        """Test that a whitespace-only user_id raises."""
        with pytest.raises(ValueError, match="user_id must be a non-empty"):
            validate_export_history_row(
                _make_export_history_dict(user_id="   ")
            )

    def test_non_string_user_id_raises(self) -> None:
        """Test that a non-string user_id raises."""
        with pytest.raises(ValueError, match="user_id must be a non-empty"):
            validate_export_history_row(
                _make_export_history_dict(user_id=123)
            )

    # ---- file_size ----

    def test_negative_file_size_raises(self) -> None:
        """Test that a negative file_size raises."""
        with pytest.raises(ValueError, match="file_size must be >= 0"):
            validate_export_history_row(
                _make_export_history_dict(file_size=-1)
            )

    def test_zero_file_size_passes(self) -> None:
        """Test that a zero file_size passes (boundary)."""
        validate_export_history_row(
            _make_export_history_dict(file_size=0)
        )

    def test_boolean_file_size_raises(self) -> None:
        """Test that a bool file_size raises (bool is an int subclass)."""
        with pytest.raises(ValueError, match="file_size must be an integer"):
            validate_export_history_row(
                _make_export_history_dict(file_size=True)
            )

    def test_non_integer_file_size_raises(self) -> None:
        """Test that a non-integer file_size raises."""
        with pytest.raises(ValueError, match="file_size must be an integer"):
            validate_export_history_row(
                _make_export_history_dict(file_size=10.5)
            )

    # ---- error message ----

    def test_error_message_includes_index(self) -> None:
        """Test that error messages include the row index."""
        with pytest.raises(ValueError, match="Row 7"):
            validate_export_history_row(
                _make_export_history_dict(export_type="xlsx"), index=7
            )


# ============================================================
# EXPORT HISTORY BATCH TESTS (A2.1)
# ============================================================
class TestValidateExportHistoryRows:
    """Tests for validate_export_history_rows()."""

    def test_empty_list_passes(self) -> None:
        """Test that an empty list passes."""
        validate_export_history_rows([])

    def test_all_valid_rows_pass(self) -> None:
        """Test that a batch of valid rows passes."""
        rows = [_make_export_history_dict() for _ in range(5)]
        validate_export_history_rows(rows)

    def test_single_invalid_row_in_batch_fails(self) -> None:
        """Test that one invalid row in a batch raises with its index."""
        rows = [
            _make_export_history_dict(),
            _make_export_history_dict(),
            _make_export_history_dict(export_type="xlsx"),  # index 2
            _make_export_history_dict(),
        ]
        with pytest.raises(ValueError, match="Row 2"):
            validate_export_history_rows(rows)

    def test_validation_stops_at_first_error(self) -> None:
        """Test that validation stops at the first invalid row."""
        rows = [
            _make_export_history_dict(export_type="xlsx"),  # index 0
            _make_export_history_dict(timeframe="7d"),  # index 1 — would fail
        ]
        with pytest.raises(ValueError, match="Row 0"):
            validate_export_history_rows(rows)


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

    def test_valid_indicator_names(self) -> None:
        """Test that VALID_INDICATOR_NAMES contains the four labels."""
        assert VALID_INDICATOR_NAMES == (
            "inflation",
            "rates",
            "gdp",
            "unemployment",
        )

    def test_valid_correlation_windows(self) -> None:
        """Test that VALID_CORRELATION_WINDOWS contains 30, 90, 365."""
        assert VALID_CORRELATION_WINDOWS == (30, 90, 365)

    def test_valid_correlation_strengths(self) -> None:
        """Test that VALID_CORRELATION_STRENGTHS contains three labels."""
        assert VALID_CORRELATION_STRENGTHS == (
            "strong",
            "medium",
            "weak",
        )

    def test_valid_correlation_directions(self) -> None:
        """Test that VALID_CORRELATION_DIRECTIONS contains two labels."""
        assert VALID_CORRELATION_DIRECTIONS == (
            "positive",
            "negative",
        )

    def test_valid_export_types(self) -> None:
        """Test that VALID_EXPORT_TYPES contains csv, png, pdf."""
        assert VALID_EXPORT_TYPES == ("csv", "png", "pdf")

    def test_valid_export_timeframes(self) -> None:
        """Test that VALID_EXPORT_TIMEFRAMES contains the four labels."""
        assert VALID_EXPORT_TIMEFRAMES == ("30d", "90d", "1y", "5y")

    def test_valid_export_statuses(self) -> None:
        """Test that VALID_EXPORT_STATUSES contains the three states."""
        assert VALID_EXPORT_STATUSES == (
            "pending",
            "completed",
            "failed",
        )

    def test_valid_data_type_names(self) -> None:
        """Test that VALID_DATA_TYPE_NAMES contains the six data types."""
        assert VALID_DATA_TYPE_NAMES == (
            "btc_price",
            "predictions",
            "model_performance",
            "correlations",
            "regimes",
            "events",
        )