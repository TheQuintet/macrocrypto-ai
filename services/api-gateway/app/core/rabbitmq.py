"""RabbitMQ client for event production and consumption.

This module provides a RabbitMQ client for publishing events and
consuming price updates for WebSocket broadcasts.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone

import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from pika.spec import Basic, BasicProperties

from app.core.config import settings
from app.core.websocket_manager import manager

logger = logging.getLogger(settings.SERVICE_NAME)


class RabbitMQClient:
    """RabbitMQ client for event production and consumption.

    Handles:
    - Publishing events to RabbitMQ
    - Consuming price updates for WebSocket broadcasts
    - Connection management with retry logic
    """

    def __init__(self):
        """Initialize the RabbitMQ client."""
        self._connection = None
        self._channel = None
        self._connected = False
        self._consuming = False
        self._retry_count = 0
        self._max_retries = 5
        self._exchange = settings.RABBITMQ_EXCHANGE
        self._queue_name = "api_gateway_websocket"
        self._routing_keys = ["price.updated"]

        self._host = settings.RABBITMQ_HOST
        self._port = settings.RABBITMQ_PORT
        self._user = settings.RABBITMQ_USER
        self._password = settings.RABBITMQ_PASSWORD
        self._vhost = settings.RABBITMQ_VHOST

        logger.info("RabbitMQ client initialized")

    def _get_connection_params(self) -> pika.ConnectionParameters:
        """Get RabbitMQ connection parameters.

        Returns:
            pika.ConnectionParameters: Connection parameters.
        """
        credentials = pika.PlainCredentials(self._user, self._password)
        return pika.ConnectionParameters(
            host=self._host,
            port=self._port,
            virtual_host=self._vhost,
            credentials=credentials,
            heartbeat=60,
            blocked_connection_timeout=300,
            connection_attempts=3,
            retry_delay=5,
        )

    async def connect(self) -> bool:
        """Establish connection to RabbitMQ.

        Returns:
            bool: True if connected, False otherwise.
        """
        try:
            # Use synchronous connection for simplicity
            # In production, use AsyncioConnection
            params = self._get_connection_params()
            self._connection = pika.BlockingConnection(params)
            self._channel = self._connection.channel()

            # Declare exchange
            self._channel.exchange_declare(
                exchange=self._exchange,
                exchange_type='topic',
                durable=True,
            )

            # Declare queue
            self._channel.queue_declare(
                queue=self._queue_name,
                durable=True,
                arguments={
                    'x-queue-type': 'quorum',
                }
            )

            # Bind queue to routing keys
            for routing_key in self._routing_keys:
                self._channel.queue_bind(
                    exchange=self._exchange,
                    queue=self._queue_name,
                    routing_key=routing_key,
                )

            self._connected = True
            self._retry_count = 0
            logger.info(f"✅ RabbitMQ connected: {self._host}:{self._port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self._connected = False
            return False

    def publish_event(self, event_type: str, data: Dict[str, Any], routing_key: str) -> bool:
        """Publish an event to RabbitMQ.

        Args:
            event_type: The type of event to publish.
            data: The event data payload.
            routing_key: The routing key for the event.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not self._connected or not self._channel:
            logger.warning("RabbitMQ not connected, cannot publish event")
            return False

        try:
            message = {
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            self._channel.basic_publish(
                exchange=self._exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json',
                ),
            )

            logger.debug(f"Event published: {event_type} -> {routing_key}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False

    def _on_price_update(self, channel: Channel, method: Basic.Deliver, properties: BasicProperties, body: bytes) -> None:
        """Handle incoming price update messages.

        Args:
            channel: The RabbitMQ channel.
            method: The delivery method.
            properties: The message properties.
            body: The message body.
        """
        try:
            message = json.loads(body.decode('utf-8'))
            event_type = message.get("event_type")
            data = message.get("data", {})

            logger.info(f"Received price update: {event_type}")

            # Broadcast to WebSocket clients
            if event_type == "PriceUpdated":
                asyncio.create_task(manager.broadcast_price_update(data))
            else:
                logger.debug(f"Ignoring event type: {event_type}")

            # Acknowledge the message
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            # Reject and requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Reject and requeue
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self) -> bool:
        """Start consuming price update messages.

        Returns:
            bool: True if started, False otherwise.
        """
        if not self._connected or not self._channel:
            logger.warning("RabbitMQ not connected, cannot start consuming")
            return False

        try:
            # Set QoS to prefetch 1 message at a time
            self._channel.basic_qos(prefetch_count=1)

            # Start consuming
            self._channel.basic_consume(
                queue=self._queue_name,
                on_message_callback=self._on_price_update,
                auto_ack=False,
            )

            self._consuming = True
            logger.info(f"✅ Started consuming price updates from queue: {self._queue_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to start consuming: {e}")
            return False

    def consume_events(self, queue_name: str, routing_keys: list, callback: Callable) -> bool:
        """Consume events from RabbitMQ with custom callback.

        Args:
            queue_name: The queue name.
            routing_keys: List of routing keys to bind.
            callback: Callback function for messages.

        Returns:
            bool: True if started, False otherwise.
        """
        if not self._connected or not self._channel:
            logger.warning("RabbitMQ not connected, cannot consume events")
            return False

        try:
            # Declare queue if not exists
            self._channel.queue_declare(
                queue=queue_name,
                durable=True,
            )

            # Bind queue to routing keys
            for routing_key in routing_keys:
                self._channel.queue_bind(
                    exchange=self._exchange,
                    queue=queue_name,
                    routing_key=routing_key,
                )

            # Start consuming
            self._channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback,
                auto_ack=False,
            )

            logger.info(f"Started consuming from queue: {queue_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to consume events: {e}")
            return False

    def stop_consuming(self) -> None:
        """Stop consuming messages."""
        if self._channel and self._consuming:
            try:
                self._channel.stop_consuming()
                self._consuming = False
                logger.info("Stopped consuming messages")
            except Exception as e:
                logger.error(f"Error stopping consumer: {e}")

    def close(self) -> None:
        """Close the RabbitMQ connection."""
        try:
            if self._channel:
                self._channel.close()
            if self._connection:
                self._connection.close()
            self._connected = False
            self._consuming = False
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ: {e}")

    def is_connected(self) -> bool:
        """Check if the client is connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connected and self._connection is not None and self._connection.is_open


# ============================================
# SINGLETON INSTANCE
# ============================================

rabbitmq_client = RabbitMQClient()