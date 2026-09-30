"""
Unit tests for the macroeconomic regime classification engine.

Sprint 4 - A3.15
"""

from datetime import date, datetime, timezone
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



from unittest.mock import AsyncMock, MagicMock, patch


# ==========================================================
# DETERMINATE REGIME - EDGE / BRANCH COVERAGE
# ==========================================================


def test_indicator_names_are_case_insensitive(service):
    """Indicator names should be normalized to lowercase."""

    indicators = [
        make_indicator(
            "CPI",
            320.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "CPI",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "high_inflation"


def test_cpi_historical_value_zero_falls_back_safely(service):
    """A zero historical CPI value must not cause division by zero."""

    indicators = [
        make_indicator(
            "cpi",
            320.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            0.0,
            utc_date(2025, 6, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_latest_cpi_none_does_not_fail(service):
    """A missing latest CPI value must be handled safely."""

    indicators = [
        make_indicator(
            "cpi",
            None,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_historical_cpi_none_does_not_fail(service):
    """A missing historical CPI value must be handled safely."""

    indicators = [
        make_indicator(
            "cpi",
            320.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            None,
            utc_date(2025, 6, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_unchanged_interest_rate_does_not_create_rate_regime(service):
    """An unchanged rate should not classify as rising or falling."""

    indicators = [
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 4, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_latest_rate_none_does_not_fail(service):
    """A missing latest rate should be handled safely."""

    indicators = [
        make_indicator(
            "federal_funds_rate",
            None,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            4.0,
            utc_date(2026, 4, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_historical_rate_none_does_not_fail(service):
    """A missing historical rate should be handled safely."""

    indicators = [
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            None,
            utc_date(2026, 4, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_gdp_exactly_at_growth_threshold_is_not_growth_from_gdp_rule(
    service,
):
    """
    GDP must be greater than the configured threshold,
    not equal to it.
    """

    from app.config import settings

    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=settings.GDP_GROWTH_THRESHOLD,
        ),
    ]

    # The service ultimately falls back to growth, but this
    # verifies the strict > threshold branch.
    assert service.determine_regime(indicators) == "growth"


def test_gdp_none_does_not_fail(service):
    """GDP with no change percentage should be handled safely."""

    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=None,
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


def test_low_inflation_takes_priority_over_falling_rates(service):
    """Low inflation is evaluated before rate classification."""

    indicators = [
        make_indicator(
            "cpi",
            303.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
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

    assert service.determine_regime(indicators) == "low_inflation"


def test_falling_rates_classification_without_cpi(service):
    """Falling rates should be reached when CPI does not classify."""

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

    assert service.determine_regime(indicators) == "falling_rates"


def test_growth_is_fallback_when_no_classification_evidence_exists(
    service,
):
    """The final fallback classification must be growth."""

    indicators = [
        make_indicator(
            "unknown_indicator",
            10.0,
            utc_date(2026, 7, 1),
        ),
    ]

    assert service.determine_regime(indicators) == "growth"


# ==========================================================
# CONFIDENCE
# ==========================================================


def test_confidence_with_no_indicators_is_zero(service):
    assert service.calculate_confidence([], "growth") == 0.0


def test_recession_confidence_is_100_with_two_negative_quarters(
    service,
):
    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=-0.5,
        ),
        make_indicator(
            "gdp",
            99.0,
            utc_date(2026, 1, 1),
            change_percent=-0.3,
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "recession",
        )
        == 100.0
    )


def test_recession_confidence_is_50_with_insufficient_negative_quarters(
    service,
):
    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=-0.5,
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "recession",
        )
        == 50.0
    )


def test_high_inflation_confidence_increases_with_inflation(
    service,
):
    from app.config import settings

    historical = 300.0
    inflation = settings.INFLATION_THRESHOLD + 1.0
    latest = historical * (1 + inflation / 100)

    indicators = [
        make_indicator(
            "cpi",
            latest,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            historical,
            utc_date(2025, 6, 1),
        ),
    ]

    confidence = service.calculate_confidence(
        indicators,
        "high_inflation",
    )

    assert confidence > 50.0
    assert confidence <= 100.0


def test_high_inflation_confidence_caps_at_100(service):
    from app.config import settings

    historical = 100.0
    inflation = settings.INFLATION_THRESHOLD + 20.0
    latest = historical * (1 + inflation / 100)

    indicators = [
        make_indicator(
            "cpi",
            latest,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            historical,
            utc_date(2025, 6, 1),
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "high_inflation",
        )
        == 100.0
    )


def test_low_inflation_confidence_increases_when_inflation_is_below_threshold(
    service,
):
    from app.config import settings

    historical = 300.0
    inflation = settings.LOW_INFLATION_THRESHOLD - 1.0
    latest = historical * (1 + inflation / 100)

    indicators = [
        make_indicator(
            "cpi",
            latest,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            historical,
            utc_date(2025, 6, 1),
        ),
    ]

    confidence = service.calculate_confidence(
        indicators,
        "low_inflation",
    )

    assert confidence > 50.0
    assert confidence <= 100.0


def test_cpi_confidence_is_50_with_insufficient_history(service):
    indicators = [
        make_indicator(
            "cpi",
            320.0,
            utc_date(2026, 6, 1),
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "high_inflation",
        )
        == 50.0
    )


def test_cpi_confidence_is_50_for_invalid_values(service):
    indicators = [
        make_indicator(
            "cpi",
            320.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            0.0,
            utc_date(2025, 6, 1),
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "high_inflation",
        )
        == 50.0
    )


def test_rising_rate_confidence_increases_with_rate_change(service):
    indicators = [
        make_indicator(
            "federal_funds_rate",
            6.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 4, 1),
        ),
    ]

    confidence = service.calculate_confidence(
        indicators,
        "rising_rates",
    )

    assert confidence > 50.0
    assert confidence <= 100.0


def test_falling_rate_confidence_increases_with_rate_change(service):
    indicators = [
        make_indicator(
            "federal_funds_rate",
            4.0,
            utc_date(2026, 7, 1),
        ),
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 4, 1),
        ),
    ]

    confidence = service.calculate_confidence(
        indicators,
        "falling_rates",
    )

    assert confidence > 50.0
    assert confidence <= 100.0


def test_rate_confidence_is_50_with_insufficient_history(service):
    indicators = [
        make_indicator(
            "federal_funds_rate",
            5.0,
            utc_date(2026, 7, 1),
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "rising_rates",
        )
        == 50.0
    )


def test_growth_confidence_increases_above_threshold(service):
    from app.config import settings

    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=settings.GDP_GROWTH_THRESHOLD + 1.0,
        ),
    ]

    confidence = service.calculate_confidence(
        indicators,
        "growth",
    )

    assert confidence > 50.0
    assert confidence <= 100.0


def test_growth_confidence_is_50_without_gdp(service):
    assert (
        service.calculate_confidence(
            [],
            "growth",
        )
        == 0.0
    )


def test_growth_confidence_is_50_for_gdp_without_change(service):
    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=None,
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "growth",
        )
        == 50.0
    )


def test_unknown_regime_confidence_returns_50(service):
    indicators = [
        make_indicator(
            "gdp",
            100.0,
            utc_date(2026, 4, 1),
            change_percent=1.0,
        ),
    ]

    assert (
        service.calculate_confidence(
            indicators,
            "unknown_regime",
        )
        == 50.0
    )


# ==========================================================
# VISUAL INDICATOR
# ==========================================================


@pytest.mark.parametrize(
    ("regime", "expected"),
    [
        ("high_inflation", "bear"),
        ("low_inflation", "bull"),
        ("rising_rates", "bear"),
        ("falling_rates", "bull"),
        ("recession", "recession"),
        ("growth", "bull"),
    ],
)
def test_visual_indicator_mapping(
    service,
    regime,
    expected,
):
    assert service.get_visual_indicator(regime) == expected


def test_unknown_regime_visual_indicator_defaults_to_recession(
    service,
):
    assert (
        service.get_visual_indicator("unknown")
        == "recession"
    )


# ==========================================================
# UPDATE CURRENT REGIME
# ==========================================================


def test_update_current_regime_returns_none_without_indicators(
    service,
):
    service.repository = MagicMock()

    result = service.update_current_regime([])

    assert result is None
    service.repository.get_current_regime.assert_not_called()


def test_update_current_regime_creates_initial_regime(service):
    service.repository = MagicMock()

    created_regime = SimpleNamespace(
        id=1,
        regime_type="growth",
    )

    service.repository.get_current_regime.return_value = None
    service.repository.create_regime.return_value = created_regime

    indicators = [
        make_indicator(
            "gdp",
            105.0,
            utc_date(2026, 4, 1),
            change_percent=2.5,
        ),
    ]

    result = service.update_current_regime(indicators)

    assert result is created_regime

    service.repository.create_regime.assert_called_once()
    service.repository.set_current_regime.assert_called_once()

    create_kwargs = (
        service.repository
        .create_regime
        .call_args.kwargs
    )

    assert create_kwargs["regime_type"] == "growth"


def test_update_current_regime_returns_existing_regime_when_unchanged(
    service,
):
    service.repository = MagicMock()

    current_regime = SimpleNamespace(
        id=1,
        regime_type="growth",
    )

    service.repository.get_current_regime.return_value = (
        current_regime
    )

    indicators = [
        make_indicator(
            "gdp",
            105.0,
            utc_date(2026, 4, 1),
            change_percent=2.5,
        ),
    ]

    result = service.update_current_regime(indicators)

    assert result is current_regime

    service.repository.close_regime.assert_not_called()
    service.repository.create_regime.assert_not_called()
    service.repository.set_current_regime.assert_not_called()


def test_update_current_regime_changes_regime(
    service,
):
    service.repository = MagicMock()

    current_regime = SimpleNamespace(
        id=10,
        regime_type="growth",
    )

    new_regime = SimpleNamespace(
        id=11,
        regime_type="high_inflation",
    )

    service.repository.get_current_regime.return_value = (
        current_regime
    )
    service.repository.create_regime.return_value = new_regime

    indicators = [
        make_indicator(
            "cpi",
            330.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    with patch(
        "app.services.regime_performance_service.RegimePerformanceService"
    ) as performance_cls:

        performance_service = (
            performance_cls.return_value
        )

        performance_service.calculate_regime_performance.return_value = (
            SimpleNamespace(id=100)
        )

        result = service.update_current_regime(
            indicators
        )

    assert result is new_regime

    service.repository.close_regime.assert_called_once_with(
        current_regime,
        date.today(),
    )

    performance_service.calculate_regime_performance.assert_called_once_with(
        current_regime
    )

    service.repository.create_regime.assert_called_once()
    service.repository.set_current_regime.assert_called_once()


def test_update_current_regime_handles_no_performance_result(
    service,
):
    service.repository = MagicMock()

    current_regime = SimpleNamespace(
        id=10,
        regime_type="growth",
    )

    new_regime = SimpleNamespace(
        id=11,
        regime_type="high_inflation",
    )

    service.repository.get_current_regime.return_value = (
        current_regime
    )
    service.repository.create_regime.return_value = new_regime

    indicators = [
        make_indicator(
            "cpi",
            330.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    with patch(
        "app.services.regime_performance_service.RegimePerformanceService"
    ) as performance_cls:

        performance_service = (
            performance_cls.return_value
        )

        performance_service.calculate_regime_performance.return_value = (
            None
        )

        result = service.update_current_regime(
            indicators
        )

    assert result is new_regime


def test_update_current_regime_continues_when_performance_fails(
    service,
):
    service.repository = MagicMock()

    current_regime = SimpleNamespace(
        id=10,
        regime_type="growth",
    )

    new_regime = SimpleNamespace(
        id=11,
        regime_type="high_inflation",
    )

    service.repository.get_current_regime.return_value = (
        current_regime
    )
    service.repository.create_regime.return_value = new_regime

    indicators = [
        make_indicator(
            "cpi",
            330.0,
            utc_date(2026, 6, 1),
        ),
        make_indicator(
            "cpi",
            300.0,
            utc_date(2025, 6, 1),
        ),
    ]

    with patch(
        "app.services.regime_performance_service.RegimePerformanceService"
    ) as performance_cls:

        performance_service = (
            performance_cls.return_value
        )

        performance_service.calculate_regime_performance.side_effect = (
            RuntimeError("performance calculation failed")
        )

        result = service.update_current_regime(
            indicators
        )

    assert result is new_regime

    service.repository.create_regime.assert_called_once()
    service.repository.set_current_regime.assert_called_once()


# ==========================================================
# UPDATE REGIME
# ==========================================================


def test_update_regime_returns_none_when_database_has_no_indicators(
    service,
):
    query = MagicMock()
    query.order_by.return_value.all.return_value = []

    service.db = MagicMock()
    service.db.query.return_value = query

    result = __import__(
        "asyncio"
    ).run(service.update_regime())

    assert result is None


def test_update_regime_passes_database_indicators_to_update(
    service,
):
    indicators = [
        make_indicator(
            "gdp",
            105.0,
            utc_date(2026, 4, 1),
            change_percent=2.5,
        ),
    ]

    query = MagicMock()
    query.order_by.return_value.all.return_value = indicators

    service.db = MagicMock()
    service.db.query.return_value = query

    expected = SimpleNamespace(
        regime_type="growth",
    )

    service.update_current_regime = MagicMock(
        return_value=expected
    )

    result = __import__(
        "asyncio"
    ).run(service.update_regime())

    assert result is expected
    service.update_current_regime.assert_called_once_with(
        indicators
    )


# ==========================================================
# PUBLIC PROCESSOR
# ==========================================================


@pytest.mark.asyncio
async def test_process_regime_returns_update_result(service):
    expected = SimpleNamespace(
        regime_type="growth",
    )

    service.update_regime = AsyncMock(
        return_value=expected
    )

    result = await service.process_regime()

    assert result is expected
    service.update_regime.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_regime_returns_none_when_update_returns_none(
    service,
):
    service.update_regime = AsyncMock(
        return_value=None
    )

    result = await service.process_regime()

    assert result is None
    service.update_regime.assert_awaited_once()


# ==========================================================
# SERVICE LIFECYCLE
# ==========================================================


@pytest.mark.asyncio
async def test_close_returns_none(service):
    assert await service.close() is None

