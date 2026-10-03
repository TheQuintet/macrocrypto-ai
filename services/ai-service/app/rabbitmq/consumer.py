"""RabbitMQ consumer for the AI Service.

Subscribes to two queues:
    - ai.price.queue       (routing key: *.price.*)
    - ai.indicator.queue   (routing key: *.economic.*)

On each message: log the routing key and a short summary, then
ack. No side effects — this is "lightweight wiring" that
justifies the rabbitmq_* config and lays the groundwork for a
future event-driven architecture.

Design:

    - Best-effort. If RabbitMQ is unavailable at startup, the
      consumer logs a WARNING and disables itself. The service
      continues running normally.

    - Idempotent start() / stop(). Calling either twice is safe.
      Matches the FastAPI lifespan pattern (startup / shutdown).

    - The exchange and queues are declared durable on startup.
      If they already exist with compatible settings, declare is
      a no-op. If they exist with incompatible settings, declare
      raises and the consumer disables itself.

    - Messages are always acked, never nacked. For log-only
      consumption, we don't want poison messages looping.

    - Graceful shutdown cancels the consume tasks with a short
      timeout, then closes the channel and connection.

Configuration:
    All values come from `settings` (app/config.py):
        rabbitmq_host, rabbitmq_port, rabbitmq_username,
        rabbitmq_password, rabbitmq_vhost, rabbitmq_exchange,
        rabbitmq_price_queue, rabbitmq_indicator_queue,
        rabbitmq_price_routing_key, rabbitmq_indicator_routing_key
"""

import asyncio
import json
import logging
from typing import Optional

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractRobustConnection,
    AbstractRobustQueue,
)

from app.config import settings

logger = logging.getLogger(__name__)


# Grace period for cancelling the consume tasks on shutdown.
# Long enough that an in-flight message handler can finish;
# short enough that shutdown stays snappy.
_SHUTDOWN_TIMEOUT_SECONDS = 5.0


class RabbitMQConsumer:
    """Lightweight RabbitMQ consumer.

    Usage in FastAPI lifespan:

        consumer = RabbitMQConsumer()
        await consumer.start()   # best-effort; never raises

        ...

        await consumer.stop()    # idempotent
    """

    def __init__(self) -> None:
        """Initialize the consumer.

        No I/O happens here — everything is deferred to start().
        """
        self._connection: Optional[AbstractRobustConnection] = None
        self._channel: Optional[AbstractChannel] = None
        self._tasks: list[asyncio.Task] = []
        self._enabled = False

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def start(self) -> None:
        """Connect to RabbitMQ and begin consuming.

        Best-effort. On any failure, logs a WARNING and leaves
        `self._enabled` False. Never raises.
        """
        if self._enabled:
            logger.debug("RabbitMQConsumer.start() called twice — no-op")
            return

        url = settings.rabbitmq_url
        # Redact password in log output.
        safe_url = url.replace(settings.rabbitmq_password, "***") if settings.rabbitmq_password else url

        try:
            logger.info(f"Connecting to RabbitMQ at {safe_url}")
            self._connection = await aio_pika.connect_robust(url)
            self._channel = await self._connection.channel()
            await self._channel.set_qos(prefetch_count=10)

            # Declare the topic exchange. Durable so it survives
            # broker restarts.
            exchange = await self._channel.declare_exchange(
                settings.rabbitmq_exchange,
                aio_pika.ExchangeType.TOPIC,
                durable=True,
            )

            # Declare + bind both queues.
            price_queue = await self._declare_and_bind(
                exchange,
                queue_name=settings.rabbitmq_price_queue,
                routing_key=settings.rabbitmq_price_routing_key,
            )
            indicator_queue = await self._declare_and_bind(
                exchange,
                queue_name=settings.rabbitmq_indicator_queue,
                routing_key=settings.rabbitmq_indicator_routing_key,
            )

            # Start consuming both queues as background tasks.
            self._tasks.append(
                asyncio.create_task(
                    self._consume_loop(price_queue, "price"),
                    name="rabbitmq-consumer-price",
                )
            )
            self._tasks.append(
                asyncio.create_task(
                    self._consume_loop(indicator_queue, "indicator"),
                    name="rabbitmq-consumer-indicator",
                )
            )

            self._enabled = True
            logger.info(
                f"RabbitMQConsumer started "
                f"(exchange={settings.rabbitmq_exchange!r}, "
                f"queues=[{settings.rabbitmq_price_queue!r}, "
                f"{settings.rabbitmq_indicator_queue!r}])"
            )

        except Exception as e:
            logger.warning(
                f"RabbitMQ consumer could not start: {e}. "
                f"The service will continue without message consumption."
            )
            # Clean up any partial state.
            await self._close_quietly()
            self._enabled = False

    async def stop(self) -> None:
        """Cancel consume tasks and close the connection.

        Idempotent. Never raises.
        """
        if not self._enabled and not self._tasks and self._connection is None:
            return

        logger.info("Stopping RabbitMQConsumer")

        # Cancel the consume tasks.
        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._tasks, return_exceptions=True),
                    timeout=_SHUTDOWN_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "RabbitMQConsumer: consume tasks did not cancel "
                    "within timeout; proceeding with shutdown"
                )

        self._tasks.clear()
        await self._close_quietly()
        self._enabled = False
        logger.info("RabbitMQConsumer stopped")

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================
    async def _declare_and_bind(
        self,
        exchange,
        queue_name: str,
        routing_key: str,
    ) -> AbstractRobustQueue:
        """Declare a durable queue and bind it to the exchange."""
        assert self._channel is not None
        queue = await self._channel.declare_queue(
            queue_name, durable=True
        )
        await queue.bind(exchange, routing_key=routing_key)
        logger.debug(
            f"Bound queue {queue_name!r} to "
            f"exchange {settings.rabbitmq_exchange!r} "
            f"with routing key {routing_key!r}"
        )
        return queue

    async def _consume_loop(
        self,
        queue: AbstractRobustQueue,
        label: str,
    ) -> None:
        """Consume messages from a queue until cancelled.

        Args:
            queue: The declared, bound queue.
            label: Human-readable label ("price" or "indicator")
                used in log lines.
        """
        try:
            async with queue.iterator() as iterator:
                async for message in iterator:
                    await self._handle_message(message, label)
        except asyncio.CancelledError:
            logger.debug(f"RabbitMQConsumer: {label} consumer cancelled")
            raise
        except Exception as e:
            logger.warning(
                f"RabbitMQConsumer: {label} consumer crashed: {e}",
                exc_info=True,
            )

    async def _handle_message(
        self,
        message: AbstractIncomingMessage,
        label: str,
    ) -> None:
        """Log a received message and ack it.

        Never raises — a message handler failure logs a warning
        but does not crash the consumer or the message remains
        unacked. We always ack, including on handler errors, to
        avoid poison-message loops for a log-only consumer.
        """
        try:
            body = message.body
            size = len(body)
            summary = self._summarize_body(body)
            logger.info(
                f"[{label}] received message "
                f"(routing_key={message.routing_key!r}, "
                f"size={size}B, "
                f"summary={summary})"
            )
        except Exception as e:
            logger.warning(
                f"[{label}] failed to process message: {e}",
                exc_info=True,
            )
        finally:
            # Always ack — log-only consumer, no retries.
            try:
                await message.ack()
            except Exception as e:
                logger.debug(
                    f"[{label}] could not ack message "
                    f"(channel may be closing): {e}"
                )

    @staticmethod
    def _summarize_body(body: bytes) -> str:
        """Return a short, safe summary of a message body.

        If the body parses as JSON and is a dict, shows the top-
        level keys. Otherwise shows the first N bytes as text.
        Never raises.
        """
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:
            return f"<{len(body)}B>"

        try:
            parsed = json.loads(text)
        except (ValueError, TypeError):
            # Not JSON — truncate to keep the log line short.
            return text[:60] + ("..." if len(text) > 60 else "")

        if isinstance(parsed, dict):
            keys = list(parsed.keys())[:8]
            suffix = "..." if len(parsed) > 8 else ""
            return f"keys={keys}{suffix}"
        if isinstance(parsed, list):
            return f"list[length={len(parsed)}]"
        return f"<{type(parsed).__name__}>"

    async def _close_quietly(self) -> None:
        """Close channel and connection without raising.

        Used both on graceful shutdown and on partial-startup
        failure. Every step is guarded so a broken channel does
        not prevent the connection from being closed, and vice
        versa.
        """
        if self._channel is not None:
            try:
                await self._channel.close()
            except Exception as e:
                logger.debug(f"Error closing channel: {e}")
            self._channel = None

        if self._connection is not None:
            try:
                await self._connection.close()
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
            self._connection = None