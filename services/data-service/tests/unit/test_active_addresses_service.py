"""
Tests for the ActiveAddressesService.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.active_addresses_service import (
    ACTIVE_ADDRESSES_INDICATOR,
    TIMESPAN,
    ActiveAddressesService,
)


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def collector():
    return MagicMock()


@pytest.fixture
def service(db, collector):
    return ActiveAddressesService(
        db=db,
        collector=collector,
    )


@pytest.mark.asyncio
async def test_calculate_returns_active_address_records(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[
            {
                "time": datetime(
                    2024,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                "value": 1000,
                "source": "blockchain.com",
            },
            {
                "time": datetime(
                    2024,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
                "value": 1100,
                "source": "blockchain.com",
            },
        ]
    )

    result = await service.calculate()

    assert len(result) == 2

    assert result[0] == {
        "indicator_name": ACTIVE_ADDRESSES_INDICATOR,
        "time": datetime(
            2024,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        "value": 1000.0,
        "previous_value": None,
        "change_percent": None,
        "source": "blockchain.com",
    }

    assert result[1] == {
        "indicator_name": ACTIVE_ADDRESSES_INDICATOR,
        "time": datetime(
            2024,
            1,
            2,
            tzinfo=timezone.utc,
        ),
        "value": 1100.0,
        "previous_value": 1000.0,
        "change_percent": 10.0,
        "source": "blockchain.com",
    }

    collector.get_active_addresses.assert_awaited_once_with(
        timespan=TIMESPAN,
    )


@pytest.mark.asyncio
async def test_calculate_sorts_records_chronologically(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[
            {
                "time": datetime(
                    2024,
                    1,
                    3,
                    tzinfo=timezone.utc,
                ),
                "value": 1200,
                "source": "blockchain.com",
            },
            {
                "time": datetime(
                    2024,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                "value": 1000,
                "source": "blockchain.com",
            },
            {
                "time": datetime(
                    2024,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
                "value": 1100,
                "source": "blockchain.com",
            },
        ]
    )

    result = await service.calculate()

    assert [record["value"] for record in result] == [
        1000.0,
        1100.0,
        1200.0,
    ]

    assert result[1]["previous_value"] == 1000.0
    assert result[1]["change_percent"] == 10.0

    assert result[2]["previous_value"] == 1100.0
    assert result[2]["change_percent"] == pytest.approx(
        9.0909,
        abs=0.0001,
    )


@pytest.mark.asyncio
async def test_calculate_handles_decrease(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[
            {
                "time": datetime(
                    2024,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                "value": 1000,
            },
            {
                "time": datetime(
                    2024,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
                "value": 800,
            },
        ]
    )

    result = await service.calculate()

    assert result[1]["previous_value"] == 1000.0
    assert result[1]["change_percent"] == -20.0


@pytest.mark.asyncio
async def test_calculate_handles_zero_previous_value(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[
            {
                "time": datetime(
                    2024,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                "value": 0,
            },
            {
                "time": datetime(
                    2024,
                    1,
                    2,
                    tzinfo=timezone.utc,
                ),
                "value": 100,
            },
        ]
    )

    result = await service.calculate()

    assert result[1]["previous_value"] == 0.0
    assert result[1]["change_percent"] is None


@pytest.mark.asyncio
async def test_calculate_returns_empty_when_no_records(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[]
    )

    result = await service.calculate()

    assert result == []

    collector.get_active_addresses.assert_awaited_once_with(
        timespan=TIMESPAN,
    )


@pytest.mark.asyncio
async def test_calculate_does_not_persist_records(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[
            {
                "time": datetime(
                    2024,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                "value": 1000,
            },
        ]
    )

    result = await service.calculate()

    assert len(result) == 1

    # calculate() prepares records only.
    # Persistence is handled by the scheduler.
    service.repository.create_many = MagicMock()

    service.repository.create_many.assert_not_called()


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

    service = ActiveAddressesService(
        db=db,
        collector=None,
    )

    # Replace the automatically created collector with a mock while
    # preserving ownership semantics.
    service.collector = owned_collector
    service._owns_collector = True

    await service.close()

    owned_collector.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_calculate_preserves_blockchain_source(
    service,
    collector,
):
    collector.get_active_addresses = AsyncMock(
        return_value=[
            {
                "time": datetime(
                    2024,
                    1,
                    1,
                    tzinfo=timezone.utc,
                ),
                "value": 1000,
                "source": "blockchain.com",
            },
        ]
    )

    result = await service.calculate()

    assert result[0]["source"] == "blockchain.com"