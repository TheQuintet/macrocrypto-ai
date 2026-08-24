from unittest.mock import MagicMock

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.database.economic_event_repository import (
    EconomicEventRepository,
)


def create_repository():
    db = MagicMock()
    return EconomicEventRepository(db)


def test_create_event():
    repository = create_repository()

    repository.db.add = MagicMock()
    repository.db.commit = MagicMock()
    repository.db.refresh = MagicMock()

    event_date = datetime(
        2026,
        9,
        10,
        14,
        30,
        tzinfo=ZoneInfo("America/New_York"),
    )

    result = repository.create_event(
        event_name="CPI Release",
        event_type="cpi",
        event_date=event_date,
        impact_level="high",
        description="Consumer price inflation release.",
    )

    assert result.event_name == "CPI Release"
    assert result.event_type == "cpi"
    assert result.impact_level == "high"
    assert result.description == (
        "Consumer price inflation release."
    )

    assert result.event_date.tzinfo == timezone.utc
    assert result.event_date.hour == 18
    assert result.event_date.minute == 30

    repository.db.add.assert_called_once()
    repository.db.commit.assert_called_once()
    repository.db.refresh.assert_called_once()


def test_create_event_rejects_naive_datetime():
    repository = create_repository()

    naive_datetime = datetime(
        2026,
        9,
        10,
        14,
        30,
    )

    with pytest.raises(
        ValueError,
        match="event_date must be timezone-aware",
    ):
        repository.create_event(
            event_name="CPI Release",
            event_type="cpi",
            event_date=naive_datetime,
            impact_level="high",
            description="Consumer price inflation release.",
        )

    repository.db.add.assert_not_called()
    repository.db.commit.assert_not_called()