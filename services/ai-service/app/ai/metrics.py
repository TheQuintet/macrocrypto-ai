"""Shared metric helpers for next-day forecasting models."""

from typing import Sequence

import numpy as np
import pandas as pd


def current_prices_for_target_dates(
    data: pd.DataFrame,
    target_dates: Sequence[pd.Timestamp],
    *,
    strict: bool = True,
) -> np.ndarray:
    """Look up day-t prices from the prior row's next-day target."""
    required = {"ds", "y"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(
            f"Target data is missing required columns: {sorted(missing)}"
        )

    dates = pd.to_datetime(data["ds"])
    if dates.dt.tz is not None:
        dates = dates.dt.tz_localize(None)
    targets = pd.Series(
        data["y"].to_numpy(dtype=float),
        index=dates + pd.Timedelta(days=1),
    )
    if targets.index.duplicated().any():
        raise ValueError("Target data contains duplicate dates")

    requested_dates = pd.DatetimeIndex(pd.to_datetime(target_dates))
    if requested_dates.tz is not None:
        requested_dates = requested_dates.tz_localize(None)
    current_prices = targets.reindex(requested_dates).to_numpy(dtype=float)
    if strict and not np.isfinite(current_prices).all():
        missing_dates = requested_dates[~np.isfinite(current_prices)]
        raise ValueError(
            "Cannot derive current BTC prices from preceding next-day "
            f"targets for dates: {list(missing_dates[:5])}"
        )
    return current_prices


def directional_accuracy(
    actual: np.ndarray,
    predicted: np.ndarray,
    current_price: np.ndarray,
) -> float:
    """Measure correct next-day movement direction from each day's price."""
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    current_price = np.asarray(current_price, dtype=float)

    if not (actual.shape == predicted.shape == current_price.shape):
        raise ValueError(
            "Actual, predicted, and current-price arrays must have "
            "matching shapes"
        )
    if actual.size == 0:
        return 0.0
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Actual and predicted values must be finite")

    valid = np.isfinite(current_price)
    if not valid.any():
        return 0.0
    correct = np.sign(predicted[valid] - current_price[valid]) == np.sign(
        actual[valid] - current_price[valid]
    )
    return float(np.mean(correct) * 100)
