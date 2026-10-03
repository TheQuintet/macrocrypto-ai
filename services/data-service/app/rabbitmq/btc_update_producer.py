"""BTC price update producer using the shared data-service RabbitMQ setup."""

import logging
import math
from typing import Any, Dict

from app.rabbitmq.producer import RabbitMQProducer
from app.config import settings

logger = logging.getLogger(__name__)


class BTCUpdateProducer(RabbitMQProducer):
    """Publish BTC updates only after a configured move from the last publish."""

    def __init__(self) -> None:
        super().__init__()
        self._threshold_usd = settings.BTC_PRICE_RABBITMQ_THRESHOLD_USD
        self._last_published_prices: Dict[str, float] = {}

    def publish_btc_update(self, price_data: Dict[str, Any]) -> None:
        try:
            price = float(price_data["price"])
        except (KeyError, TypeError, ValueError):
            logger.error("Skipping BTC update with missing or invalid price")
            return

        if not math.isfinite(price):
            logger.error("Skipping BTC update with a non-finite price")
            return

        self.process_data_events()

        symbol = str(price_data.get("symbol", "BTCUSDT"))
        last_published_price = self._last_published_prices.get(symbol)
        if (
            last_published_price is not None
            and abs(price - last_published_price) < self._threshold_usd
        ):
            return

        event_data = {
            **price_data,
            "symbol": "BTC/USD" if symbol == "BTCUSDT" else symbol,
        }
        if last_published_price is not None:
            event_data["previous_price"] = last_published_price

        if self.publish_price_update(event_data):
            self._last_published_prices[symbol] = price
