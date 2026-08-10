"""
Service for collecting and caching BTC market capitalization data.
"""

import logging

from app.collectors.coingecko import CoinGeckoCollector
from app.config import settings

logger = logging.getLogger(__name__)


class MarketCapService:
    """
    Handles BTC market cap collection and Redis caching.
    """

    CACHE_KEY = "btc_market_cap"

    def __init__(self, cache_client):
        self.cache_client = cache_client
        self.collector = CoinGeckoCollector()

    async def update_market_cap(self) -> bool:
        """
        Fetch market cap from CoinGecko and store in Redis.
        """

        try:
            market_cap_data = await self.collector.get_btc_market_cap()

            return await self.cache_client.set(
                self.CACHE_KEY,
                market_cap_data,
                ttl=settings.MARKET_CAP_CACHE_TTL
            )

        except Exception as error:
            logger.error(
                f"Failed to update BTC market cap: {error}"
            )
            return False

    async def get_market_cap(self):
        """
        Get cached market cap.
        """

        return await self.cache_client.get(
            self.CACHE_KEY
        )

    async def close(self):
        """
        Close collector resources.
        """

        await self.collector.close()