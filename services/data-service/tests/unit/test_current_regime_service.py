"""
Unit tests for CurrentRegimeService.

Coverage:
- service initialization
- confidence calculation
- CPI evidence
- interest-rate evidence
- GDP evidence
- multiple evidence sources
- unavailable evidence
- invalid regime handling
- confidence bounds
- visual indicators
- current regime persistence
- current regime processing
- database indicator loading
- empty indicator handling
- service lifecycle
"""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.config import settings
from app.services.current_regime_service import CurrentRegimeService


# ============================================================
# HELPERS
# ============================================================


def make_indicator(
    name,
    value=None,
    change_percent=None,
    time=None,
):
    """
    Create a lightweight indicator object suitable for
    CurrentRegimeService tests.
    """

    if time is None:
        time = datetime.now(timezone.utc)

    return SimpleNamespace(
        indicator_name=name,
        value=value,
        change_percent=change_percent,
        time=time,
    )

def make_service():
    """
    Create CurrentRegimeService with mocked database and downstream services.
    """

    db = MagicMock()

    service = CurrentRegimeService(db)

    service.repository.set_current_regime = MagicMock()
    service.regime_service.determine_regime = MagicMock()

    return service, db
# ============================================================
# INITIALIZATION
# ============================================================


def test_service_initializes_with_database():
    """
    Service should retain the supplied database session.
    """

    db = MagicMock()

    service = CurrentRegimeService(db)

    assert service.db is db
    assert service.repository is not None
    assert service.regime_service is not None


# ============================================================
# CONFIDENCE - BASIC VALIDATION
# ============================================================


def test_calculate_confidence_invalid_regime_raises():
    """
    Invalid regime types should raise ValueError.
    """

    service, _ = make_service()

    with pytest.raises(ValueError, match="Invalid regime type"):
        service.calculate_confidence(
            regime_type="invalid_regime",
            indicators=[],
        )


@pytest.mark.parametrize(
    "regime_type",
    [
        "high_inflation",
        "low_inflation",
        "rising_rates",
        "falling_rates",
        "recession",
        "growth",
    ],
)
def test_calculate_confidence_accepts_valid_regimes(
    regime_type,
):
    """
    All supported regime types should be accepted.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type=regime_type,
        indicators=[],
    )

    assert result == 0.0


def test_calculate_confidence_no_indicators_returns_zero():
    """
    No indicators should result in zero confidence.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[],
    )

    assert result == 0.0


def test_calculate_confidence_none_indicators_returns_zero():
    """
    None indicators should result in zero confidence.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=None,
    )

    assert result == 0.0


# ============================================================
# CPI CONFIDENCE
# ============================================================


def test_high_inflation_cpi_supports_regime():
    """
    CPI inflation above the configured threshold should support
    high_inflation.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    historical = make_indicator(
        "CPI",
        value=100.0,
        time=now - timedelta(days=365),
    )

    latest = make_indicator(
        "CPI",
        value=105.0,
        time=now,
    )

    result = service.calculate_confidence(
        regime_type="high_inflation",
        indicators=[
            historical,
            latest,
        ],
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


def test_high_inflation_cpi_does_not_support_regime():
    """
    CPI inflation below the high-inflation threshold should not
    support high_inflation.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    historical = make_indicator(
        "CPI",
        value=100.0,
        time=now - timedelta(days=365),
    )

    latest = make_indicator(
        "CPI",
        value=101.0,
        time=now,
    )

    result = service.calculate_confidence(
        regime_type="high_inflation",
        indicators=[
            historical,
            latest,
        ],
    )

    assert result == pytest.approx(
        0.0,
        abs=0.01,
    )


def test_low_inflation_cpi_supports_regime():
    """
    CPI inflation below the configured low-inflation threshold
    should support low_inflation.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    historical = make_indicator(
        "CPI",
        value=100.0,
        time=now - timedelta(days=365),
    )

    latest = make_indicator(
        "CPI",
        value=101.0,
        time=now,
    )

    result = service.calculate_confidence(
        regime_type="low_inflation",
        indicators=[
            historical,
            latest,
        ],
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


def test_cpi_without_historical_record_is_not_applicable():
    """
    A single CPI record cannot provide year-over-year evidence.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="high_inflation",
        indicators=[
            make_indicator(
                "CPI",
                value=105.0,
            )
        ],
    )

    assert result == 0.0


def test_cpi_none_latest_value_is_not_applicable():
    """
    Missing latest CPI value should not contribute evidence.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    indicators = [
        make_indicator(
            "CPI",
            value=None,
            time=now,
        ),
        make_indicator(
            "CPI",
            value=100.0,
            time=now - timedelta(days=365),
        ),
    ]

    result = service.calculate_confidence(
        regime_type="high_inflation",
        indicators=indicators,
    )

    assert result == 0.0


def test_cpi_zero_historical_value_is_not_applicable():
    """
    A zero historical CPI value cannot be used for percentage
    change calculation.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    indicators = [
        make_indicator(
            "CPI",
            value=105.0,
            time=now,
        ),
        make_indicator(
            "CPI",
            value=0.0,
            time=now - timedelta(days=365),
        ),
    ]

    result = service.calculate_confidence(
        regime_type="high_inflation",
        indicators=indicators,
    )

    assert result == 0.0


# ============================================================
# INTEREST RATE CONFIDENCE
# ============================================================


def test_rising_rates_supports_regime():
    """
    A positive three-month rate change should support
    rising_rates.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    historical = make_indicator(
        "Federal_Funds_Rate",
        value=4.0,
        time=now - timedelta(days=90),
    )

    latest = make_indicator(
        "Federal_Funds_Rate",
        value=5.0,
        time=now,
    )

    result = service.calculate_confidence(
        regime_type="rising_rates",
        indicators=[
            historical,
            latest,
        ],
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


def test_rising_rates_not_supported_by_falling_rate():
    """
    A negative rate change should not support rising_rates.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    historical = make_indicator(
        "Federal_Funds_Rate",
        value=5.0,
        time=now - timedelta(days=90),
    )

    latest = make_indicator(
        "Federal_Funds_Rate",
        value=4.0,
        time=now,
    )

    result = service.calculate_confidence(
        regime_type="rising_rates",
        indicators=[
            historical,
            latest,
        ],
    )

    assert result == pytest.approx(
        0.0,
        abs=0.01,
    )


def test_falling_rates_supports_regime():
    """
    A negative three-month rate change should support
    falling_rates.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    historical = make_indicator(
        "Federal_Funds_Rate",
        value=5.0,
        time=now - timedelta(days=90),
    )

    latest = make_indicator(
        "Federal_Funds_Rate",
        value=4.0,
        time=now,
    )

    result = service.calculate_confidence(
        regime_type="falling_rates",
        indicators=[
            historical,
            latest,
        ],
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


def test_rate_without_historical_record_is_not_applicable():
    """
    A single rate record cannot establish rate direction.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="rising_rates",
        indicators=[
            make_indicator(
                "Federal_Funds_Rate",
                value=5.0,
            )
        ],
    )

    assert result == 0.0


def test_rate_none_value_is_not_applicable():
    """
    Missing rate values should not contribute evidence.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    indicators = [
        make_indicator(
            "Federal_Funds_Rate",
            value=None,
            time=now,
        ),
        make_indicator(
            "Federal_Funds_Rate",
            value=4.0,
            time=now - timedelta(days=90),
        ),
    ]

    result = service.calculate_confidence(
        regime_type="rising_rates",
        indicators=indicators,
    )

    assert result == 0.0


# ============================================================
# GDP CONFIDENCE
# ============================================================


def test_growth_gdp_supports_regime():
    """
    GDP growth above the configured threshold should support
    growth.
    """

    service, _ = make_service()

    indicator = make_indicator(
        "GDP",
        change_percent=3.0,
    )

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[indicator],
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


def test_growth_gdp_below_threshold_does_not_support_regime():
    """
    GDP growth below the configured threshold should not support
    growth.
    """

    service, _ = make_service()

    indicator = make_indicator(
        "GDP",
        change_percent=1.0,
    )

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[indicator],
    )

    assert result == pytest.approx(
        0.0,
        abs=0.01,
    )


def test_recession_requires_two_negative_gdp_quarters():
    """
    Recession confidence requires at least two negative GDP
    observations among the latest two records.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    indicators = [
        make_indicator(
            "GDP",
            change_percent=-1.0,
            time=now,
        ),
        make_indicator(
            "GDP",
            change_percent=-2.0,
            time=now - timedelta(days=90),
        ),
    ]

    result = service.calculate_confidence(
        regime_type="recession",
        indicators=indicators,
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


def test_recession_not_supported_by_one_negative_quarter():
    """
    One negative GDP observation is insufficient for recession
    confidence.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    indicators = [
        make_indicator(
            "GDP",
            change_percent=-1.0,
            time=now,
        ),
        make_indicator(
            "GDP",
            change_percent=1.0,
            time=now - timedelta(days=90),
        ),
    ]

    result = service.calculate_confidence(
        regime_type="recession",
        indicators=indicators,
    )

    assert result == pytest.approx(
        0.0,
        abs=0.01,
    )


def test_gdp_missing_change_percent_is_not_applicable():
    """
    Missing GDP change_percent should not contribute evidence.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[
            make_indicator(
                "GDP",
                change_percent=None,
            )
        ],
    )

    assert result == 0.0


# ============================================================
# MULTIPLE EVIDENCE SOURCES
# ============================================================


def test_confidence_combines_multiple_supported_evidence_sources():
    """
    Confidence should combine applicable evidence using the
    configured weights.
    """

    service, _ = make_service()

    now = datetime.now(timezone.utc)

    indicators = [
        # CPI: supported
        make_indicator(
            "CPI",
            value=105.0,
            time=now,
        ),
        make_indicator(
            "CPI",
            value=100.0,
            time=now - timedelta(days=365),
        ),

        # Rate: supported
        make_indicator(
            "Federal_Funds_Rate",
            value=5.0,
            time=now,
        ),
        make_indicator(
            "Federal_Funds_Rate",
            value=4.0,
            time=now - timedelta(days=90),
        ),

        # GDP: supported
        make_indicator(
            "GDP",
            change_percent=3.0,
            time=now,
        ),
    ]

    result = service.calculate_confidence(
        regime_type="high_inflation",
        indicators=indicators,
    )

    expected = (
        settings.REGIME_CONFIDENCE_CPI_WEIGHT
        / (
            settings.REGIME_CONFIDENCE_CPI_WEIGHT
            + settings.REGIME_CONFIDENCE_RATE_WEIGHT
            + settings.REGIME_CONFIDENCE_GDP_WEIGHT
        )
    ) * 100

    assert result == pytest.approx(
        round(expected, 2),
        abs=0.01,
    )


def test_confidence_ignores_unrelated_indicators():
    """
    Indicators outside CPI, Federal Funds Rate, and GDP should
    not affect confidence.
    """

    service, _ = make_service()

    indicators = [
        make_indicator(
            "DXY",
            value=100.0,
        ),
        make_indicator(
            "M2",
            value=1000.0,
        ),
        make_indicator(
            "GDP",
            change_percent=3.0,
        ),
    ]

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=indicators,
    )

    assert result == pytest.approx(
        100.0,
        abs=0.01,
    )


# ============================================================
# CONFIDENCE RANGE
# ============================================================


def test_confidence_is_within_zero_to_one_hundred():
    """
    Confidence should always be constrained to 0-100.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[
            make_indicator(
                "GDP",
                change_percent=1000.0,
            )
        ],
    )

    assert 0.0 <= result <= 100.0


def test_confidence_is_rounded_to_two_decimal_places():
    """
    Confidence should be returned with at most two decimal
    places.
    """

    service, _ = make_service()

    result = service.calculate_confidence(
        regime_type="growth",
        indicators=[
            make_indicator(
                "GDP",
                change_percent=2.123456,
            )
        ],
    )

    assert result == round(result, 2)


# ============================================================
# VISUAL INDICATOR
# ============================================================


@pytest.mark.parametrize(
    "regime_type",
    [
        "high_inflation",
        "low_inflation",
        "rising_rates",
        "falling_rates",
        "recession",
        "growth",
    ],
)
def test_get_visual_indicator_valid_regime(
    regime_type,
):
    """
    Every supported regime should return a configured visual
    indicator.
    """

    service, _ = make_service()

    result = service.get_visual_indicator(
        regime_type
    )

    assert isinstance(result, str)
    assert result


def test_get_visual_indicator_invalid_regime_raises():
    """
    Invalid regime types should raise ValueError.
    """

    service, _ = make_service()

    with pytest.raises(ValueError, match="Invalid regime type"):
        service.get_visual_indicator(
            "invalid_regime"
        )


def test_get_visual_indicator_uses_configured_mapping(
    monkeypatch,
):
    """
    The service should use REGIME_VISUAL_INDICATORS from settings.
    """

    service, _ = make_service()

    monkeypatch.setattr(
        settings,
        "REGIME_VISUAL_INDICATORS",
        {
            "growth": "custom_bull",
        },
    )

    result = service.get_visual_indicator(
        "growth"
    )

    assert result == "custom_bull"


def test_get_visual_indicator_defaults_to_neutral(
    monkeypatch,
):
    """
    If a valid regime is missing from the configured mapping,
    neutral should be returned.
    """

    service, _ = make_service()

    monkeypatch.setattr(
        settings,
        "REGIME_VISUAL_INDICATORS",
        {},
    )

    result = service.get_visual_indicator(
        "growth"
    )

    assert result == "neutral"


# ============================================================
# UPDATE CURRENT REGIME
# ============================================================


def test_update_current_regime_persists_snapshot(
    monkeypatch,
):
    """
    update_current_regime() should calculate confidence,
    calculate the visual indicator, and persist the snapshot.
    """

    service, _ = make_service()

    confidence_mock = MagicMock(
        return_value=85.5
    )

    visual_indicator_mock = MagicMock(
        return_value="bull"
    )

    monkeypatch.setattr(
        service,
        "calculate_confidence",
        confidence_mock,
    )

    monkeypatch.setattr(
        service,
        "get_visual_indicator",
        visual_indicator_mock,
    )

    expected = MagicMock()

    service.repository.set_current_regime = MagicMock(
        return_value=expected
    )

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=1
    )

    result = service.update_current_regime(
        regime_type="growth",
        indicators=[],
        expires_at=expires_at,
    )

    assert result is expected

    confidence_mock.assert_called_once_with(
        regime_type="growth",
        indicators=[],
    )

    visual_indicator_mock.assert_called_once_with(
        "growth"
    )

    service.repository.set_current_regime.assert_called_once_with(
        regime_type="growth",
        confidence=85.5,
        visual_indicator="bull",
        expires_at=expires_at,
    )


def test_update_current_regime_invalid_regime_raises():
    """
    update_current_regime() should reject invalid regimes before
    calling downstream methods.
    """

    service, _ = make_service()

    with pytest.raises(ValueError, match="Invalid regime type"):
        service.update_current_regime(
            regime_type="invalid_regime",
            indicators=[],
        )

    service.repository.set_current_regime.assert_not_called()


def test_update_current_regime_accepts_none_expiration():
    """
    expires_at should be optional.
    """

    service, _ = make_service()

    service.calculate_confidence = MagicMock(
        return_value=50.0
    )

    service.get_visual_indicator = MagicMock(
        return_value="neutral"
    )

    service.repository.set_current_regime = MagicMock(
        return_value=MagicMock()
    )

    service.update_current_regime(
        regime_type="growth",
        indicators=[],
        expires_at=None,
    )

    service.repository.set_current_regime.assert_called_once_with(
        regime_type="growth",
        confidence=50.0,
        visual_indicator="neutral",
        expires_at=None,
    )


# ============================================================
# PROCESS CURRENT REGIME
# ============================================================


@pytest.mark.asyncio
async def test_process_current_regime_uses_supplied_indicators():
    """
    Supplied indicators should be used directly rather than
    querying the database.
    """

    service, db = make_service()

    indicators = [
        make_indicator(
            "GDP",
            change_percent=3.0,
        )
    ]

    service.regime_service.determine_regime = MagicMock(
        return_value="growth"
    )

    service.update_current_regime = MagicMock(
        return_value="current-regime"
    )

    result = await service.process_current_regime(
        indicators=indicators
    )

    assert result == "current-regime"

    service.regime_service.determine_regime.assert_called_once_with(
        indicators
    )

    service.update_current_regime.assert_called_once_with(
        regime_type="growth",
        indicators=indicators,
    )

    db.query.assert_not_called()


@pytest.mark.asyncio
async def test_process_current_regime_loads_indicators_from_database():
    """
    When indicators are not supplied, the service should query
    MacroIndicator records ordered newest first.
    """

    service, db = make_service()

    indicators = [
        make_indicator(
            "GDP",
            change_percent=3.0,
        )
    ]

    query = MagicMock()

    query.order_by.return_value = query
    query.all.return_value = indicators

    db.query.return_value = query

    service.regime_service.determine_regime = MagicMock(
        return_value="growth"
    )

    service.update_current_regime = MagicMock(
        return_value="current-regime"
    )

    result = await service.process_current_regime()

    assert result == "current-regime"

    db.query.assert_called_once()

    query.order_by.assert_called_once()
    query.all.assert_called_once()

    service.regime_service.determine_regime.assert_called_once_with(
        indicators
    )

    service.update_current_regime.assert_called_once_with(
        regime_type="growth",
        indicators=indicators,
    )


@pytest.mark.asyncio
async def test_process_current_regime_returns_none_when_database_has_no_indicators():
    """
    No available indicators should result in None.
    """

    service, db = make_service()

    query = MagicMock()

    query.order_by.return_value = query
    query.all.return_value = []

    db.query.return_value = query

    result = await service.process_current_regime()

    assert result is None

    service.regime_service.determine_regime.assert_not_called()
    service.repository.set_current_regime.assert_not_called()


@pytest.mark.asyncio
async def test_process_current_regime_returns_none_when_indicators_are_empty():
    """
    An explicitly supplied empty indicator list should result in
    None.
    """

    service, _ = make_service()

    result = await service.process_current_regime(
        indicators=[]
    )

    assert result is None

    service.regime_service.determine_regime.assert_not_called()
    service.repository.set_current_regime.assert_not_called()


@pytest.mark.asyncio
async def test_process_current_regime_determines_regime_before_update():
    """
    Regime classification should happen before persistence.
    """

    service, _ = make_service()

    indicators = [
        make_indicator(
            "GDP",
            change_percent=3.0,
        )
    ]

    service.regime_service.determine_regime = MagicMock(
        return_value="growth"
    )

    service.update_current_regime = MagicMock(
        return_value="saved"
    )

    result = await service.process_current_regime(
        indicators
    )

    assert result == "saved"

    service.regime_service.determine_regime.assert_called_once_with(
        indicators
    )

    service.update_current_regime.assert_called_once_with(
        regime_type="growth",
        indicators=indicators,
    )


# ============================================================
# SERVICE LIFECYCLE
# ============================================================


@pytest.mark.asyncio
async def test_close_returns_none():
    """
    close() should return None because database lifecycle is
    managed externally.
    """

    service, _ = make_service()

    result = await service.close()

    assert result is None