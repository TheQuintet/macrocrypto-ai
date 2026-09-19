"""Validators for AI Service database writes.

This module provides validation functions that enforce invariants
on data before it hits the database. Validators raise `ValueError`
with clear messages so callers can surface actionable errors.

Validators are called by repositories before INSERT / UPDATE, so
any caller (generator, scheduler, ad-hoc scripts) benefits from
the same checks.

Currently validates:
    - Prediction rows: bounds ordering, finiteness, enum membership
"""

import logging
import math
from typing import Iterable

from app.database.repositories.prediction_repository import PredictionRow

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
VALID_HORIZONS = ("24h", "7d")
VALID_CONFIDENCE_LEVELS = (0.70, 0.85, 0.95)


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