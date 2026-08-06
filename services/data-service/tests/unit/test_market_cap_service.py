import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.market_cap_service import MarketCapService
from tests.fixtures.mock_data import MOCK_BTC_MARKET_CAP


# Verify that market cap data is fetched and successfully cached in Redis.
@pytest.mark.asyncio
async def test_update_market_cap_success():
    cache_client = MagicMock()
    cache_client.set = AsyncMock(return_value=True)

    service = MarketCapService(cache_client)

    service.collector.get_btc_market_cap = AsyncMock(
        return_value=MOCK_BTC_MARKET_CAP
    )

    result = await service.update_market_cap()

    assert result is True

    cache_client.set.assert_called_once_with(
        "btc_market_cap",
        MOCK_BTC_MARKET_CAP,
        ttl=900,
    )


# Verify that the service returns False when the CoinGecko request fails.
@pytest.mark.asyncio
async def test_update_market_cap_failure():
    cache_client = MagicMock()

    service = MarketCapService(cache_client)

    service.collector.get_btc_market_cap = AsyncMock(
        side_effect=Exception("CoinGecko unavailable")
    )

    result = await service.update_market_cap()

    assert result is False


# Verify that cached market cap data is retrieved from Redis.
@pytest.mark.asyncio
async def test_get_market_cap():
    cache_client = MagicMock()
    cache_client.get = AsyncMock(return_value=MOCK_BTC_MARKET_CAP)

    service = MarketCapService(cache_client)

    result = await service.get_market_cap()

    assert result == MOCK_BTC_MARKET_CAP

    cache_client.get.assert_called_once_with(
        "btc_market_cap"
    )


# Verify that the CoinGecko collector is closed during service shutdown.
@pytest.mark.asyncio
async def test_close():
    cache_client = MagicMock()

    service = MarketCapService(cache_client)

    service.collector.close = AsyncMock()

    await service.close()

    service.collector.close.assert_awaited_once()