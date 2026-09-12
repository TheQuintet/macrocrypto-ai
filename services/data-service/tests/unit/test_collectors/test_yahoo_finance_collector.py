"""
Tests for Yahoo Finance gold spot collector.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.collectors.yahoo_finance import YahooFinanceCollector


@pytest.fixture
def collector():
    return YahooFinanceCollector()


@pytest.mark.asyncio
async def test_get_latest_price_returns_regular_market_price(collector):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": 2650.50,
                        "previousClose": 2645.25,
                    }
                }
            ]
        }
    }

    collector.client.get = AsyncMock(return_value=response)

    result = await collector._get_latest_price("XAUUSD=X")

    assert result == 2650.50
    collector.client.get.assert_awaited_once_with(
        f"{collector.BASE_URL}/XAUUSD=X",
        params={
            "range": "5d",
            "interval": "1d",
        },
    )


@pytest.mark.asyncio
async def test_get_latest_price_falls_back_to_previous_close(collector):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": None,
                        "previousClose": 2645.25,
                    }
                }
            ]
        }
    }

    collector.client.get = AsyncMock(return_value=response)

    result = await collector._get_latest_price("XAUUSD=X")

    assert result == 2645.25


@pytest.mark.asyncio
async def test_get_latest_price_returns_none_when_result_is_empty(collector):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "chart": {
            "result": []
        }
    }

    collector.client.get = AsyncMock(return_value=response)

    result = await collector._get_latest_price("XAUUSD=X")

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_price_returns_none_when_price_is_missing(collector):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {}
                }
            ]
        }
    }

    collector.client.get = AsyncMock(return_value=response)

    result = await collector._get_latest_price("XAUUSD=X")

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_price_returns_none_on_http_error(collector):
    collector.client.get = AsyncMock(
        side_effect=httpx.HTTPError("Yahoo Finance unavailable")
    )

    result = await collector._get_latest_price("XAUUSD=X")

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_price_returns_none_on_invalid_price(collector):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": "not-a-number"
                    }
                }
            ]
        }
    }

    collector.client.get = AsyncMock(return_value=response)

    result = await collector._get_latest_price("XAUUSD=X")

    assert result is None


@pytest.mark.asyncio
async def test_get_gold_spot_returns_spot_price(collector):
    collector._get_latest_price = AsyncMock(return_value=2650.50)

    result = await collector.get_gold_spot()

    assert result == 2650.50
    collector._get_latest_price.assert_awaited_once_with(
        collector.GOLD_SPOT_SYMBOL
    )


@pytest.mark.asyncio
async def test_get_gold_spot_falls_back_to_gold_futures(collector):
    collector._get_latest_price = AsyncMock(
        side_effect=[None, 2648.75]
    )

    result = await collector.get_gold_spot()

    assert result == 2648.75
    assert collector._get_latest_price.await_count == 2
    collector._get_latest_price.assert_any_await(
        collector.GOLD_SPOT_SYMBOL
    )
    collector._get_latest_price.assert_any_await(
        collector.GOLD_FUTURES_SYMBOL
    )


@pytest.mark.asyncio
async def test_get_gold_spot_returns_none_when_spot_and_futures_fail(
    collector,
):
    collector._get_latest_price = AsyncMock(
        side_effect=[None, None]
    )

    result = await collector.get_gold_spot()

    assert result is None
    assert collector._get_latest_price.await_count == 2


@pytest.mark.asyncio
async def test_close_closes_http_client(collector):
    collector.client.aclose = AsyncMock()

    await collector.close()

    collector.client.aclose.assert_awaited_once()