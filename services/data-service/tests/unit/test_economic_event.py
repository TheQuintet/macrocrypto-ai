from datetime import datetime, timezone

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

    assert event.event_type == "fed"
    assert event.impact_level == "high"
    assert event.event_date.tzinfo is not None


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
    from zoneinfo import ZoneInfo

    event = EconomicEventCreate(
        event_name="CPI Release",
        event_type="cpi",
        event_date=datetime(
            2026,
            9,
            10,
            14,
            30,
            tzinfo=ZoneInfo("America/New_York"),
        ),
        impact_level="high",
        description="Consumer price inflation release.",
    )

    assert event.event_date.utcoffset().total_seconds() == 0