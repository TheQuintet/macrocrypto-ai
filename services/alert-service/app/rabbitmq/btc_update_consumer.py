"""Background consumer for BTC price updates."""

import logging
import threading
from typing import Callable

import pika

from app.rabbitmq.consumer import RabbitMQConsumer

logger = logging.getLogger(__name__)


class BTCUpdateConsumer:
    """Run the existing price-update consumer on a dedicated Pika thread."""

    def __init__(
        self,
        consumer: RabbitMQConsumer,
        price_callback: Callable[[dict], None],
    ) -> None:
        self._consumer = consumer
        self._consumer.price_callback = price_callback
        self._stop_requested = threading.Event()
        self._thread = threading.Thread(
            target=self._consume,
            name="btc-price-update-consumer",
            daemon=True,
        )

    @property
    def is_connected(self) -> bool:
        return self._consumer.is_connected

    def start(self) -> None:
        """Connect and consume BTC updates without blocking FastAPI startup."""
        if self._thread.ident is None:
            self._thread.start()

    def _consume(self) -> None:
        try:
            if not self._consumer.connect():
                logger.error("BTC price update consumer could not connect")
                return

            if not self._stop_requested.is_set():
                self._consumer.start_consuming()
        except Exception:
            logger.exception("BTC price update consumer stopped unexpectedly")
        finally:
            connection = self._consumer.connection
            if connection and connection.is_open:
                self._consumer.close()
            else:
                self._consumer.is_connected = False

    def close(self) -> None:
        """Stop consuming and wait briefly for the Pika thread to exit."""
        self._stop_requested.set()
        connection = self._consumer.connection
        channel = self._consumer.channel

        if connection and connection.is_open and channel:
            try:
                connection.add_callback_threadsafe(channel.stop_consuming)
            except pika.exceptions.ConnectionWrongStateError:
                logger.debug("BTC consumer connection closed before shutdown")

        if self._thread.ident is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning("BTC price update consumer did not stop within 5 seconds")
