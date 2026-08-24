from datetime import datetime, timezone

import pytest
from unittest.mock import AsyncMock, Mock

from app.models.economic_event import EconomicEvent
from app.services.economic_calendar_service import (
    EconomicCalendarService,
)


@pytest.mark.asyncio
async def test_collect_events_creates_new_events(
    clean_db,
):
    collector = AsyncMock()

    collector.get_all_events.return_value = [
        {
            "event_name": "Consumer Price Index",
            "event_type": "cpi",
            "event_date": datetime(
                2026,
                9,
                10,
                12,
                0,
                tzinfo=timezone.utc,
            ),
            "impact_level": "high",
            "description": "Inflation release.",
        }
    ]

    service = EconomicCalendarService(
        clean_db,
        collector,
    )

    events = await service.collect_events(
        days=365
    )

    assert len(events) == 1

    saved = (
        clean_db.query(EconomicEvent)
        .first()
    )

    assert saved is not None
    assert saved.event_type == "cpi"
    assert saved.impact_level == "high"
    assert saved.event_date.tzinfo is not None

    await service.close()


@pytest.mark.asyncio
async def test_collect_events_skips_duplicates(
    clean_db,
):
    collector = AsyncMock()

    event_date = datetime(
        2026,
        9,
        10,
        12,
        0,
        tzinfo=timezone.utc,
    )

    collector.get_all_events.return_value = [
        {
            "event_name": "GDP Release",
            "event_type": "gdp",
            "event_date": event_date,
            "impact_level": "high",
            "description": "GDP report.",
        }
    ]

    service = EconomicCalendarService(
        clean_db,
        collector,
    )

    first_result = await service.collect_events()

    second_result = await service.collect_events()

    assert len(first_result) == 1
    assert len(second_result) == 0

    count = (
        clean_db.query(EconomicEvent)
        .count()
    )

    assert count == 1

    await service.close()


@pytest.mark.asyncio
async def test_collect_events_normalizes_naive_datetime(
    clean_db,
):
    collector = AsyncMock()

    collector.get_all_events.return_value = [
        {
            "event_name": "Employment Report",
            "event_type": "employment",
            "event_date": datetime(
                2026,
                9,
                5,
                8,
                30,
            ),
            "impact_level": "high",
            "description": "Jobs report.",
        }
    ]

    service = EconomicCalendarService(
        clean_db,
        collector,
    )

    events = await service.collect_events()

    assert len(events) == 1

    saved = (
        clean_db.query(EconomicEvent)
        .first()
    )

    assert saved.event_date.tzinfo is not None

    assert (
        saved.event_date.utcoffset()
        .total_seconds()
        == 0
    )

    await service.close()


@pytest.mark.asyncio
async def test_collect_events_returns_empty_when_no_events(
    clean_db,
):
    collector = AsyncMock()

    collector.get_all_events.return_value = []

    service = EconomicCalendarService(
        clean_db,
        collector,
    )

    events = await service.collect_events()

    assert events == []

    count = (
        clean_db.query(EconomicEvent)
        .count()
    )

    assert count == 0

    await service.close()


@pytest.mark.asyncio
async def test_collect_events_skips_missing_event_type(
    clean_db,
):
    collector = AsyncMock()

    collector.get_all_events.return_value = [
        {
            "event_name": "Invalid Event",
            "event_date": datetime.now(
                timezone.utc
            ),
            "impact_level": "high",
            "description": "Missing type.",
        }
    ]

    service = EconomicCalendarService(
        clean_db,
        collector,
    )

    events = await service.collect_events()

    assert events == []

    await service.close()


@pytest.mark.asyncio
async def test_collect_events_rolls_back_on_database_error(
    clean_db,
):
    collector = AsyncMock()

    collector.get_all_events.return_value = [
        {
            "event_name": "CPI Release",
            "event_type": "cpi",
            "event_date": datetime.now(
                timezone.utc
            ),
            "impact_level": "high",
            "description": "CPI data.",
        }
    ]

    service = EconomicCalendarService(
        clean_db,
        collector,
    )

    clean_db.commit = Mock(
        side_effect=Exception(
            "Database failure"
        )
    )

    with pytest.raises(Exception):

        await service.collect_events()

    await service.close()