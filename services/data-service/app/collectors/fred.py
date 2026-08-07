"""
FRED API collector for macroeconomic indicators.

Collects:
- CPI Inflation (YoY)
- Federal Funds Rate
- M2 Money Supply
- US Dollar Index (DXY)
- 10-Year Treasury Yield
- GDP
- Unemployment Rate

This collector only retrieves data.
Storage, calculations, and trend analysis
are handled by later services.
"""

import asyncio
import logging
from typing import Dict, Any

import httpx

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FREDCollector:
    """
    Collector for Federal Reserve Economic Data (FRED).

    Features:
    - Async FRED API client
    - API key authentication
    - Rate limiting
    - Error handling
    - Logging
    """

    def __init__(self):
        """
        Initialize FRED collector.
        """

        self.base_url = settings.FRED_API_URL
        self.api_key = settings.FRED_API_KEY
        self.timeout = 10.0
        self.request_delay = settings.FRED_REQUEST_DELAY

        self.client = httpx.AsyncClient(
            timeout=self.timeout
        )

        logger.info(
            f"FREDCollector initialized with endpoint: {self.base_url}"
        )

    async def _get_series(
        self,
        series_id: str
    ) -> Dict[str, Any]:
        """
        Fetch observations for a FRED series.
        """

        if not self.api_key:
            logger.error(
                "FRED API key is missing"
            )

            return {}

        endpoint = (
            f"{self.base_url}/series/observations"
        )

        params = {
            "series_id": series_id,
            "api_key": self.api_key,
            "file_type": "json",
            "sort_order": "desc",
        }

        try:
            # Respect FRED API rate limits
            await asyncio.sleep(
                self.request_delay
            )

            logger.info(
                f"Fetching FRED series: {series_id}"
            )

            response = await self.client.get(
                endpoint,
                params=params,
            )

            response.raise_for_status()

            data = response.json()

            logger.info(
                f"Successfully fetched FRED series: {series_id}"
            )

            return data

        except httpx.TimeoutException:
            logger.error(
                f"Timeout fetching FRED series: {series_id}"
            )

            return {}

        except httpx.HTTPStatusError as error:
            logger.error(
                f"FRED HTTP error "
                f"{error.response.status_code} "
                f"for series {series_id}"
            )

            return {}

        except Exception as error:
            logger.error(
                f"FRED collector error for {series_id}: {error}"
            )

            return {}

    async def get_cpi(self) -> Dict[str, Any]:
        """
        Get CPI inflation data.
        """

        return await self._get_series(
            settings.FRED_CPI_SERIES
        )

    async def get_federal_funds_rate(self) -> Dict[str, Any]:
        """
        Get Federal Funds Rate data.
        """

        return await self._get_series(
            settings.FRED_FED_FUNDS_SERIES
        )

    async def get_m2_money_supply(self) -> Dict[str, Any]:
        """
        Get M2 Money Supply data.
        """

        return await self._get_series(
            settings.FRED_M2_SERIES
        )

    async def get_dxy(self) -> Dict[str, Any]:
        """
        Get US Dollar Index data.
        """

        return await self._get_series(
            settings.FRED_DXY_SERIES
        )

    async def get_ten_year_treasury(self) -> Dict[str, Any]:
        """
        Get 10-Year Treasury Yield data.
        """

        return await self._get_series(
            settings.FRED_TREASURY_10Y_SERIES
        )

    async def get_gdp(self) -> Dict[str, Any]:
        """
        Get GDP data.
        """

        return await self._get_series(
            settings.FRED_GDP_SERIES
        )

    async def get_unemployment(self) -> Dict[str, Any]:
        """
        Get unemployment rate data.
        """

        return await self._get_series(
            settings.FRED_UNEMPLOYMENT_SERIES
        )

    async def get_all_indicators(self) -> Dict[str, Any]:
        """
        Fetch all configured FRED economic indicators.
        """

        logger.info(
            "Fetching all FRED economic indicators"
        )

        return {
            "cpi": await self.get_cpi(),

            "federal_funds_rate": (
                await self.get_federal_funds_rate()
            ),

            "m2_money_supply": (
                await self.get_m2_money_supply()
            ),

            "dxy": await self.get_dxy(),

            "ten_year_treasury": (
                await self.get_ten_year_treasury()
            ),

            "gdp": await self.get_gdp(),

            "unemployment": (
                await self.get_unemployment()
            ),
        }

    async def close(self):
        """
        Close HTTP client.
        """

        await self.client.aclose()

        logger.info(
            "FREDCollector closed"
        )