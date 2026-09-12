"""
Yahoo Finance collector for market data.
"""

import logging
from typing import Optional

import httpx


logger = logging.getLogger(__name__)


class YahooFinanceCollector:
    """Collect market data from Yahoo Finance."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart"

    GOLD_SPOT_SYMBOL = "XAUUSD=X"
    GOLD_FUTURES_SYMBOL = "GC=F"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0,headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/140.0 Safari/537.36"
            )
        },)

    async def _get_latest_price(
        self,
        symbol: str,
    ) -> Optional[float]:
        """Get the latest price for a Yahoo Finance symbol."""

        try:
            response = await self.client.get(
                f"{self.BASE_URL}/{symbol}",
                params={
                    "range": "5d",
                    "interval": "1d",
                },
            )

            response.raise_for_status()

            data = response.json()

            result = data.get("chart", {}).get("result")

            if not result:
                return None

            meta = result[0].get("meta", {})

            price = (
                meta.get("regularMarketPrice")
                or meta.get("previousClose")
            )

            if price is None:
                return None

            return float(price)

        except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
            logger.warning(
                "Failed to fetch Yahoo Finance price for %s: %s",
                symbol,
                exc,
            )
            return None

    async def get_gold_spot(self) -> Optional[float]:
        """
        Get the latest gold price.

        XAUUSD=X is preferred as the gold spot price.
        GC=F is used as a fallback when spot is unavailable.
        """

        price = await self._get_latest_price(
            self.GOLD_SPOT_SYMBOL
        )

        if price is not None:
            return price

        logger.warning(
            "Gold spot price unavailable from %s; "
            "falling back to %s",
            self.GOLD_SPOT_SYMBOL,
            self.GOLD_FUTURES_SYMBOL,
        )

        return await self._get_latest_price(
            self.GOLD_FUTURES_SYMBOL
        )

    async def close(self):
        """Close the HTTP client."""

        await self.client.aclose()