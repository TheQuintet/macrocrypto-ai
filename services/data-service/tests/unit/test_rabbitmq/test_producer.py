"""Unit tests for RabbitMQProducer."""

import pytest
from unittest.mock import MagicMock, patch
from app.rabbitmq.producer import RabbitMQProducer


class TestRabbitMQProducer:
    """Test suite for RabbitMQProducer."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        producer = RabbitMQProducer()
        mock_connection = MagicMock()
        mock_channel = MagicMock()

        with patch("app.rabbitmq.producer.pika.BlockingConnection", return_value=mock_connection):
            mock_connection.channel.return_value = mock_channel
            result = await producer.connect()
            assert result is True
            assert producer.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_failure(self):
        producer = RabbitMQProducer()
        with patch("app.rabbitmq.producer.pika.BlockingConnection", side_effect=Exception("Connection failed")):
            result = await producer.connect()
            assert result is False
            assert producer.is_connected is False

    def test_publish_price_update_not_connected(self):
        producer = RabbitMQProducer()
        with patch.object(producer, "_connect", return_value=False) as connect:
            published = producer.publish_price_update(
                {"symbol": "BTCUSDT", "price": 45000.0}
            )

        assert published is False
        connect.assert_called_once()

    def test_publish_price_update_reconnects_after_channel_closes(self):
        producer = RabbitMQProducer()
        producer.is_connected = True
        producer.connection = MagicMock(is_open=True)
        producer.channel = MagicMock(is_open=False)
        replacement_connection = MagicMock(is_open=True)
        replacement_channel = MagicMock(is_open=True)

        def reconnect():
            producer.connection = replacement_connection
            producer.channel = replacement_channel
            producer.is_connected = True
            return True

        with patch.object(producer, "_connect", side_effect=reconnect) as connect:
            published = producer.publish_price_update(
                {"symbol": "BTC/USD", "price": 45000.0}
            )

        assert published is True
        connect.assert_called_once()
        replacement_channel.basic_publish.assert_called_once()

    def test_close(self):
        producer = RabbitMQProducer()
        mock_connection = MagicMock()
        producer.connection = mock_connection
        producer.is_connected = True
        producer.close()
        mock_connection.close.assert_called_once()