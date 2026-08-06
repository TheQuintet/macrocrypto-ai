"""
CoinGecko API collector for Bitcoin market data.

Used for:
- BTC market capitalization

Market cap does not change every second, so this collector
should be called periodically (for example every 5-15 minutes)
and the value cached.
"""

import logging
from typing import Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CoinGeckoCollector:
    """
    Collector for CoinGecko market data.

    Currently collects:
    - Bitcoin market cap
    """

    def __init__(self):
        """Initialize CoinGecko collector."""
        self.base_url = settings.COINGECKO_API_URL
        self.timeout = 10.0
        self.client = httpx.AsyncClient(timeout=self.timeout)

        logger.info(
            f"CoinGeckoCollector initialized with endpoint: {self.base_url}"
        )

    async def get_btc_market_cap(self) -> Dict[str, Any]:
        """
        Fetch current Bitcoin market capitalization.

        Returns:
            {
                "market_cap": float,
                "source": "coingecko"
            }
        """

        endpoint = f"{self.base_url}/simple/price"

        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_market_cap": "true",
        }

        try:
            logger.debug("Fetching BTC market cap from CoinGecko")

            response = await self.client.get(
                endpoint,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

            market_cap = data.get(
                "bitcoin",
                {}
            ).get(
                "usd_market_cap",
                0,
            )

            return {
                "market_cap": float(market_cap),
                "source": "coingecko",
            }

        except httpx.TimeoutException:
            logger.error(
                "Timeout fetching BTC market cap from CoinGecko"
            )
            return self._empty_response()

        except httpx.HTTPStatusError as error:
            logger.error(
                f"CoinGecko HTTP error: {error.response.status_code}"
            )
            return self._empty_response()

        except Exception as error:
            logger.error(
                f"CoinGecko collector error: {error}"
            )
            return self._empty_response()

    def _empty_response(self) -> Dict[str, Any]:
        """
        Return safe fallback response.
        """
        return {
            "market_cap": 0.0,
            "source": "coingecko",
        }

    async def close(self):
        """
        Close HTTP client.
        """
        await self.client.aclose()