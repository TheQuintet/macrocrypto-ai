import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from app.collectors.binance import (
    BinanceCollector,
    BinanceWebSocketClient,
)


@pytest.fixture
def collector():

    client = BinanceCollector()

    client.client = MagicMock()

    return client



# =====================================================
# get_24hr_ticker
# =====================================================


@pytest.mark.asyncio
async def test_get_24hr_ticker_success(
    collector
):

    response = MagicMock()

    response.raise_for_status = MagicMock()

    response.json.return_value = {
        "symbol": "BTCUSDT",
        "priceChange": "100",
        "priceChangePercent": "1.5",
        "lastPrice": "60000",
        "volume": "10",
    }


    collector.client.get = AsyncMock(
        return_value=response
    )


    result = await collector.get_24hr_ticker()


    assert result["symbol"] == "BTCUSDT"

    assert result["price_change"] == 100

    assert result["last_price"] == 60000

    assert result["source"] == "binance_rest"



@pytest.mark.asyncio
async def test_get_24hr_ticker_timeout(
    collector
):

    collector.client.get = AsyncMock(
        side_effect=httpx.TimeoutException(
            "timeout"
        )
    )


    result = await collector.get_24hr_ticker()


    assert result["source"] == "binance_rest_dummy"

    assert result["last_price"] == 0.0



@pytest.mark.asyncio
async def test_get_24hr_ticker_http_error(
    collector
):

    response = MagicMock()

    response.raise_for_status.side_effect = (
        httpx.HTTPStatusError(
            "error",
            request=MagicMock(),
            response=MagicMock(
                status_code=500,
                text="error"
            )
        )
    )


    collector.client.get = AsyncMock(
        return_value=response
    )


    result = await collector.get_24hr_ticker()


    assert result["source"] == "binance_rest_dummy"



@pytest.mark.asyncio
async def test_get_24hr_ticker_generic_error(
    collector
):

    collector.client.get = AsyncMock(
        side_effect=Exception(
            "failed"
        )
    )


    result = await collector.get_24hr_ticker()


    assert result["source"] == "binance_rest_dummy"



# =====================================================
# current price
# =====================================================


@pytest.mark.asyncio
async def test_get_current_price_success(
    collector
):

    response = MagicMock()

    response.raise_for_status = MagicMock()

    response.json.return_value = {
        "symbol": "BTCUSDT",
        "price": "60000"
    }


    collector.client.get = AsyncMock(
        return_value=response
    )


    result = await collector.get_current_price()


    assert result["price"] == 60000

    assert result["symbol"] == "BTCUSDT"



@pytest.mark.asyncio
async def test_get_current_price_error(
    collector
):

    collector.client.get = AsyncMock(
        side_effect=Exception(
            "failed"
        )
    )


    result = await collector.get_current_price()


    assert result["price"] == 0.0



# =====================================================
# klines
# =====================================================


@pytest.mark.asyncio
async def test_get_klines_success(
    collector
):

    response = MagicMock()

    response.raise_for_status = MagicMock()

    response.json.return_value = [
        [
            1,
            "60000",
            "61000",
            "59000",
            "60500",
            "10",
            2,
            "100",
            50,
            "5",
            "50"
        ]
    ]


    collector.client.get = AsyncMock(
        return_value=response
    )


    result = await collector.get_klines()


    assert len(result) == 1

    assert result[0]["open"] == 60000

    assert result[0]["close"] == 60500



@pytest.mark.asyncio
async def test_get_klines_error(
    collector
):

    collector.client.get = AsyncMock(
        side_effect=Exception(
            "failed"
        )
    )


    result = await collector.get_klines()


    assert result == []



# =====================================================
# close
# =====================================================


@pytest.mark.asyncio
async def test_close(
    collector
):

    collector.client.aclose = AsyncMock()


    await collector.close()


    collector.client.aclose.assert_called_once()



# =====================================================
# dummy ticker
# =====================================================


def test_dummy_ticker(
    collector
):

    result = collector._get_dummy_ticker(
        "BTCUSDT"
    )


    assert result["symbol"] == "BTCUSDT"

    assert result["source"] == "binance_rest_dummy"



# =====================================================
# Legacy websocket wrapper
# =====================================================


@pytest.mark.asyncio
async def test_legacy_websocket_connect():

    client = BinanceWebSocketClient()


    result = await client.connect()


    assert result is False



@pytest.mark.asyncio
async def test_legacy_subscribe():

    client = BinanceWebSocketClient()


    result = await client.subscribe_btc_usdt(
        None
    )


    assert result is None



@pytest.mark.asyncio
async def test_legacy_disconnect():

    client = BinanceWebSocketClient()


    result = await client.disconnect()


    assert result is None