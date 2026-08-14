"""
Unit tests for CurrentRegimeService.
"""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.current_regime_service import (
    CurrentRegimeService,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_db():
    """
    Mock database session.
    """
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """
    CurrentRegimeService using a mocked database.
    """
    return CurrentRegimeService(mock_db)


def indicator(
    name,
    time,
    value=None,
    change_percent=None,
):
    """
    Create a lightweight mock macro indicator.
    """
    return SimpleNamespace(
        indicator_name=name,
        time=time,
        value=value,
        change_percent=change_percent,
    )


# ============================================================
# VISUAL INDICATOR TESTS
# ============================================================

def test_growth_visual_indicator(service):
    """
    Growth should map to bull.
    """

    result = service.get_visual_indicator(
        "growth"
    )

    assert result == "bull"


def test_high_inflation_visual_indicator(service):
    """
    High inflation should map to bear.
    """

    result = service.get_visual_indicator(
        "high_inflation"
    )

    assert result == "bear"


def test_rising_rates_visual_indicator(service):
    """
    Rising rates should map to bear.
    """

    result = service.get_visual_indicator(
        "rising_rates"
    )

    assert result == "bear"


def test_falling_rates_visual_indicator(service):
    """
    Falling rates should map to bull.
    """

    result = service.get_visual_indicator(
        "falling_rates"
    )

    assert result == "bull"


def test_recession_visual_indicator(service):
    """
    Recession should map to recession.
    """

    result = service.get_visual_indicator(
        "recession"
    )

    assert result == "recession"


def test_invalid_regime_visual_indicator(service):
    """
    Invalid regime types should be rejected.
    """

    with pytest.raises(ValueError):
        service.get_visual_indicator(
            "invalid_regime"
        )


# ============================================================
# CONFIDENCE TESTS
# ============================================================

def test_confidence_returns_zero_without_indicators(
    service,
):
    """
    No indicators should produce zero confidence.
    """

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[],
    )

    assert result == 0.0


def test_confidence_rejects_invalid_regime(
    service,
):
    """
    Invalid regime types should be rejected.
    """

    with pytest.raises(ValueError):
        service.calculate_confidence(
            regime_type="invalid_regime",
            indicators=[],
        )


def test_growth_confidence_with_supporting_gdp(
    service,
):
    """
    GDP supporting growth should produce
    positive confidence.
    """

    indicators = [
        indicator(
            "gdp",
            datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            ),
            change_percent=3.0,
        )
    ]

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=indicators,
    )

    assert result > 0
    assert result <= 100


def test_growth_confidence_with_non_supporting_gdp(
    service,
):
    """
    GDP below the configured growth threshold
    should not support growth.
    """

    indicators = [
        indicator(
            "gdp",
            datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            ),
            change_percent=1.0,
        )
    ]

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=indicators,
    )

    assert result == 0.0


def test_recession_confidence_requires_two_negative_quarters(
    service,
):
    """
    Recession confidence requires two consecutive
    negative GDP quarters.
    """

    indicators = [
        indicator(
            "gdp",
            datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            ),
            change_percent=-1.0,
        ),
        indicator(
            "gdp",
            datetime(
                2026,
                4,
                1,
                tzinfo=timezone.utc,
            ),
            change_percent=-0.5,
        ),
    ]

    result = service.calculate_confidence(
        regime_type="recession",
        indicators=indicators,
    )

    assert result > 0
    assert result <= 100


def test_rising_rates_confidence(
    service,
):
    """
    An increase in federal funds rate over
    the configured three-month period should
    support rising rates.
    """

    indicators = [
        indicator(
            "federal_funds_rate",
            datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            ),
            value=5.5,
        ),
        indicator(
            "federal_funds_rate",
            datetime(
                2026,
                4,
                1,
                tzinfo=timezone.utc,
            ),
            value=5.0,
        ),
    ]

    result = service.calculate_confidence(
        regime_type="rising_rates",
        indicators=indicators,
    )

    assert result > 0
    assert result <= 100


def test_falling_rates_confidence(
    service,
):
    """
    A decrease in federal funds rate over
    the configured three-month period should
    support falling rates.
    """

    indicators = [
        indicator(
            "federal_funds_rate",
            datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            ),
            value=4.5,
        ),
        indicator(
            "federal_funds_rate",
            datetime(
                2026,
                4,
                1,
                tzinfo=timezone.utc,
            ),
            value=5.0,
        ),
    ]

    result = service.calculate_confidence(
        regime_type="falling_rates",
        indicators=indicators,
    )

    assert result > 0
    assert result <= 100


# ============================================================
# UPDATE TESTS
# ============================================================

def test_update_current_regime_persists_result(
    service,
):
    """
    update_current_regime should calculate confidence,
    visual indicator, and persist the current regime.
    """

    expected = SimpleNamespace(
        id=1,
        regime_type="growth",
        confidence=100.0,
        visual_indicator="bull",
    )

    service.repository.set_current_regime = MagicMock(
        return_value=expected
    )

    indicators = [
        indicator(
            "gdp",
            datetime(
                2026,
                7,
                1,
                tzinfo=timezone.utc,
            ),
            change_percent=3.0,
        )
    ]

    result = service.update_current_regime(
        regime_type="growth",
        indicators=indicators,
    )

    assert result == expected

    service.repository.set_current_regime.assert_called_once()

    kwargs = (
        service.repository
        .set_current_regime
        .call_args.kwargs
    )

    assert kwargs["regime_type"] == "growth"
    assert kwargs["confidence"] == 100.0
    assert kwargs["visual_indicator"] == "bull"


def test_update_current_regime_rejects_invalid_regime(
    service,
):
    """
    Invalid regime types should raise ValueError
    and should not attempt to persist the regime.
    """

    with pytest.raises(ValueError):
        service.update_current_regime(
            regime_type="invalid_regime",
            indicators=[],
        )