"""Unit tests for BTCWebSocketClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.websocket.btc_client import BTCWebSocketClient
from app.services.data_processor import DataProcessor


class TestBTCWebSocketClient:
    """Test suite for BTCWebSocketClient."""

    def test_initialization(self):
        client = BTCWebSocketClient()
        assert client.data_processor is None
        assert client.rabbitmq_producer is None
        assert client.is_running is False
        assert client.task is None

    def test_initialization_with_services(self):
        data_processor = DataProcessor()
        client = BTCWebSocketClient(data_processor=data_processor)
        assert client.data_processor is data_processor

    @pytest.mark.asyncio
    async def test_start_stop(self):
        client = BTCWebSocketClient()
        with patch.object(client, "_run_websocket", new_callable=AsyncMock):
            await client.start()
            assert client.is_running is True
            assert client.task is not None

            await client.stop()
            assert client.is_running is False
            assert client.task is None

    @pytest.mark.asyncio
    async def test_process_message_with_price(self):
        client = BTCWebSocketClient()
        data = {
            "s": "BTCUSDT",
            "c": "45000.00",
            "o": "44000.00",
            "h": "46000.00",
            "l": "43500.00",
            "v": "1000.00",
            "P": "2.27",
            "p": "1000.00"
        }

        data_processor = MagicMock()
        client.data_processor = data_processor
        await client._process_message(data)
        data_processor.process_ticker_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_no_price(self):
        client = BTCWebSocketClient()
        data = {}
        await client._process_message(data)  # Should not raise exception

    @property
    def is_connected_false(self):
        client = BTCWebSocketClient()
        assert client.is_connected is False