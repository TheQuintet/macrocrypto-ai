"""Unit tests for the RabbitMQ client."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pika
import pytest

from app.core.rabbitmq import RabbitMQClient, rabbitmq_client


@pytest.fixture
def client():
    """Create a fresh RabbitMQ client."""
    return RabbitMQClient()


@pytest.fixture
def mock_connection():
    """Create a mocked RabbitMQ connection."""
    connection = MagicMock()
    connection.is_open = True
    connection.channel.return_value = MagicMock()
    return connection


@pytest.fixture
def mock_channel():
    """Create a mocked RabbitMQ channel."""
    return MagicMock()


class TestRabbitMQClientInitialization:
    """Test RabbitMQ client initialization."""

    def test_initialization(self, client):
        """Test default client state and configuration."""
        assert client._connection is None
        assert client._channel is None
        assert client._connected is False
        assert client._consuming is False
        assert client._retry_count == 0
        assert client._max_retries == 5
        assert client._queue_name == "api_gateway_websocket"
        assert client._routing_keys == ["price.updated"]

    def test_singleton_exists(self):
        """Test that the module exposes a singleton client."""
        assert isinstance(rabbitmq_client, RabbitMQClient)


class TestRabbitMQConnectionParameters:
    """Test RabbitMQ connection parameter creation."""

    def test_get_connection_params(self, client):
        """Test connection parameters contain configured values."""
        params = client._get_connection_params()

        assert isinstance(params, pika.ConnectionParameters)
        assert params.host == client._host
        assert params.port == client._port
        assert params.virtual_host == client._vhost
        assert params.heartbeat == 60
        assert params.blocked_connection_timeout == 300
        assert params.connection_attempts == 3
        assert params.retry_delay == 5


    def test_get_connection_params_uses_credentials(self, client):
        """Test configured username and password are used."""
        with patch(
            "app.core.rabbitmq.pika.PlainCredentials",
            wraps=pika.PlainCredentials,
        ) as mock_credentials:
            params = client._get_connection_params()

        mock_credentials.assert_called_once_with(
            client._user,
            client._password,
        )

        assert isinstance(params.credentials, pika.PlainCredentials)
        assert params.credentials.username == client._user
        assert params.credentials.password == client._password



class TestRabbitMQConnect:
    """Test RabbitMQ connection handling."""

    @pytest.mark.asyncio
    async def test_connect_success(
        self,
        client,
        mock_connection,
        mock_channel,
    ):
        """Test successful RabbitMQ connection."""
        mock_connection.channel.return_value = mock_channel

        with patch(
            "app.core.rabbitmq.pika.BlockingConnection",
            return_value=mock_connection,
        ) as mock_blocking_connection:
            result = await client.connect()

        assert result is True
        assert client._connection is mock_connection
        assert client._channel is mock_channel
        assert client._connected is True
        assert client._retry_count == 0

        mock_blocking_connection.assert_called_once()

        mock_channel.exchange_declare.assert_called_once_with(
            exchange=client._exchange,
            exchange_type="topic",
            durable=True,
        )

        mock_channel.queue_declare.assert_called_once_with(
            queue=client._queue_name,
            durable=True,
            arguments={"x-queue-type": "quorum"},
        )

        mock_channel.queue_bind.assert_called_once_with(
            exchange=client._exchange,
            queue=client._queue_name,
            routing_key="price.updated",
        )

    @pytest.mark.asyncio
    async def test_connect_failure(self, client):
        """Test connection failure returns False and resets state."""
        with patch(
            "app.core.rabbitmq.pika.BlockingConnection",
            side_effect=Exception("connection failed"),
        ):
            result = await client.connect()

        assert result is False
        assert client._connected is False

    @pytest.mark.asyncio
    async def test_connect_channel_failure(
        self,
        client,
        mock_connection,
    ):
        """Test failure while creating the channel."""
        mock_connection.channel.side_effect = Exception("channel failed")

        with patch(
            "app.core.rabbitmq.pika.BlockingConnection",
            return_value=mock_connection,
        ):
            result = await client.connect()

        assert result is False
        assert client._connected is False


class TestRabbitMQPublish:
    """Test event publishing."""

    def test_publish_when_not_connected(self, client):
        """Test publishing fails when client is disconnected."""
        result = client.publish_event(
            "PriceUpdated",
            {"price": 100},
            "price.updated",
        )

        assert result is False

    def test_publish_when_channel_missing(self, client):
        """Test publishing fails when channel is unavailable."""
        client._connected = True
        client._channel = None

        result = client.publish_event(
            "PriceUpdated",
            {"price": 100},
            "price.updated",
        )

        assert result is False

    def test_publish_success(self, client, mock_channel):
        """Test successful event publishing."""
        client._connected = True
        client._channel = mock_channel

        result = client.publish_event(
            "PriceUpdated",
            {"price": 100},
            "price.updated",
        )

        assert result is True
        mock_channel.basic_publish.assert_called_once()

        call_kwargs = mock_channel.basic_publish.call_args.kwargs

        assert call_kwargs["exchange"] == client._exchange
        assert call_kwargs["routing_key"] == "price.updated"

        message = json.loads(call_kwargs["body"])

        assert message["event_type"] == "PriceUpdated"
        assert message["data"] == {"price": 100}
        assert "timestamp" in message

        properties = call_kwargs["properties"]
        assert properties.delivery_mode == 2
        assert properties.content_type == "application/json"

    def test_publish_serialization_failure(
        self,
        client,
        mock_channel,
    ):
        """Test publishing handles serialization errors."""
        client._connected = True
        client._channel = mock_channel

        unserializable = {"value": object()}

        result = client.publish_event(
            "TestEvent",
            unserializable,
            "test.routing",
        )

        assert result is False
        mock_channel.basic_publish.assert_not_called()

    def test_publish_channel_failure(
        self,
        client,
        mock_channel,
    ):
        """Test publishing handles RabbitMQ channel errors."""
        client._connected = True
        client._channel = mock_channel
        mock_channel.basic_publish.side_effect = Exception("publish failed")

        result = client.publish_event(
            "TestEvent",
            {"value": 1},
            "test.routing",
        )

        assert result is False


class TestRabbitMQPriceUpdate:
    """Test price update message handling."""

    @pytest.mark.asyncio
    async def test_price_update_message(
        self,
        client,
        mock_channel,
    ):
        """Test valid PriceUpdated messages are broadcast."""
        method = MagicMock()
        method.delivery_tag = "delivery-1"

        body = json.dumps(
            {
                "event_type": "PriceUpdated",
                "data": {"price": 50000},
            }
        ).encode("utf-8")

        broadcast_task = AsyncMock()

        with patch(
            "app.core.rabbitmq.manager.broadcast_price_update",
            new=broadcast_task,
        ), patch(
            "app.core.rabbitmq.asyncio.create_task"
        ) as mock_create_task:
            client._on_price_update(
                mock_channel,
                method,
                MagicMock(),
                body,
            )

        mock_create_task.assert_called_once()
        mock_channel.basic_ack.assert_called_once_with(
            delivery_tag="delivery-1"
        )
        mock_channel.basic_nack.assert_not_called()

    def test_non_price_event_is_acknowledged(
        self,
        client,
        mock_channel,
    ):
        """Test non-price events are ignored but acknowledged."""
        method = MagicMock()
        method.delivery_tag = "delivery-2"

        body = json.dumps(
            {
                "event_type": "OtherEvent",
                "data": {"value": 123},
            }
        ).encode("utf-8")

        with patch("app.core.rabbitmq.asyncio.create_task") as mock_create_task:
            client._on_price_update(
                mock_channel,
                method,
                MagicMock(),
                body,
            )

        mock_create_task.assert_not_called()
        mock_channel.basic_ack.assert_called_once_with(
            delivery_tag="delivery-2"
        )
        mock_channel.basic_nack.assert_not_called()

    def test_invalid_json_is_requeued(
        self,
        client,
        mock_channel,
    ):
        """Test malformed messages are rejected and requeued."""
        method = MagicMock()
        method.delivery_tag = "delivery-3"

        client._on_price_update(
            mock_channel,
            method,
            MagicMock(),
            b"invalid-json",
        )

        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="delivery-3",
            requeue=True,
        )
        mock_channel.basic_ack.assert_not_called()

    def test_message_processing_error_is_requeued(
        self,
        client,
        mock_channel,
    ):
        """Test unexpected processing errors result in requeue."""
        method = MagicMock()
        method.delivery_tag = "delivery-4"

        with patch(
            "app.core.rabbitmq.json.loads",
            side_effect=RuntimeError("processing failed"),
        ):
            client._on_price_update(
                mock_channel,
                method,
                MagicMock(),
                b"{}",
            )

        mock_channel.basic_nack.assert_called_once_with(
            delivery_tag="delivery-4",
            requeue=True,
        )


class TestStartConsuming:
    """Test default price-update consumer."""

    def test_start_when_not_connected(self, client):
        """Test consuming cannot start while disconnected."""
        assert client.start_consuming() is False

    def test_start_when_channel_missing(self, client):
        """Test consuming cannot start without a channel."""
        client._connected = True
        client._channel = None

        assert client.start_consuming() is False

    def test_start_success(self, client, mock_channel):
        """Test successful consumer startup."""
        client._connected = True
        client._channel = mock_channel

        result = client.start_consuming()

        assert result is True
        assert client._consuming is True

        mock_channel.basic_qos.assert_called_once_with(
            prefetch_count=1
        )
        mock_channel.basic_consume.assert_called_once_with(
            queue=client._queue_name,
            on_message_callback=client._on_price_update,
            auto_ack=False,
        )

    def test_start_failure(self, client, mock_channel):
        """Test consumer startup failure."""
        client._connected = True
        client._channel = mock_channel
        mock_channel.basic_qos.side_effect = Exception("consumer failed")

        result = client.start_consuming()

        assert result is False
        assert client._consuming is False


class TestConsumeEvents:
    """Test custom event consumption."""

    def test_consume_when_not_connected(self, client):
        """Test custom consumption fails when disconnected."""
        callback = MagicMock()

        result = client.consume_events(
            "test_queue",
            ["test.event"],
            callback,
        )

        assert result is False

    def test_consume_success(self, client, mock_channel):
        """Test successful custom event consumption."""
        client._connected = True
        client._channel = mock_channel
        callback = MagicMock()

        result = client.consume_events(
            "test_queue",
            ["event.one", "event.two"],
            callback,
        )

        assert result is True

        mock_channel.queue_declare.assert_called_once_with(
            queue="test_queue",
            durable=True,
        )

        assert mock_channel.queue_bind.call_count == 2

        mock_channel.queue_bind.assert_any_call(
            exchange=client._exchange,
            queue="test_queue",
            routing_key="event.one",
        )
        mock_channel.queue_bind.assert_any_call(
            exchange=client._exchange,
            queue="test_queue",
            routing_key="event.two",
        )

        mock_channel.basic_consume.assert_called_once_with(
            queue="test_queue",
            on_message_callback=callback,
            auto_ack=False,
        )

    def test_consume_with_empty_routing_keys(
        self,
        client,
        mock_channel,
    ):
        """Test custom consumption works with no routing keys."""
        client._connected = True
        client._channel = mock_channel

        result = client.consume_events(
            "test_queue",
            [],
            MagicMock(),
        )

        assert result is True
        mock_channel.queue_declare.assert_called_once()
        mock_channel.queue_bind.assert_not_called()
        mock_channel.basic_consume.assert_called_once()

    def test_consume_failure(self, client, mock_channel):
        """Test custom consumption handles RabbitMQ errors."""
        client._connected = True
        client._channel = mock_channel
        mock_channel.queue_declare.side_effect = Exception(
            "queue declaration failed"
        )

        result = client.consume_events(
            "test_queue",
            ["test.event"],
            MagicMock(),
        )

        assert result is False


class TestStopConsuming:
    """Test stopping the consumer."""

    def test_stop_when_not_consuming(self, client, mock_channel):
        """Test stop does nothing when consumer is inactive."""
        client._channel = mock_channel
        client._consuming = False

        client.stop_consuming()

        mock_channel.stop_consuming.assert_not_called()

    def test_stop_when_no_channel(self, client):
        """Test stop does nothing when channel is unavailable."""
        client._channel = None
        client._consuming = True

        client.stop_consuming()

        assert client._consuming is True

    def test_stop_success(self, client, mock_channel):
        """Test successful consumer shutdown."""
        client._channel = mock_channel
        client._consuming = True

        client.stop_consuming()

        mock_channel.stop_consuming.assert_called_once()
        assert client._consuming is False

    def test_stop_failure(self, client, mock_channel):
        """Test consumer shutdown handles errors."""
        client._channel = mock_channel
        client._consuming = True
        mock_channel.stop_consuming.side_effect = Exception(
            "stop failed"
        )

        client.stop_consuming()

        assert client._consuming is True


class TestClose:
    """Test RabbitMQ connection closing."""

    def test_close_connection_and_channel(
        self,
        client,
        mock_connection,
        mock_channel,
    ):
        """Test channel and connection are closed."""
        client._channel = mock_channel
        client._connection = mock_connection
        client._connected = True
        client._consuming = True

        client.close()

        mock_channel.close.assert_called_once()
        mock_connection.close.assert_called_once()

        assert client._connected is False
        assert client._consuming is False

    def test_close_without_resources(self, client):
        """Test close works when nothing is connected."""
        client.close()

        assert client._connected is False
        assert client._consuming is False

    def test_close_failure(self, client, mock_connection, mock_channel):
        """Test close handles connection errors."""
        client._channel = mock_channel
        client._connection = mock_connection
        client._connected = True
        client._consuming = True

        mock_channel.close.side_effect = Exception("close failed")

        client.close()

        # Production code exits the try block after the first exception.
        assert client._connected is True
        assert client._consuming is True


class TestConnectionStatus:
    """Test connection status reporting."""

    def test_is_connected_true(
        self,
        client,
        mock_connection,
    ):
        """Test connected state when connection is open."""
        client._connection = mock_connection
        client._connected = True

        assert client.is_connected() is True

    def test_is_connected_false_when_flag_false(
        self,
        client,
        mock_connection,
    ):
        """Test status is false when connected flag is false."""
        client._connection = mock_connection
        client._connected = False

        assert client.is_connected() is False

    def test_is_connected_false_without_connection(self, client):
        """Test status is false without a connection."""
        client._connected = True
        client._connection = None

        assert client.is_connected() is False

    def test_is_connected_false_when_connection_closed(
        self,
        client,
        mock_connection,
    ):
        """Test status is false when RabbitMQ connection is closed."""
        mock_connection.is_open = False
        client._connection = mock_connection
        client._connected = True

        assert client.is_connected() is False

