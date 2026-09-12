"""
Tests for the gold_spot service.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.gold_spot_service import (
    GOLD_SPOT_INDICATOR,
    GoldSpotService,
)


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def collector():
    return MagicMock()


@pytest.fixture
def service(db, collector):
    return GoldSpotService(db, collector=collector)


@pytest.mark.asyncio
async def test_collect_returns_gold_spot_record(
    service,
    collector,
):
    collector.get_gold_spot = AsyncMock(return_value=2650.50)

    result = await service.collect()

    assert len(result) == 1

    record = result[0]

    assert record["indicator_name"] == GOLD_SPOT_INDICATOR
    assert record["value"] == 2650.50
    assert record["previous_value"] is None
    assert record["change_percent"] is None
    assert record["source"] == "yahoo_finance"
    assert isinstance(record["time"], datetime)
    assert record["time"].tzinfo is not None

    collector.get_gold_spot.assert_awaited_once()


@pytest.mark.asyncio
async def test_collect_returns_float_value(
    service,
    collector,
):
    collector.get_gold_spot = AsyncMock(return_value=2650.50)

    result = await service.collect()

    assert result[0]["value"] == 2650.50
    assert isinstance(result[0]["value"], float)
    
@pytest.mark.asyncio
async def test_collect_returns_empty_list_when_price_unavailable(
    service,
    collector,
):
    collector.get_gold_spot = AsyncMock(return_value=None)

    result = await service.collect()

    assert result == []

    collector.get_gold_spot.assert_awaited_once()


@pytest.mark.asyncio
async def test_collect_returns_single_record(
    service,
    collector,
):
    collector.get_gold_spot = AsyncMock(return_value=2700.0)

    result = await service.collect()

    assert isinstance(result, list)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_collect_uses_utc_timestamp(
    service,
    collector,
):
    collector.get_gold_spot = AsyncMock(return_value=2700.0)

    result = await service.collect()

    timestamp = result[0]["time"]

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == 0


@pytest.mark.asyncio
async def test_close_does_not_close_injected_collector(
    service,
    collector,
):
    collector.close = AsyncMock()

    await service.close()

    collector.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_close_closes_owned_collector(db):
    owned_collector = MagicMock()
    owned_collector.close = AsyncMock()

    service = GoldSpotService(db, collector=None)

    # Replace the automatically-created collector with a controlled mock
    service.collector.close = owned_collector.close

    await service.close()

    service.collector.close.assert_awaited_once()


def test_service_uses_injected_collector(db, collector):
    service = GoldSpotService(db, collector=collector)

    assert service.collector is collector
    assert service._owns_collector is False


def test_service_owns_collector_when_not_injected(db):
    service = GoldSpotService(db)

    assert service.collector is not None
    assert service._owns_collector is True

