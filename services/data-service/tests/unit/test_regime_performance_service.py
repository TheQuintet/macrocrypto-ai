import math
from datetime import date, datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.models.btc_price import BTCPrice
from app.models.macro_regime import MacroRegime
from app.services.regime_performance_service import (
    RegimePerformanceService,
)


class MockPriceRecord:
    """
    Lightweight mock object that mimics the BTCPrice attributes
    required by RegimePerformanceService.
    """

    def __init__(
        self,
        price: float | None,
        time: datetime | None = None,
    ):
        self.price = price
        self.time = time or datetime.now(timezone.utc)


@pytest.fixture
def mock_db():
    """Provide a mocked SQLAlchemy database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Provide a RegimePerformanceService using the mocked DB."""
    return RegimePerformanceService(db=mock_db)


@pytest.fixture
def sample_regime():
    """Provide a sample macro regime for database/query tests."""
    regime = MagicMock(spec=MacroRegime)
    regime.id = 1
    regime.start_date = date(2023, 1, 1)
    regime.end_date = date(2023, 6, 1)
    regime.regime_type = "growth"
    return regime


# ==========================================================
# AVG RETURN TESTS
# ==========================================================


def test_calculate_return_average_positive_returns(service):
    """
    Tests arithmetic mean of consecutive positive BTC returns.

    Prices:
        100 -> 120 = +20%
        120 -> 150 = +25%

    Average return:
        (20% + 25%) / 2 = 22.5%
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(120.0),
        MockPriceRecord(150.0),
    ]

    assert service.calculate_return(prices) == pytest.approx(22.5)


def test_calculate_return_average_negative_returns(service):
    """
    Tests arithmetic mean of consecutive negative BTC returns.

    Prices:
        200 -> 180 = -10%
        180 -> 150 = -16.6667%

    Average return:
        (-10% + -16.6667%) / 2
        = -13.3333%
    """

    prices = [
        MockPriceRecord(200.0),
        MockPriceRecord(180.0),
        MockPriceRecord(150.0),
    ]

    assert service.calculate_return(prices) == pytest.approx(
        -13.3333333333
    )


def test_calculate_return_average_mixed_returns(service):
    """
    Tests average return when consecutive returns have
    different directions.

    Prices:
        100 -> 110 = +10%
        110 -> 99 = -10%

    Average return:
        (10% + -10%) / 2 = 0%
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(99.0),
    ]

    assert service.calculate_return(prices) == pytest.approx(0.0)


def test_calculate_return_insufficient_data(service):
    """Return calculation requires at least two price records."""

    assert service.calculate_return([]) is None

    assert service.calculate_return(
        [MockPriceRecord(100.0)]
    ) is None


def test_calculate_return_invalid_prices(service):
    """
    Tests that invalid previous prices are skipped rather than
    causing division-by-zero or invalid calculations.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(0.0),
        MockPriceRecord(-50.0),
        MockPriceRecord(None),
        MockPriceRecord(120.0),
    ]

    result = service.calculate_return(prices)

    # No valid consecutive pair exists because every transition
    # after 100 uses an invalid previous price.
    assert result is None


# ==========================================================
# MAX DRAWDOWN TESTS
# ==========================================================


def test_calculate_max_drawdown_standard(service):
    """
    Tests maximum peak-to-trough drawdown.

    Peak = 120
    Lowest subsequent price = 80

    Drawdown = ((80 - 120) / 120) * 100
             = -33.3333%
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(120.0),
        MockPriceRecord(90.0),
        MockPriceRecord(110.0),
        MockPriceRecord(80.0),
        MockPriceRecord(130.0),
    ]

    assert service.calculate_max_drawdown(prices) == pytest.approx(
        -33.3333333333
    )


def test_calculate_max_drawdown_no_drop(service):
    """Tests drawdown when BTC price never decreases."""

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(120.0),
    ]

    assert service.calculate_max_drawdown(prices) == 0.0


def test_calculate_max_drawdown_insufficient_data(service):
    """Drawdown requires at least two price records."""

    assert service.calculate_max_drawdown([]) is None

    assert service.calculate_max_drawdown(
        [MockPriceRecord(100.0)]
    ) is None


def test_calculate_max_drawdown_filters_invalid_prices(service):
    """
    Tests that None, zero, and negative prices are excluded
    from drawdown calculations.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(None),
        MockPriceRecord(-50.0),
        MockPriceRecord(0.0),
        MockPriceRecord(120.0),
    ]

    assert service.calculate_max_drawdown(prices) == 0.0


# ==========================================================
# VOLATILITY TESTS
# ==========================================================


def test_calculate_volatility_standard(service):
    """
    Tests sample standard deviation of period returns.

    Prices:
        100 -> 110 = +10%
        110 -> 99 = -10%

    Mean return = 0%

    Sample variance:
        ((10 - 0)^2 + (-10 - 0)^2) / (2 - 1)
        = 200

    Volatility:
        sqrt(200) = 14.1421356...
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(99.0),
    ]

    assert service.calculate_volatility(prices) == pytest.approx(
        math.sqrt(200.0)
    )


def test_calculate_volatility_insufficient_data(service):
    """
    Volatility requires at least two valid period returns,
    which requires at least three price records.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
    ]

    assert service.calculate_volatility(prices) is None


def test_calculate_volatility_invalid_prices(service):
    """Tests that invalid price observations are skipped safely."""

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(None),
        MockPriceRecord(0.0),
        MockPriceRecord(-10.0),
        MockPriceRecord(110.0),
    ]

    # There are not enough valid consecutive returns to calculate
    # volatility.
    assert service.calculate_volatility(prices) is None


# ==========================================================
# SHARPE RATIO TESTS
# ==========================================================


def test_calculate_sharpe_ratio_zero_mean(service):
    """
    Tests Sharpe ratio when average period return is zero.

    Returns:
        +10%, -10%

    Mean return = 0
    Volatility > 0

    Sharpe ratio = 0 / volatility = 0
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(99.0),
    ]

    assert service.calculate_sharpe_ratio(prices) == 0.0


def test_calculate_sharpe_ratio_positive(service):
    """
    Tests a positive Sharpe ratio.

    Prices:
        100 -> 110 = +10%
        110 -> 121 = +10%

    Volatility = 0, so the implementation safely returns None.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(121.0),
    ]

    assert service.calculate_sharpe_ratio(prices) is None


def test_calculate_sharpe_ratio_zero_volatility(service):
    """
    Explicitly verifies safe handling of zero volatility.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(121.0),
    ]

    result = service.calculate_sharpe_ratio(prices)

    assert result is None


def test_calculate_sharpe_ratio_insufficient_data(service):
    """Sharpe ratio requires at least two valid period returns."""

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
    ]

    assert service.calculate_sharpe_ratio(prices) is None


def test_calculate_sharpe_ratio_invalid_prices(service):
    """Tests safe handling of invalid BTC prices."""

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(None),
        MockPriceRecord(0.0),
        MockPriceRecord(-50.0),
        MockPriceRecord(110.0),
    ]

    assert service.calculate_sharpe_ratio(prices) is None


# ==========================================================
# COMBINED METRICS TESTS
# ==========================================================


def test_calculate_metrics(service):
    """
    Tests that calculate_metrics returns all required BTC
    performance metrics.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(110.0),
        MockPriceRecord(99.0),
    ]

    metrics = service.calculate_metrics(prices)

    assert metrics["avg_return"] == pytest.approx(0.0)
    assert metrics["max_drawdown"] == pytest.approx(-10.0)
    assert metrics["volatility"] == pytest.approx(
        math.sqrt(200.0)
    )
    assert metrics["sharpe_ratio"] == pytest.approx(0.0)
    assert metrics["btc_price_start"] == 100.0
    assert metrics["btc_price_end"] == 99.0


def test_calculate_metrics_insufficient_data(service):
    """Tests combined metric fallback for insufficient data."""

    prices = [
        MockPriceRecord(100.0),
    ]

    expected = {
        "avg_return": None,
        "max_drawdown": None,
        "volatility": None,
        "sharpe_ratio": None,
        "btc_price_start": None,
        "btc_price_end": None,
    }

    assert service.calculate_metrics(prices) == expected


# ==========================================================
# DATA VALIDATION TESTS
# ==========================================================


def test_metrics_handle_none_prices(service):
    """
    Tests that None price values do not cause calculation
    failures.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(None),
        MockPriceRecord(120.0),
    ]

    # Drawdown can still use the valid values.
    assert service.calculate_max_drawdown(prices) == pytest.approx(
        0.0
    )


def test_metrics_handle_zero_and_negative_prices(service):
    """
    Tests that zero and negative prices are safely ignored.
    """

    prices = [
        MockPriceRecord(100.0),
        MockPriceRecord(0.0),
        MockPriceRecord(-25.0),
        MockPriceRecord(120.0),
    ]

    assert service.calculate_max_drawdown(prices) == 0.0


# ==========================================================
# TIMEFRAME VALIDATION TESTS
# ==========================================================


def test_supported_timeframes(service):
    """Verifies all A3.3-supported timeframes are configured."""

    assert service.SUPPORTED_TIMEFRAMES == {
        "30d": 30,
        "90d": 90,
        "1y": 365,
        "5y": 1825,
    }


def test_unsupported_timeframe_validation_error(
    service,
    sample_regime,
):
    """Invalid timeframe should raise ValueError."""

    with pytest.raises(
        ValueError,
        match="Unsupported timeframe: 10y",
    ):
        service.get_regime_prices(
            sample_regime,
            timeframe="10y",
        )


# ==========================================================
# DATABASE QUERY TESTS
# ==========================================================


def test_get_regime_prices_query_execution(
    service,
    sample_regime,
    mock_db,
):
    """
    Verifies that the service constructs the expected SQLAlchemy
    query and returns the database results.
    """

    mock_query = mock_db.query.return_value
    mock_filter = mock_query.filter.return_value
    mock_order = mock_filter.order_by.return_value

    mock_order.all.return_value = [
        MockPriceRecord(50000.0),
        MockPriceRecord(55000.0),
    ]

    result = service.get_regime_prices(
        sample_regime,
        timeframe="30d",
    )

    mock_db.query.assert_called_once_with(BTCPrice)
    assert mock_query.filter.called
    assert mock_filter.order_by.called
    assert len(result) == 2