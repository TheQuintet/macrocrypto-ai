from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from app.schemas.economic_event import EconomicEventCreate


def test_valid_economic_event():
    event = EconomicEventCreate(
        event_name="Federal Reserve Interest Rate Decision",
        event_type="fed",
        event_date=datetime(
            2026,
            9,
            16,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        impact_level="high",
        description="Federal Reserve interest rate decision.",
    )

    assert event.event_name == (
        "Federal Reserve Interest Rate Decision"
    )
    assert event.event_type == "fed"
    assert event.impact_level == "high"
    assert event.event_date.tzinfo == timezone.utc


def test_invalid_event_type():
    with pytest.raises(ValidationError):
        EconomicEventCreate(
            event_name="Invalid Event",
            event_type="invalid",
            event_date=datetime(
                2026,
                9,
                16,
                tzinfo=timezone.utc,
            ),
            impact_level="high",
            description="Test event.",
        )


def test_invalid_impact_level():
    with pytest.raises(ValidationError):
        EconomicEventCreate(
            event_name="Invalid Event",
            event_type="fed",
            event_date=datetime(
                2026,
                9,
                16,
                tzinfo=timezone.utc,
            ),
            impact_level="invalid",
            description="Test event.",
        )


def test_naive_event_datetime_rejected():
    with pytest.raises(ValidationError):
        EconomicEventCreate(
            event_name="Federal Reserve Decision",
            event_type="fed",
            event_date=datetime(
                2026,
                9,
                16,
            ),
            impact_level="high",
            description="Test event.",
        )


def test_event_datetime_normalized_to_utc():
    event = EconomicEventCreate(
        event_name="CPI Release",
        event_type="cpi",
        event_date=datetime(
            2026,
            9,
            10,
            14,
            30,
            tzinfo=ZoneInfo(
                "America/New_York"
            ),
        ),
        impact_level="high",
        description="Consumer price inflation release.",
    )

    # September 2026 New York = UTC-4
    # 14:30 New York = 18:30 UTC
    assert event.event_date.utcoffset().total_seconds() == 0
    assert event.event_date.hour == 18
    assert event.event_date.minute == 30


def test_missing_event_name():

    with pytest.raises(ValidationError):

        EconomicEventCreate(
            event_type="cpi",
            event_date=datetime.now(
                timezone.utc
            ),
            impact_level="high",
            description="Missing event name.",
        )


@pytest.mark.parametrize(
    "event_type",
    [
        "fed",
        "cpi",
        "gdp",
        "employment",
    ],
)
def test_supported_event_types(event_type):

    event = EconomicEventCreate(
        event_name="Economic Event",
        event_type=event_type,
        event_date=datetime.now(
            timezone.utc
        ),
        impact_level="high",
        description="Test event.",
    )

    assert event.event_type == event_type


@pytest.mark.parametrize(
    "impact_level",
    [
        "high",
        "medium",
        "low",
    ],
)
def test_supported_impact_levels(
    impact_level
):

    event = EconomicEventCreate(
        event_name="Economic Event",
        event_type="fed",
        event_date=datetime.now(
            timezone.utc
        ),
        impact_level=impact_level,
        description="Test event.",
    )

    assert event.impact_level == impact_level


def test_empty_description_rejected():

    with pytest.raises(ValidationError):

        EconomicEventCreate(
            event_name="GDP Release",
            event_type="gdp",
            event_date=datetime.now(
                timezone.utc
            ),
            impact_level="high",
            description="",
        )