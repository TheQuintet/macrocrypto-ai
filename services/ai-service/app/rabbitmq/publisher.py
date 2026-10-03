"""RabbitMQ publisher for the AI Service.

A one-shot publish helper used by scheduler jobs to announce
events (e.g. ModelsRetrained) on the configured exchange.

Design:

    - Best-effort. Every public method logs failures and returns
      a bool rather than raising. A caller wiring this into a
      scheduler job should never have to catch.

    - Lazy connection. The first publish() call opens the
      connection; subsequent calls reuse it. close() closes.

    - One instance per publish site is fine. The class is small
      enough that constructing a fresh instance per job run is
      cheap — no pooling needed.

Usage:

    publisher = RabbitMQPublisher()
    ok = await publisher.publish(
        routing_key="intelligence.forecast.generated",
        payload={"event": "ModelsRetrained", "count": 6},
    )
    await publisher.close()

Configuration:
    Same rabbitmq_* settings as the consumer.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractRobustConnection,
)

from app.config import settings

logger = logging.getLogger(__name__)


class RabbitMQPublisher:
    """Lightweight RabbitMQ publish helper.

    Not a long-lived singleton — instantiate where needed. The
    connection is opened lazily on first publish.
    """

    def __init__(self) -> None:
        """Initialize the publisher. No I/O happens here."""
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def publish(
        self,
        routing_key: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Publish a JSON payload to the exchange.

        Args:
            routing_key: The routing key to publish under. The
                exchange uses topic routing, so wildcards are
                allowed in bindings but not in the publish key.
            payload: A JSON-serializable dict. A `timestamp` field
                is added automatically if not present.

        Returns:
            True on successful publish; False on any failure.
            Never raises.
        """
        try:
            channel = await self._ensure_channel()
            if channel is None:
                return False

            # Inject a timestamp if the caller didn't provide one.
            if "timestamp" not in payload:
                payload = {
                    **payload,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

            body = json.dumps(payload, default=str).encode("utf-8")

            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=routing_key,
            )

            logger.info(
                f"Published to routing_key={routing_key!r} "
                f"({len(body)}B)"
            )
            return True

        except Exception as e:
            logger.warning(
                f"Failed to publish to routing_key={routing_key!r}: {e}"
            )
            return False

    async def close(self) -> None:
        """Close the channel and connection if open.

        Idempotent. Never raises.
        """
        if self._channel is not None:
            try:
                await self._channel.close()
            except Exception as e:
                logger.debug(f"Error closing publisher channel: {e}")
            self._channel = None

        if self._connection is not None:
            try:
                await self._connection.close()
            except Exception as e:
                logger.debug(f"Error closing publisher connection: {e}")
            self._connection = None

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================
    async def _ensure_channel(self) -> Optional[AbstractChannel]:
        """Return a live channel, opening one if needed.

        Returns None on any failure (with a log line). Never
        raises.
        """
        if self._channel is not None and not self._channel.is_closed:
            return self._channel

        try:
            if self._connection is None or self._connection.is_closed:
                logger.debug("Opening RabbitMQ publisher connection")
                self._connection = await aio_pika.connect_robust(
                    settings.rabbitmq_url
                )

            self._channel = await self._connection.channel()

            # Declare the exchange so publishes succeed even if no
            # consumer has connected yet.
            await self._channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            return self._channel

        except Exception as e:
            logger.warning(
                f"Could not open RabbitMQ publisher channel: {e}"
            )
            # Clean up partial state so the next call retries fresh.
            await self.close()
            return None