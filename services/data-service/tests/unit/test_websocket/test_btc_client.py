import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.websocket.btc_client import BTCWebSocketClient


@pytest.fixture
def ws_client():
    return BTCWebSocketClient()


# =====================================================
# Initialization
# =====================================================


def test_client_initialization():

    client = BTCWebSocketClient()

    assert client.is_running is False
    assert client.websocket is None
    assert client.task is None



# =====================================================
# start / stop
# =====================================================


@pytest.mark.asyncio
async def test_start():

    client = BTCWebSocketClient()

    client._run_websocket = AsyncMock()


    await client.start()


    assert client.is_running is True
    assert client.task is not None


    await client.stop()



@pytest.mark.asyncio
async def test_start_when_already_running():

    client = BTCWebSocketClient()

    client.is_running = True


    result = await client.start()


    assert result is None



@pytest.mark.asyncio
async def test_stop():

    client = BTCWebSocketClient()

    client.is_running = True

    client.task = MagicMock()

    client.task.done.return_value = True


    await client.stop()


    assert client.is_running is False
    assert client.task is None



# =====================================================
# process message
# =====================================================


@pytest.mark.asyncio
async def test_process_message_missing_ticker():

    client = BTCWebSocketClient()


    result = await client._process_message(
        {
            "invalid": True
        }
    )


    assert result is None



@pytest.mark.asyncio
async def test_process_message_success():

    processor = MagicMock()

    processor.process_ticker_update.return_value = True


    repository = MagicMock()


    client = BTCWebSocketClient(
        data_processor=processor,
        btc_price_repository=repository
    )


    data = {
        "s": "BTCUSDT",
        "c": "60000",
        "v": "10",
        "o": "59000",
        "h": "61000",
        "l": "58000",
        "q": "100",
        "P": "1",
        "p": "500",
    }


    await client._process_message(
        data
    )


    processor.process_ticker_update.assert_called_once()

    repository.save_price.assert_called_once()



@pytest.mark.asyncio
async def test_process_message_invalid_price():

    client = BTCWebSocketClient()


    await client._process_message(
        {
            "c": "invalid"
        }
    )



@pytest.mark.asyncio
async def test_process_message_cache_update():

    processor = MagicMock()

    processor.process_ticker_update.return_value = True


    snapshot = MagicMock()

    snapshot.to_dict.return_value = {
        "price": 60000
    }


    processor.get_snapshot.return_value = snapshot


    cache = MagicMock()

    cache.is_connected = True

    cache.set = AsyncMock()


    client = BTCWebSocketClient(
        data_processor=processor,
        cache_client=cache
    )


    await client._process_message(
        {
            "c": "60000",
            "v": "10"
        }
    )


    cache.set.assert_called_once()



@pytest.mark.asyncio
async def test_process_message_cache_error():

    processor = MagicMock()

    processor.process_ticker_update.return_value = True


    cache = MagicMock()

    cache.is_connected = True

    cache.get = AsyncMock(
        side_effect=Exception(
            "cache failure"
        )
    )


    client = BTCWebSocketClient(
        data_processor=processor,
        cache_client=cache
    )


    await client._process_message(
        {
            "c": "60000",
            "v": "10"
        }
    )


@pytest.mark.asyncio
async def test_process_message_rabbitmq_publish():

    rabbit = MagicMock()


    client = BTCWebSocketClient(
        rabbitmq_producer=rabbit
    )


    await client._process_message(
        {
            "s": "BTCUSDT",
            "c": "60000",
            "o": "59000",
            "h": "61000",
            "l": "58000",
            "v": "10",
            "q": "100",
            "P": "1",
            "p": "500",
        }
    )

    rabbit.publish_btc_update.assert_called_once()



@pytest.mark.asyncio
async def test_process_message_rabbitmq_error():

    rabbit = MagicMock()

    rabbit.publish_btc_update.side_effect = Exception(
        "rabbit failure"
    )


    client = BTCWebSocketClient(
        rabbitmq_producer=rabbit
    )


    await client._process_message(
        {
            "s": "BTCUSDT",
            "c": "60000"
        }
    )



# =====================================================
# websocket runner
# =====================================================


@pytest.mark.asyncio
async def test_run_websocket_success():

    client = BTCWebSocketClient()

    websocket = MagicMock()

    websocket.send = AsyncMock()

    websocket.recv = AsyncMock(
        return_value=json.dumps(
            {
                "c": "60000"
            }
        )
    )


    async def stop_after_message(data):

        client.is_running = False


    client._process_message = AsyncMock(
        side_effect=stop_after_message
    )


    client.is_running = True


    with patch(
        "app.websocket.btc_client.websockets.connect",
        AsyncMock(
            return_value=websocket
        )
    ):

        await asyncio.wait_for(
            client._run_websocket(),
            timeout=2
        )


    websocket.send.assert_called_once()

@pytest.mark.asyncio
async def test_run_websocket_invalid_json():

    client = BTCWebSocketClient()

    client.is_running = True


    websocket = MagicMock()

    websocket.send = AsyncMock()


    async def stop_after_invalid_message():

        client.is_running = False

        return "invalid json"


    websocket.recv = AsyncMock(
        side_effect=stop_after_invalid_message
    )


    with patch(
        "app.websocket.btc_client.websockets.connect",
        AsyncMock(
            return_value=websocket
        )
    ):

        await asyncio.wait_for(
            client._run_websocket(),
            timeout=2
        )


    websocket.send.assert_called_once()

# =====================================================
# properties
# =====================================================


def test_is_connected_false():

    client = BTCWebSocketClient()


    assert client.is_connected is False



def test_current_price_without_processor():

    client = BTCWebSocketClient()


    assert client.current_price is None



def test_current_price_with_processor():

    processor = MagicMock()

    processor.get_price.return_value = 60000


    client = BTCWebSocketClient(
        data_processor=processor
    )


    assert client.current_price == 60000



# =====================================================
# legacy support
# =====================================================


@pytest.mark.asyncio
async def test_process_btc_ticker_update_without_client():

    from app.websocket import btc_client


    btc_client._global_client = None


    result = await btc_client.process_btc_ticker_update(
        {
            "c": "60000"
        }
    )


    assert result is None