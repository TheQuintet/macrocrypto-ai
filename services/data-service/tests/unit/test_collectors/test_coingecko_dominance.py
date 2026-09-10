import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.collectors.coingecko import CoinGeckoCollector


@pytest.mark.asyncio
async def test_get_btc_dominance():
    collector = CoinGeckoCollector()

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "data": {
            "market_cap_percentage": {
                "btc": 56.42,
            }
        }
    }

    collector.client.get = AsyncMock(
        return_value=response
    )

    result = await collector.get_btc_dominance()

    assert result == {
        "btc_dominance": 56.42,
        "source": "coingecko",
    }

    collector.client.get.assert_called_once_with(
        "https://api.coingecko.com/api/v3/global"
    )

    await collector.close()


@pytest.mark.asyncio
async def test_get_btc_dominance_missing_value():
    collector = CoinGeckoCollector()

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "data": {
            "market_cap_percentage": {}
        }
    }

    collector.client.get = AsyncMock(
        return_value=response
    )

    result = await collector.get_btc_dominance()

    assert result["btc_dominance"] == 0.0
    assert result["source"] == "coingecko"

    await collector.close()