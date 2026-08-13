"""
Unit tests for the macroeconomic regime classification engine.

Sprint 4 - A3.15
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.regime_service import RegimeService


def make_indicator(
    indicator_name,
    value,
    time,
    change_percent=None,
):
    """Create a lightweight indicator object for unit tests."""

    return SimpleNamespace(
        indicator_name=indicator_name,
        value=value,
        time=time,
        change_percent=change_percent,
    )


def utc_date(year, month, day=1):
    """Create a timezone-aware datetime."""

    return datetime(
        year,
        month,
        day,
        tzinfo=timezone.utc,
    )


@pytest.fixture
def service():
    """
    Create RegimeService without requiring a database connection.

    determine_regime() only requires the service instance.
    """

    return RegimeService(None)


# ==========================================================
# HIGH INFLATION
# ==========================================================


def test_high_inflation_classification(service):
    """
    CPI YoY > 3% must classify as high inflation.
    """

    indicators = [
        make_indicator(
            "cpi",
            332.568,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            320.0,
            utc_date(2025, 6, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "high_inflation"


# ==========================================================
# LOW INFLATION
# ==========================================================


def test_low_inflation_classification(service):
    """
    CPI YoY < 2% must classify as low inflation.
    """

    indicators = [
        make_indicator(
            "cpi",
            325.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            320.0,
            utc_date(2025, 6, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "low_inflation"


# ==========================================================
# RISING RATES
# ==========================================================


def test_rising_rates_classification(service):
    """
    Interest rates increasing over approximately 3 months
    must classify as rising rates.
    """

    indicators = [
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            4.5,
            utc_date(2026, 4, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "rising_rates"


# ==========================================================
# FALLING RATES
# ==========================================================


def test_falling_rates_classification(service):
    """
    Interest rates decreasing over approximately 3 months
    must classify as falling rates.
    """

    indicators = [
        make_indicator(
            "federal_funds_rate",
            4.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            4.5,
            utc_date(2026, 4, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "falling_rates"


# ==========================================================
# RECESSION
# ==========================================================


def test_recession_classification(service):
    """
    Two consecutive quarters of negative GDP growth
    must classify as recession.
    """

    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=-0.5,
        ),
        make_indicator(
            "gdp",
            100.5,
            utc_date(2026, 1, 1),
            change_percent=-0.3,
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "recession"


# ==========================================================
# GROWTH
# ==========================================================


def test_growth_classification(service):
    """
    GDP growth > 2% must classify as growth when
    higher-priority conditions are not present.
    """

    indicators = [
        make_indicator(
            "gdp",
            105.0,
            utc_date(2026, 4, 1),
            change_percent=2.5,
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "growth"


# ==========================================================
# OVERLAPPING REGIMES
# ==========================================================


def test_recession_takes_priority_over_high_inflation(
    service,
):
    """
    When recession and high inflation conditions overlap,
    recession takes priority.
    """

    indicators = [
        make_indicator(
            "cpi",
            332.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            320.0,
            utc_date(2025, 6, 1),
        ),
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=-0.5,
        ),
        make_indicator(
            "gdp",
            100.5,
            utc_date(2026, 1, 1),
            change_percent=-0.3,
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "recession"


def test_high_inflation_takes_priority_over_rising_rates(
    service,
):
    """
    When high inflation and rising rates overlap,
    high inflation takes priority.
    """

    indicators = [
        make_indicator(
            "cpi",
            332.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            320.0,
            utc_date(2025, 6, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            4.5,
            utc_date(2026, 4, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "high_inflation"


# ==========================================================
# DATA VALIDATION / EDGE CASES
# ==========================================================


def test_empty_indicators_default_to_growth(service):
    """
    Missing indicators must not cause an exception.
    """

    result = service.determine_regime([])

    assert result == "growth"


def test_missing_cpi_data_does_not_fail(service):
    """
    Missing CPI data must not cause classification failure.
    """

    indicators = [
        make_indicator(
            "gdp",
            105.0,
            utc_date(2026, 4, 1),
            change_percent=2.5,
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "growth"


def test_missing_rate_history_does_not_fail(service):
    """
    A single interest-rate observation is insufficient
    for the 3-month rate comparison.
    """

    indicators = [
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 7, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "growth"


def test_missing_gdp_history_does_not_create_recession(
    service,
):
    """
    One negative GDP quarter must not classify as recession.
    """

    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=-0.5,
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "growth"


def test_cpi_exactly_three_percent_is_not_high_inflation(
    service,
):
    """
    Acceptance criterion is CPI > 3%, not >= 3%.
    """

    indicators = [
        make_indicator(
            "cpi",
            309.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result != "high_inflation"


def test_cpi_exactly_two_percent_is_not_low_inflation(
    service,
):
    """
    Acceptance criterion is CPI < 2%, not <= 2%.
    """

    indicators = [
        make_indicator(
            "cpi",
            306.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    result = service.determine_regime(indicators)

    assert result != "low_inflation"


def test_invalid_indicator_values_do_not_raise(
    service,
):
    """
    None values must be safely ignored by classification.
    """

    indicators = [
        make_indicator(
            "cpi",
            None,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            None,
            utc_date(2025, 6, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            None,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "gdp",
            None,
            utc_date(2026, 4, 1),
            change_percent=None,
        ),
    ]

    result = service.determine_regime(indicators)

    assert result == "growth"


def test_result_is_valid_regime(service):
    """
    Classification must always return one of the supported
    regime types.
    """

    result = service.determine_regime([])

    assert result in service.VALID_REGIMES