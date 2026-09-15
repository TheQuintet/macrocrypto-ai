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

logging.basicConfig(level=logging.INFO)
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

    async def get_btc_dominance(self) -> Dict[str, Any]:
        """
        Fetch current Bitcoin market dominance from CoinGecko.

        Returns:
            {
                "btc_dominance": float,
                "source": "coingecko"
            }
        """

        endpoint = f"{self.base_url}/global"

        try:
            logger.debug("Fetching BTC dominance from CoinGecko")

            response = await self.client.get(endpoint)
            response.raise_for_status()

            data = response.json()

            dominance = (
                data
                .get("data", {})
                .get("market_cap_percentage", {})
                .get("btc")
            )

            if dominance is None:
                logger.warning(
                    "BTC dominance missing from CoinGecko response"
                )
                return self._empty_dominance_response()

            return {
                "btc_dominance": float(dominance),
                "source": "coingecko",
            }

        except httpx.TimeoutException:
            logger.error(
                "Timeout fetching BTC dominance from CoinGecko"
            )
            return self._empty_dominance_response()

        except httpx.HTTPStatusError as error:
            logger.error(
                f"CoinGecko HTTP error: {error.response.status_code}"
            )
            return self._empty_dominance_response()

        except (TypeError, ValueError) as error:
            logger.error(
                f"Invalid BTC dominance response: {error}"
            )
            return self._empty_dominance_response()

        except Exception as error:
            logger.error(
                f"CoinGecko dominance collector error: {error}"
            )
            return self._empty_dominance_response()

    async def get_btc_dominance_history(
        self,
        days: int = 3650,
    ) -> list[dict]:
        """
        Fetch historical BTC dominance from CoinGecko.

        CoinGecko's market chart endpoint provides BTC market cap and
        total crypto market cap history. BTC dominance is calculated
        from those two series.
        """
        try:
            btc_url = f"{self.base_url}/coins/bitcoin/market_chart"
            global_url = f"{self.base_url}/global/market_cap_chart"

            params = {
                "vs_currency": "usd",
                "days": days,
            }

            btc_response = await self.client.get(
                btc_url,
                params=params,
            )
            btc_response.raise_for_status()

            global_response = await self.client.get(
                global_url,
                params=params,
            )
            global_response.raise_for_status()

            btc_data = btc_response.json()
            global_data = global_response.json()

            btc_market_caps = btc_data.get("market_caps", [])
            total_market_caps = global_data.get("market_cap_percentage", {})

            # This endpoint does not provide the total market-cap series
            # in the same structure needed here.
            # Do not persist incomplete data.
            if not btc_market_caps or not total_market_caps:
                logger.warning(
                    "CoinGecko returned incomplete BTC dominance history"
                )
                return []

            return []

        except Exception as error:
            logger.error(
                "Failed to fetch BTC dominance history: %s",
                error,
            )
            return []

    def _empty_dominance_response(self) -> Dict[str, Any]:
        """
        Return safe fallback response for BTC dominance.
        """
        return {
            "btc_dominance": 0.0,
            "source": "coingecko",
        }

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