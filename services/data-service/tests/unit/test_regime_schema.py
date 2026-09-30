"""
Unit tests for regime API response schemas.

Tests cover:
- required fields
- optional fields
- nested response models
- valid data
- date/datetime validation
- numeric validation
- complete BTC regime response composition
- invalid/missing required fields
"""

from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.api.schemas.regime import (
    BTCRegimeResponse,
    CurrentRegimeResponse,
    EventAnalysisResponse,
    RegimePerformanceResponse,
    RegimeResponse,
    SimilarPeriodResponse,
)


# ==========================================================
# REGIME PERFORMANCE RESPONSE
# ==========================================================


def test_regime_performance_response_accepts_required_field_only():
    result = RegimePerformanceResponse(regime_id=1)

    assert result.regime_id == 1
    assert result.avg_return is None
    assert result.max_drawdown is None
    assert result.volatility is None
    assert result.sharpe_ratio is None
    assert result.btc_price_start is None
    assert result.btc_price_end is None


def test_regime_performance_response_accepts_all_fields():
    result = RegimePerformanceResponse(
        regime_id=1,
        avg_return=0.125,
        max_drawdown=-0.20,
        volatility=0.35,
        sharpe_ratio=1.4,
        btc_price_start=60_000.0,
        btc_price_end=67_500.0,
    )

    assert result.regime_id == 1
    assert result.avg_return == 0.125
    assert result.max_drawdown == -0.20
    assert result.volatility == 0.35
    assert result.sharpe_ratio == 1.4
    assert result.btc_price_start == 60_000.0
    assert result.btc_price_end == 67_500.0


def test_regime_performance_response_requires_regime_id():
    with pytest.raises(ValidationError):
        RegimePerformanceResponse()


# ==========================================================
# REGIME RESPONSE
# ==========================================================


def test_regime_response_accepts_required_fields_only():
    result = RegimeResponse(
        id=1,
        regime_type="growth",
        start_date=date(2026, 1, 1),
    )

    assert result.id == 1
    assert result.regime_type == "growth"
    assert result.start_date == date(2026, 1, 1)
    assert result.end_date is None
    assert result.duration_days is None
    assert result.performance is None


def test_regime_response_accepts_all_fields():
    performance = RegimePerformanceResponse(
        regime_id=1,
        avg_return=0.10,
        volatility=0.25,
        sharpe_ratio=1.2,
    )

    result = RegimeResponse(
        id=1,
        regime_type="growth",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 3, 31),
        duration_days=90,
        performance=performance,
    )

    assert result.id == 1
    assert result.regime_type == "growth"
    assert result.start_date == date(2026, 1, 1)
    assert result.end_date == date(2026, 3, 31)
    assert result.duration_days == 90
    assert result.performance == performance


def test_regime_response_requires_id():
    with pytest.raises(ValidationError):
        RegimeResponse(
            regime_type="growth",
            start_date=date(2026, 1, 1),
        )


def test_regime_response_requires_regime_type():
    with pytest.raises(ValidationError):
        RegimeResponse(
            id=1,
            start_date=date(2026, 1, 1),
        )


def test_regime_response_requires_start_date():
    with pytest.raises(ValidationError):
        RegimeResponse(
            id=1,
            regime_type="growth",
        )


def test_regime_response_accepts_nested_performance_dictionary():
    result = RegimeResponse(
        id=1,
        regime_type="growth",
        start_date=date(2026, 1, 1),
        performance={
            "regime_id": 1,
            "avg_return": 0.15,
            "sharpe_ratio": 1.5,
        },
    )

    assert isinstance(result.performance, RegimePerformanceResponse)
    assert result.performance.regime_id == 1
    assert result.performance.avg_return == 0.15


# ==========================================================
# CURRENT REGIME RESPONSE
# ==========================================================


def test_current_regime_response_accepts_required_fields():
    identified_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = CurrentRegimeResponse(
        regime_type="growth",
        confidence=0.85,
        visual_indicator="bull",
        identified_at=identified_at,
    )

    assert result.regime_type == "growth"
    assert result.confidence == 0.85
    assert result.visual_indicator == "bull"
    assert result.identified_at == identified_at
    assert result.expires_at is None


def test_current_regime_response_accepts_expires_at():
    identified_at = datetime(
        2026,
        1,
        1,
        12,
        0,
        tzinfo=timezone.utc,
    )

    expires_at = datetime(
        2026,
        1,
        2,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = CurrentRegimeResponse(
        regime_type="growth",
        confidence=0.85,
        visual_indicator="bull",
        identified_at=identified_at,
        expires_at=expires_at,
    )

    assert result.expires_at == expires_at


@pytest.mark.parametrize(
    "missing_field",
    [
        "regime_type",
        "confidence",
        "visual_indicator",
        "identified_at",
    ],
)
def test_current_regime_response_requires_required_fields(
    missing_field,
):
    data = {
        "regime_type": "growth",
        "confidence": 0.85,
        "visual_indicator": "bull",
        "identified_at": datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    }

    data.pop(missing_field)

    with pytest.raises(ValidationError):
        CurrentRegimeResponse(**data)


def test_current_regime_response_accepts_datetime_string():
    result = CurrentRegimeResponse(
        regime_type="growth",
        confidence=0.85,
        visual_indicator="bull",
        identified_at="2026-01-01T12:00:00Z",
    )

    assert isinstance(result.identified_at, datetime)


# ==========================================================
# SIMILAR PERIOD RESPONSE
# ==========================================================


def test_similar_period_response_accepts_required_fields():
    result = SimilarPeriodResponse(
        start_date=date(2025, 1, 1),
        regime_type="growth",
    )

    assert result.start_date == date(2025, 1, 1)
    assert result.end_date is None
    assert result.regime_type == "growth"
    assert result.distance is None
    assert result.reasoning is None
    assert result.btc_performance is None


def test_similar_period_response_accepts_all_fields():
    result = SimilarPeriodResponse(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        regime_type="growth",
        distance=0.15,
        reasoning="Similar macroeconomic conditions.",
        btc_performance=0.25,
    )

    assert result.start_date == date(2025, 1, 1)
    assert result.end_date == date(2025, 3, 31)
    assert result.regime_type == "growth"
    assert result.distance == 0.15
    assert result.reasoning == "Similar macroeconomic conditions."
    assert result.btc_performance == 0.25


def test_similar_period_response_requires_start_date():
    with pytest.raises(ValidationError):
        SimilarPeriodResponse(
            regime_type="growth",
        )


def test_similar_period_response_requires_regime_type():
    with pytest.raises(ValidationError):
        SimilarPeriodResponse(
            start_date=date(2025, 1, 1),
        )


# ==========================================================
# EVENT ANALYSIS RESPONSE
# ==========================================================


def test_event_analysis_response_accepts_required_fields():
    event_date = datetime(
        2026,
        1,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = EventAnalysisResponse(
        id=1,
        regime_id=10,
        event_type="fed_rate_change",
        event_date=event_date,
        btc_price_before=90_000.0,
        btc_price_after=92_000.0,
        btc_reaction_percent=2.22,
        reaction_window_hours=24,
        source="FRED",
    )

    assert result.id == 1
    assert result.regime_id == 10
    assert result.event_type == "fed_rate_change"
    assert result.event_date == event_date
    assert result.event_value is None
    assert result.btc_price_before == 90_000.0
    assert result.btc_price_after == 92_000.0
    assert result.btc_reaction_percent == 2.22
    assert result.reaction_window_hours == 24
    assert result.source == "FRED"
    assert result.reasoning is None


def test_event_analysis_response_accepts_optional_fields():
    event_date = datetime(
        2026,
        1,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )

    result = EventAnalysisResponse(
        id=1,
        regime_id=10,
        event_type="fed_rate_change",
        event_date=event_date,
        event_value=5.25,
        btc_price_before=90_000.0,
        btc_price_after=92_000.0,
        btc_reaction_percent=2.22,
        reaction_window_hours=24,
        source="FRED",
        reasoning="BTC increased following the event.",
    )

    assert result.event_value == 5.25
    assert result.reasoning == (
        "BTC increased following the event."
    )


@pytest.mark.parametrize(
    "missing_field",
    [
        "id",
        "regime_id",
        "event_type",
        "event_date",
        "btc_price_before",
        "btc_price_after",
        "btc_reaction_percent",
        "reaction_window_hours",
        "source",
    ],
)
def test_event_analysis_response_requires_required_fields(
    missing_field,
):
    data = {
        "id": 1,
        "regime_id": 10,
        "event_type": "fed_rate_change",
        "event_date": datetime(
            2026,
            1,
            15,
            tzinfo=timezone.utc,
        ),
        "btc_price_before": 90_000.0,
        "btc_price_after": 92_000.0,
        "btc_reaction_percent": 2.22,
        "reaction_window_hours": 24,
        "source": "FRED",
    }

    data.pop(missing_field)

    with pytest.raises(ValidationError):
        EventAnalysisResponse(**data)


# ==========================================================
# BTC REGIME RESPONSE
# ==========================================================


def test_btc_regime_response_accepts_empty_lists_and_no_current_regime():
    result = BTCRegimeResponse(
        regimes=[],
        current_regime=None,
        similar_periods=[],
        event_analysis=[],
    )

    assert result.regimes == []
    assert result.current_regime is None
    assert result.similar_periods == []
    assert result.event_analysis == []


def test_btc_regime_response_accepts_nested_models():
    current_regime = CurrentRegimeResponse(
        regime_type="growth",
        confidence=0.90,
        visual_indicator="bull",
        identified_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

    regime = RegimeResponse(
        id=1,
        regime_type="growth",
        start_date=date(2026, 1, 1),
    )

    similar_period = SimilarPeriodResponse(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 3, 31),
        regime_type="growth",
        distance=0.10,
        reasoning="Similar conditions.",
        btc_performance=0.20,
    )

    event = EventAnalysisResponse(
        id=1,
        regime_id=1,
        event_type="fed_rate_change",
        event_date=datetime(
            2026,
            1,
            15,
            tzinfo=timezone.utc,
        ),
        btc_price_before=90_000,
        btc_price_after=92_000,
        btc_reaction_percent=2.22,
        reaction_window_hours=24,
        source="FRED",
    )

    result = BTCRegimeResponse(
        regimes=[regime],
        current_regime=current_regime,
        similar_periods=[similar_period],
        event_analysis=[event],
    )

    assert len(result.regimes) == 1
    assert isinstance(result.regimes[0], RegimeResponse)

    assert isinstance(
        result.current_regime,
        CurrentRegimeResponse,
    )

    assert len(result.similar_periods) == 1
    assert isinstance(
        result.similar_periods[0],
        SimilarPeriodResponse,
    )

    assert len(result.event_analysis) == 1
    assert isinstance(
        result.event_analysis[0],
        EventAnalysisResponse,
    )


def test_btc_regime_response_builds_nested_models_from_dictionaries():
    result = BTCRegimeResponse(
        regimes=[
            {
                "id": 1,
                "regime_type": "growth",
                "start_date": "2026-01-01",
                "end_date": "2026-03-31",
                "duration_days": 89,
                "performance": {
                    "regime_id": 1,
                    "avg_return": 0.10,
                    "sharpe_ratio": 1.2,
                },
            }
        ],
        current_regime={
            "regime_type": "growth",
            "confidence": 0.90,
            "visual_indicator": "bull",
            "identified_at": "2026-01-01T12:00:00Z",
        },
        similar_periods=[
            {
                "start_date": "2025-01-01",
                "regime_type": "growth",
                "distance": 0.15,
            }
        ],
        event_analysis=[
            {
                "id": 1,
                "regime_id": 1,
                "event_type": "fed_rate_change",
                "event_date": "2026-01-15T12:00:00Z",
                "btc_price_before": 90_000,
                "btc_price_after": 92_000,
                "btc_reaction_percent": 2.22,
                "reaction_window_hours": 24,
                "source": "FRED",
            }
        ],
    )

    assert isinstance(result.regimes[0], RegimeResponse)
    assert isinstance(
        result.regimes[0].performance,
        RegimePerformanceResponse,
    )
    assert isinstance(
        result.current_regime,
        CurrentRegimeResponse,
    )
    assert isinstance(
        result.similar_periods[0],
        SimilarPeriodResponse,
    )
    assert isinstance(
        result.event_analysis[0],
        EventAnalysisResponse,
    )


@pytest.mark.parametrize(
    "missing_field",
    [
        "regimes",
        "current_regime",
        "similar_periods",
        "event_analysis",
    ],
)
def test_btc_regime_response_requires_all_top_level_fields(
    missing_field,
):
    data = {
        "regimes": [],
        "current_regime": None,
        "similar_periods": [],
        "event_analysis": [],
    }

    data.pop(missing_field)

    with pytest.raises(ValidationError):
        BTCRegimeResponse(**data)


# ==========================================================
# SERIALIZATION
# ==========================================================


def test_btc_regime_response_serializes_nested_models():
    result = BTCRegimeResponse(
        regimes=[
            RegimeResponse(
                id=1,
                regime_type="growth",
                start_date=date(2026, 1, 1),
            )
        ],
        current_regime=None,
        similar_periods=[],
        event_analysis=[],
    )

    data = result.model_dump()

    assert data["regimes"][0]["id"] == 1
    assert data["regimes"][0]["regime_type"] == "growth"
    assert data["regimes"][0]["start_date"] == date(2026, 1, 1)
    assert data["current_regime"] is None
    assert data["similar_periods"] == []
    assert data["event_analysis"] == []