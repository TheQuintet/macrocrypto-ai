"""Validators for AI Service database writes.

This module provides validation functions that enforce invariants
on data before it hits the database. Validators raise `ValueError`
with clear messages so callers can surface actionable errors.

Validators are called by repositories before INSERT / UPDATE, so
any caller (generator, scheduler, ad-hoc scripts) benefits from
the same checks.

Currently validates:
    - Prediction rows: bounds ordering, finiteness, enum membership
    - Performance rows: metric non-negativity, market condition enum
    - Model performance rows: metric range, sample_size positivity,
      horizon enum (M7)
    - Correlation rows: indicator/window/strength/direction enums,
      coefficient and p_value ranges (A1.1)
"""

import logging
import math
from typing import Any, Iterable, Optional

from app.database.repositories.prediction_repository import PredictionRow

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
VALID_HORIZONS = ("24h", "7d")
VALID_CONFIDENCE_LEVELS = (0.70, 0.85, 0.95)
VALID_MARKET_CONDITIONS = ("bull", "bear", "volatile", "neutral")

# A1.1 — correlation enums
VALID_INDICATOR_NAMES = ("inflation", "rates", "gdp", "unemployment")
VALID_CORRELATION_WINDOWS = (30, 90, 365)
VALID_CORRELATION_STRENGTHS = ("strong", "medium", "weak")
VALID_CORRELATION_DIRECTIONS = ("positive", "negative")


# ============================================================
# PREDICTION ROW VALIDATION
# ============================================================
def validate_prediction_row(
    row: PredictionRow,
    index: int = 0,
) -> None:
    """Validate a single prediction row.

    Checks:
        - All numeric fields are finite (no NaN / inf)
        - Bounds are correctly ordered: lower <= predicted <= upper
        - Confidence is one of 0.70, 0.85, 0.95
        - Horizon is one of '24h', '7d'
        - model_name is non-empty

    Args:
        row: The PredictionRow to validate.
        index: Row index (for error messages).

    Raises:
        ValueError: If the row violates any invariant.
    """
    # ---- 1. model_name non-empty ----
    if not row.model_name or not row.model_name.strip():
        raise ValueError(
            f"Row {index}: model_name must be non-empty"
        )

    # ---- 2. horizon valid ----
    if row.horizon not in VALID_HORIZONS:
        raise ValueError(
            f"Row {index}: invalid horizon '{row.horizon}'. "
            f"Must be one of {VALID_HORIZONS}."
        )

    # ---- 3. confidence valid ----
    if row.confidence not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(
            f"Row {index}: invalid confidence {row.confidence}. "
            f"Must be one of {VALID_CONFIDENCE_LEVELS}."
        )

    # ---- 4. Numeric fields are finite ----
    for field_name in ("predicted_price", "lower_bound", "upper_bound"):
        value = getattr(row, field_name)
        if value is None or not math.isfinite(value):
            raise ValueError(
                f"Row {index}: {field_name} must be a finite number, "
                f"got {value!r}"
            )

    # ---- 5. Bounds ordering ----
    if row.lower_bound > row.predicted_price:
        raise ValueError(
            f"Row {index}: lower_bound ({row.lower_bound}) must be "
            f"<= predicted_price ({row.predicted_price})"
        )

    if row.predicted_price > row.upper_bound:
        raise ValueError(
            f"Row {index}: predicted_price ({row.predicted_price}) "
            f"must be <= upper_bound ({row.upper_bound})"
        )


def validate_prediction_rows(
    rows: Iterable[PredictionRow],
) -> None:
    """Validate a batch of prediction rows.

    Fails on the first invalid row and includes its index in the
    error message. Returns None on success.

    Args:
        rows: An iterable of PredictionRow instances.

    Raises:
        ValueError: If any row is invalid.
    """
    for i, row in enumerate(rows):
        validate_prediction_row(row, index=i)

    logger.debug("All prediction rows passed validation")


# ============================================================
# PERFORMANCE ROW VALIDATION
# ============================================================
def validate_performance_row(
    row: Any,
    index: int = 0,
) -> None:
    """Validate a single prediction_performance row.

    The row may be a ``PerformanceRow`` dataclass, a dict, or any
    object with the expected attributes. This keeps the validator
    decoupled from the repository's concrete row type.

    Checks:
        - prediction_id is None or a positive integer (backtest
          rows have NULL; production evaluations reference a real
          prediction)
        - horizon is one of '24h', '7d'
        - model_name and model_version are non-empty
        - forecast_date is present
        - predicted_price and actual_price are finite and > 0
        - mae, rmse, mape (if present) are finite and >= 0
        - market_condition (if present) is one of the valid enum values

    Args:
        row: The row to validate (object or dict).
        index: Row index (for error messages).

    Raises:
        ValueError: If the row violates any invariant.
    """

    def _get(name: str) -> Any:
        """Read a field from a dict or object."""
        if isinstance(row, dict):
            return row.get(name)
        return getattr(row, name, None)

    # ---- 1. prediction_id: nullable, but must be a positive int when set ----
    prediction_id = _get("prediction_id")
    if prediction_id is not None:
        if not isinstance(prediction_id, int) or isinstance(prediction_id, bool):
            raise ValueError(
                f"Row {index}: prediction_id must be an integer or None, "
                f"got {prediction_id!r}"
            )
        if prediction_id <= 0:
            raise ValueError(
                f"Row {index}: prediction_id must be positive, "
                f"got {prediction_id}"
            )

    # ---- 2. horizon ----
    horizon = _get("horizon")
    if horizon not in VALID_HORIZONS:
        raise ValueError(
            f"Row {index}: invalid horizon '{horizon}'. "
            f"Must be one of {VALID_HORIZONS}."
        )

    # ---- 3. model_name / model_version ----
    for field_name in ("model_name", "model_version"):
        value = _get(field_name)
        if not value or not str(value).strip():
            raise ValueError(
                f"Row {index}: {field_name} must be non-empty"
            )

    # ---- 4. forecast_date ----
    forecast_date = _get("forecast_date")
    if forecast_date is None:
        raise ValueError(
            f"Row {index}: forecast_date must be set"
        )

    # ---- 5. Prices: finite and positive ----
    for field_name in ("predicted_price", "actual_price"):
        value = _get(field_name)
        if value is None or not math.isfinite(value):
            raise ValueError(
                f"Row {index}: {field_name} must be a finite number, "
                f"got {value!r}"
            )
        if value <= 0:
            raise ValueError(
                f"Row {index}: {field_name} must be positive, "
                f"got {value}"
            )

    # ---- 6. Metrics: nullable, but non-negative when present ----
    for field_name in ("mae", "rmse", "mape"):
        value = _get(field_name)
        if value is None:
            continue
        if not math.isfinite(value):
            raise ValueError(
                f"Row {index}: {field_name} must be finite when set, "
                f"got {value!r}"
            )
        if value < 0:
            raise ValueError(
                f"Row {index}: {field_name} must be >= 0, "
                f"got {value}"
            )

    # ---- 7. market_condition: nullable, but must be in enum ----
    market_condition = _get("market_condition")
    if market_condition is not None and market_condition not in (
        VALID_MARKET_CONDITIONS
    ):
        raise ValueError(
            f"Row {index}: invalid market_condition "
            f"'{market_condition}'. Must be one of "
            f"{VALID_MARKET_CONDITIONS} or None."
        )


def validate_performance_rows(
    rows: Iterable[Any],
) -> None:
    """Validate a batch of prediction_performance rows.

    Fails on the first invalid row and includes its index in the
    error message. Returns None on success.

    Args:
        rows: An iterable of performance rows (objects or dicts).

    Raises:
        ValueError: If any row is invalid.
    """
    for i, row in enumerate(rows):
        validate_performance_row(row, index=i)

    logger.debug("All performance rows passed validation")


# ============================================================
# MODEL PERFORMANCE ROW VALIDATION (M7)
# ============================================================
def validate_model_performance_row(
    row: Any,
    index: int = 0,
) -> None:
    """Validate a single model_performance row.

    The row may be a ``ModelPerformanceRow`` dataclass, a dict, or
    any object with the expected attributes. This keeps the
    validator decoupled from the repository's concrete row type.

    Checks:
        - model_name is non-empty
        - horizon is one of '24h', '7d'
        - sample_size is a positive integer
        - calculated_at is present
        - mae, rmse, mape (if present) are finite and >= 0
        - directional_accuracy (if present) is finite and in [0, 100]

    Args:
        row: The row to validate (object or dict).
        index: Row index (for error messages).

    Raises:
        ValueError: If the row violates any invariant.
    """

    def _get(name: str) -> Any:
        """Read a field from a dict or object."""
        if isinstance(row, dict):
            return row.get(name)
        return getattr(row, name, None)

    # ---- 1. model_name ----
    model_name = _get("model_name")
    if not model_name or not str(model_name).strip():
        raise ValueError(
            f"Row {index}: model_name must be non-empty"
        )

    # ---- 2. horizon ----
    horizon = _get("horizon")
    if horizon not in VALID_HORIZONS:
        raise ValueError(
            f"Row {index}: invalid horizon '{horizon}'. "
            f"Must be one of {VALID_HORIZONS}."
        )

    # ---- 3. sample_size: positive integer ----
    sample_size = _get("sample_size")
    if sample_size is None:
        raise ValueError(
            f"Row {index}: sample_size must be set"
        )
    if not isinstance(sample_size, int) or isinstance(sample_size, bool):
        raise ValueError(
            f"Row {index}: sample_size must be an integer, "
            f"got {sample_size!r}"
        )
    if sample_size <= 0:
        raise ValueError(
            f"Row {index}: sample_size must be positive, "
            f"got {sample_size}"
        )

    # ---- 4. calculated_at ----
    calculated_at = _get("calculated_at")
    if calculated_at is None:
        raise ValueError(
            f"Row {index}: calculated_at must be set"
        )

    # ---- 5. Metrics: nullable, but non-negative when present ----
    for field_name in ("mae", "rmse", "mape"):
        value = _get(field_name)
        if value is None:
            continue
        if not math.isfinite(value):
            raise ValueError(
                f"Row {index}: {field_name} must be finite when set, "
                f"got {value!r}"
            )
        if value < 0:
            raise ValueError(
                f"Row {index}: {field_name} must be >= 0, "
                f"got {value}"
            )

    # ---- 6. directional_accuracy: nullable, but in [0, 100] when set ----
    da = _get("directional_accuracy")
    if da is not None:
        if not math.isfinite(da):
            raise ValueError(
                f"Row {index}: directional_accuracy must be finite "
                f"when set, got {da!r}"
            )
        if da < 0 or da > 100:
            raise ValueError(
                f"Row {index}: directional_accuracy must be in "
                f"[0, 100], got {da}"
            )


def validate_model_performance_rows(
    rows: Iterable[Any],
) -> None:
    """Validate a batch of model_performance rows.

    Fails on the first invalid row and includes its index in the
    error message. Returns None on success.

    Args:
        rows: An iterable of model performance rows (objects or dicts).

    Raises:
        ValueError: If any row is invalid.
    """
    for i, row in enumerate(rows):
        validate_model_performance_row(row, index=i)

    logger.debug("All model performance rows passed validation")


# ============================================================
# CORRELATION ROW VALIDATION (A1.1)
# ============================================================
def validate_correlation_row(
    row: Any,
    index: int = 0,
) -> None:
    """Validate a single btc_macro_correlation row.

    The row may be a ``CorrelationRow`` dataclass, a dict, or any
    object with the expected attributes. This keeps the validator
    decoupled from the repository's concrete row type.

    Checks:
        - indicator_name is one of 'inflation', 'rates', 'gdp',
          'unemployment'
        - window_days is one of 30, 90, 365
        - calculated_at is present
        - correlation_coefficient is finite and in [-1, 1]
        - strength is one of 'strong', 'medium', 'weak'
        - direction is one of 'positive', 'negative'
        - p_value is None, or finite and in [0, 1]

    Note: this validator does NOT check that `strength` and
    `direction` are consistent with the coefficient. That
    consistency is A1.3's responsibility — the table stores the
    derived labels as a cache, not as the source of truth.

    Args:
        row: The row to validate (object or dict).
        index: Row index (for error messages).

    Raises:
        ValueError: If the row violates any invariant.
    """

    def _get(name: str) -> Any:
        """Read a field from a dict or object."""
        if isinstance(row, dict):
            return row.get(name)
        return getattr(row, name, None)

    # ---- 1. indicator_name ----
    indicator_name = _get("indicator_name")
    if indicator_name not in VALID_INDICATOR_NAMES:
        raise ValueError(
            f"Row {index}: invalid indicator_name '{indicator_name}'. "
            f"Must be one of {VALID_INDICATOR_NAMES}."
        )

    # ---- 2. window_days ----
    window_days = _get("window_days")
    if window_days not in VALID_CORRELATION_WINDOWS:
        raise ValueError(
            f"Row {index}: invalid window_days {window_days}. "
            f"Must be one of {VALID_CORRELATION_WINDOWS}."
        )

    # ---- 3. calculated_at ----
    calculated_at = _get("calculated_at")
    if calculated_at is None:
        raise ValueError(
            f"Row {index}: calculated_at must be set"
        )

    # ---- 4. correlation_coefficient: finite and in [-1, 1] ----
    coefficient = _get("correlation_coefficient")
    if coefficient is None or not math.isfinite(coefficient):
        raise ValueError(
            f"Row {index}: correlation_coefficient must be a finite "
            f"number, got {coefficient!r}"
        )
    if coefficient < -1.0 or coefficient > 1.0:
        raise ValueError(
            f"Row {index}: correlation_coefficient must be in "
            f"[-1, 1], got {coefficient}"
        )

    # ---- 5. strength ----
    strength = _get("strength")
    if strength not in VALID_CORRELATION_STRENGTHS:
        raise ValueError(
            f"Row {index}: invalid strength '{strength}'. "
            f"Must be one of {VALID_CORRELATION_STRENGTHS}."
        )

    # ---- 6. direction ----
    direction = _get("direction")
    if direction not in VALID_CORRELATION_DIRECTIONS:
        raise ValueError(
            f"Row {index}: invalid direction '{direction}'. "
            f"Must be one of {VALID_CORRELATION_DIRECTIONS}."
        )

    # ---- 7. p_value: nullable, but in [0, 1] when set ----
    p_value = _get("p_value")
    if p_value is not None:
        if not math.isfinite(p_value):
            raise ValueError(
                f"Row {index}: p_value must be finite when set, "
                f"got {p_value!r}"
            )
        if p_value < 0.0 or p_value > 1.0:
            raise ValueError(
                f"Row {index}: p_value must be in [0, 1], "
                f"got {p_value}"
            )


def validate_correlation_rows(
    rows: Iterable[Any],
) -> None:
    """Validate a batch of btc_macro_correlation rows.

    Fails on the first invalid row and includes its index in the
    error message. Returns None on success.

    Args:
        rows: An iterable of correlation rows (objects or dicts).

    Raises:
        ValueError: If any row is invalid.
    """
    for i, row in enumerate(rows):
        validate_correlation_row(row, index=i)

    logger.debug("All correlation rows passed validation")