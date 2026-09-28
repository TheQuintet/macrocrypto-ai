import numpy as np
import pandas as pd
import pytest

from app.ai.metrics import (
    current_prices_for_target_dates,
    directional_accuracy,
)


def test_current_price_comes_from_preceding_next_day_target() -> None:
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    data = pd.DataFrame(
        {
            "ds": dates,
            "y": [11.0, 12.0, 13.0, 14.0],
        }
    )

    current = current_prices_for_target_dates(data, dates[1:])

    np.testing.assert_array_equal(current, [11.0, 12.0, 13.0])


def test_current_prices_require_contiguous_prior_target_dates() -> None:
    data = pd.DataFrame(
        {
            "ds": pd.to_datetime(["2024-01-01", "2024-01-03"]),
            "y": [11.0, 13.0],
        }
    )

    with pytest.raises(ValueError, match="Cannot derive current BTC prices"):
        current_prices_for_target_dates(data, [pd.Timestamp("2024-01-03")])


def test_directional_accuracy_compares_each_forecast_to_current_price() -> None:
    actual = np.array([110.0, 90.0, 100.0])
    predicted = np.array([120.0, 95.0, 100.0])
    current = np.array([100.0, 100.0, 100.0])

    assert directional_accuracy(actual, predicted, current) == pytest.approx(
        100.0
    )


def test_persistence_baseline_is_neutral_for_moving_prices() -> None:
    actual = np.array([110.0, 90.0])
    current = np.array([100.0, 100.0])

    assert directional_accuracy(actual, current, current) == 0.0
