"""Correlation analysis package.

Provides the calculation logic for BTC-vs-macro correlations (A1).

Public API:
    - CorrelationCalculator: orchestrates fetch, compute, and persist
    - CalculationResult: structured result of one calculation run
    - pearson_correlation: pure Pearson correlation on two series
    - classify_strength: label a coefficient as strong/medium/weak
    - classify_direction: label a coefficient as positive/negative
    - strength_color: translate a strength label to a display color
    - direction_arrow: translate a direction label to a display arrow
    - INDICATOR_SOURCE_COLUMNS: mapping of indicator label → source
      column name (or None when the source has no data for it yet)
"""

from app.correlation.calculator import (
    INDICATOR_SOURCE_COLUMNS,
    WINDOWS,
    CalculationResult,
    CorrelationCalculator,
    classify_direction,
    classify_strength,
    direction_arrow,
    pearson_correlation,
    strength_color,
)

__all__ = [
    "INDICATOR_SOURCE_COLUMNS",
    "WINDOWS",
    "CalculationResult",
    "CorrelationCalculator",
    "classify_direction",
    "classify_strength",
    "direction_arrow",
    "pearson_correlation",
    "strength_color",
]