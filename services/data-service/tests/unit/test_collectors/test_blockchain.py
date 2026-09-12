"""
Tests for the Blockchain.com collector.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from app.collectors.blockchain import BlockchainCollector


@pytest.mark.asyncio
async def test_get_active_addresses_returns_normalized_records():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={
            "values": [
                {
                    "x": 1704067200,
                    "y": 850000,
                },
                {
                    "x": 1704153600,
                    "y": 875000,
                },
            ]
        }
    )

    result = await collector.get_active_addresses()

    assert result == [
        {
            "time": datetime(
                2024,
                1,
                1,
                tzinfo=timezone.utc,
            ),
            "value": 850000.0,
            "source": "blockchain.com",
        },
        {
            "time": datetime(
                2024,
                1,
                2,
                tzinfo=timezone.utc,
            ),
            "value": 875000.0,
            "source": "blockchain.com",
        },
    ]

    collector._get.assert_awaited_once_with(
        "n-unique-addresses",
        params={
            "timespan": "1year",
            "format": "json",
        },
    )


@pytest.mark.asyncio
async def test_get_active_addresses_passes_optional_parameters():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={"values": []}
    )

    await collector.get_active_addresses(
        timespan="30days",
        rolling_average="7days",
        start="2024-01-01",
    )

    collector._get.assert_awaited_once_with(
        "n-unique-addresses",
        params={
            "timespan": "30days",
            "format": "json",
            "rollingAverage": "7days",
            "start": "2024-01-01",
        },
    )


@pytest.mark.asyncio
async def test_get_active_addresses_handles_missing_optional_parameters():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={"values": []}
    )

    await collector.get_active_addresses(
        timespan="2years",
    )

    collector._get.assert_awaited_once_with(
        "n-unique-addresses",
        params={
            "timespan": "2years",
            "format": "json",
        },
    )


@pytest.mark.asyncio
async def test_get_active_addresses_skips_invalid_records():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={
            "values": [
                {
                    "x": 1704067200,
                    "y": 850000,
                },
                {
                    "x": None,
                    "y": 900000,
                },
                {
                    "x": 1704153600,
                    "y": None,
                },
                {
                    "x": "invalid",
                    "y": 950000,
                },
                {
                    "x": 1704240000,
                    "y": "invalid",
                },
                "not-a-dict",
                {
                    "x": 1704326400,
                    "y": 975000,
                },
            ]
        }
    )

    result = await collector.get_active_addresses()

    assert result == [
        {
            "time": datetime(
                2024,
                1,
                1,
                tzinfo=timezone.utc,
            ),
            "value": 850000.0,
            "source": "blockchain.com",
        },
        {
            "time": datetime(
                2024,
                1,
                4,
                tzinfo=timezone.utc,
            ),
            "value": 975000.0,
            "source": "blockchain.com",
        },
    ]


@pytest.mark.asyncio
async def test_get_active_addresses_returns_empty_for_invalid_values():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={
            "values": "invalid",
        }
    )

    result = await collector.get_active_addresses()

    assert result == []


@pytest.mark.asyncio
async def test_get_active_addresses_returns_empty_when_values_missing():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={}
    )

    result = await collector.get_active_addresses()

    assert result == []


@pytest.mark.asyncio
async def test_get_active_addresses_returns_empty_for_empty_values():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={
            "values": [],
        }
    )

    result = await collector.get_active_addresses()

    assert result == []


@pytest.mark.asyncio
async def test_get_active_addresses_propagates_client_error():
    collector = BlockchainCollector()

    error = aiohttp.ClientError("request failed")

    collector._get = AsyncMock(
        side_effect=error
    )

    with pytest.raises(aiohttp.ClientError, match="request failed"):
        await collector.get_active_addresses()


@pytest.mark.asyncio
async def test_close_closes_owned_session():
    session = MagicMock()
    session.close = AsyncMock()

    collector = BlockchainCollector(session=None)

    # Simulate the collector having created its own session.
    collector.session = session

    await collector.close()

    session.close.assert_awaited_once()
    assert collector.session is None


@pytest.mark.asyncio
async def test_close_does_not_close_injected_session():
    session = MagicMock()
    session.close = AsyncMock()

    collector = BlockchainCollector(session=session)

    await collector.close()

    session.close.assert_not_awaited()
    assert collector.session is session


@pytest.mark.asyncio
async def test_get_active_addresses_uses_correct_chart():
    collector = BlockchainCollector()
    collector._get = AsyncMock(
        return_value={"values": []}
    )

    await collector.get_active_addresses()

    chart_name = collector._get.await_args.args[0]

    assert chart_name == "n-unique-addresses"