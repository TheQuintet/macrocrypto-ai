import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from app.collectors.economic_calendar import (
    EconomicCalendarCollector,
)


@pytest.mark.asyncio
async def test_get_events_by_type_cpi():

    collector = EconomicCalendarCollector()

    collector._get_release_dates = AsyncMock(
        return_value={
            "release_dates": [
                {
                    "release_id": 10,
                    "date": "2026-08-12",
                }
            ]
        }
    )

    events = await collector.get_events_by_type(
        "cpi",
        days=365,
    )

    assert len(events) > 0

    event = events[0]

    assert event["event_type"] == "cpi"
    assert event["event_name"] == (
        "Consumer Price Index"
    )
    assert event["impact_level"] == "high"

    await collector.close()


@pytest.mark.asyncio
async def test_get_events_by_type_gdp():

    collector = EconomicCalendarCollector()

    collector._get_release_dates = AsyncMock(
        return_value={
            "release_dates": [
                {
                    "release_id": 53,
                    "date": "2026-08-15",
                }
            ]
        }
    )

    events = await collector.get_events_by_type(
        "gdp",
        days=365,
    )

    assert len(events) > 0

    assert events[0]["event_type"] == "gdp"

    await collector.close()


@pytest.mark.asyncio
async def test_get_events_by_type_employment():

    collector = EconomicCalendarCollector()

    collector._get_release_dates = AsyncMock(
        return_value={
            "release_dates": [
                {
                    "release_id": 50,
                    "date": "2026-08-07",
                }
            ]
        }
    )

    events = await collector.get_events_by_type(
        "employment",
        days=365,
    )

    assert len(events) > 0

    assert events[0]["event_type"] == "employment"

    await collector.close()


@pytest.mark.asyncio
async def test_get_events_by_type_fed():

    collector = EconomicCalendarCollector()

    collector._get_release_dates = AsyncMock(
        return_value={
            "release_dates": [
                {
                    "release_id": 101,
                    "date": "2026-09-16",
                },
                {
                    "release_id": 102,
                    "date": "2026-07-29",
                },
                {
                    "release_id": 103,
                    "date": "2026-06-17",
                },
            ]
        }
    )

    events = await collector.get_events_by_type(
        "fed",
        days=365,
    )

    assert len(events) > 0

    assert events[0]["event_type"] == "fed"
    assert events[0]["impact_level"] == "high"

    await collector.close()


@pytest.mark.asyncio
async def test_get_events_handles_empty_fred_response():

    collector = EconomicCalendarCollector()

    collector._get_release_dates = AsyncMock(
        return_value={
            "release_dates": []
        }
    )

    events = await collector.get_events_by_type(
        "cpi",
        days=365,
    )

    assert events == []

    await collector.close()


@pytest.mark.asyncio
async def test_get_all_events_returns_all_macro_events():

    collector = EconomicCalendarCollector()

    test_date = datetime(
        2026,
        9,
        16,
        tzinfo=timezone.utc,
    )

    collector.get_events_by_type = AsyncMock(
        side_effect=[
            [
                {
                    "event_type": "fed",
                    "event_date": test_date,
                }
            ],
            [
                {
                    "event_type": "cpi",
                    "event_date": test_date,
                }
            ],
            [
                {
                    "event_type": "gdp",
                    "event_date": test_date,
                }
            ],
            [
                {
                    "event_type": "employment",
                    "event_date": test_date,
                }
            ],
        ]
    )

    events = await collector.get_all_events(
        days=365
    )

    assert len(events) == 4

    event_types = {
        event["event_type"]
        for event in events
    }

    assert event_types == {
        "fed",
        "cpi",
        "gdp",
        "employment",
    }

    await collector.close()