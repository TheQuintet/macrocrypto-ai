"""
Service for collecting, storing, and caching BTC dominance.
"""

import logging
from datetime import datetime, timezone

from app.collectors.coingecko import CoinGeckoCollector
from app.config import settings
from app.database.btc_dominance_repository import (
    BTCDominanceRepository,
)

logger = logging.getLogger(__name__)


class BTCDominanceService:
    """
    Handles BTC dominance collection, persistence, and caching.
    """

    CACHE_KEY = "btc_dominance"

    def __init__(self, db, cache_client=None):
        self.db = db
        self.cache_client = cache_client
        self.collector = CoinGeckoCollector()
        self.repository = BTCDominanceRepository(db)

    async def update_dominance(self) -> bool:
        """
        Fetch BTC dominance from CoinGecko and persist it.
        """

        try:
            data = await self.collector.get_btc_dominance()

            dominance = data.get("btc_dominance", 0.0)

            if dominance <= 0:
                logger.warning(
                    "Invalid BTC dominance received from CoinGecko"
                )
                return False

            timestamp = datetime.now(timezone.utc)

            record = self.repository.create(
                time=timestamp,
                dominance=dominance,
                source=data.get("source", "coingecko"),
            )

            response = {
                "btc_dominance": record.dominance,
                "time": record.time,
                "source": record.source,
            }

            if self.cache_client:
                await self.cache_client.set(
                    self.CACHE_KEY,
                    response,
                    ttl=settings.BTC_DOMINANCE_CACHE_TTL,
                )

            return True

        except Exception as error:
            logger.error(
                f"Failed to update BTC dominance: {error}"
            )
            return False

    async def get_dominance(self) -> dict | None:
        """
        Get the latest BTC dominance.

        Redis is checked first, followed by TimescaleDB.
        """

        if self.cache_client:
            cached = await self.cache_client.get(
                self.CACHE_KEY
            )

            if cached:
                return cached

        record = self.repository.get_latest()

        if not record:
            return None

        response = {
            "btc_dominance": record.dominance,
            "time": record.time,
            "source": record.source,
        }

        if self.cache_client:
            await self.cache_client.set(
                self.CACHE_KEY,
                response,
                ttl=settings.BTC_DOMINANCE_CACHE_TTL,
            )

        return response

    async def close(self):
        await self.collector.close()