"""
Blockchain.com collector for Bitcoin on-chain data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class BlockchainCollector:
    """Collector for Bitcoin on-chain metrics from Blockchain.com."""

    BASE_URL = "https://api.blockchain.info/charts"
    ACTIVE_ADDRESSES_CHART = "n-unique-addresses"

    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: int = 30,
    ):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._owns_session = session is None

    async def _get(
        self,
        chart_name: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Fetch chart data from Blockchain.com."""

        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=self.timeout
            )

        url = f"{self.BASE_URL}/{chart_name}"

        try:
            async with self.session.get(
                url,
                params=params or {},
            ) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError:
            logger.exception(
                "Blockchain.com request failed: %s",
                url,
            )
            raise

    async def get_active_addresses(
        self,
        timespan: str = "1year",
        rolling_average: Optional[str] = None,
        start: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Get daily unique Bitcoin addresses used on the blockchain.

        Blockchain.com calls this metric "Unique Addresses Used".
        The project exposes it as the active_addresses feature.

        Args:
            timespan:
                Blockchain.com timespan such as "30days", "1year",
                "2years", or "all".
            rolling_average:
                Optional rolling-average parameter supported by the
                Blockchain.com Charts API.
            start:
                Optional start date accepted by the API.

        Returns:
            List of normalized records containing:
                - time
                - value
                - source
        """

        params: dict[str, Any] = {
            "timespan": timespan,
            "format": "json",
        }

        if rolling_average:
            params["rollingAverage"] = rolling_average

        if start:
            params["start"] = start

        data = await self._get(
            self.ACTIVE_ADDRESSES_CHART,
            params=params,
        )

        values = data.get("values", [])

        if not isinstance(values, list):
            logger.warning(
                "Unexpected active addresses response format"
            )
            return []

        records: list[dict[str, Any]] = []

        for item in values:
            if not isinstance(item, dict):
                continue

            timestamp = item.get("x")
            value = item.get("y")

            if timestamp is None or value is None:
                continue

            try:
                record_time = datetime.fromtimestamp(
                    float(timestamp),
                    tz=timezone.utc,
                )

                record_value = float(value)

            except (TypeError, ValueError, OSError):
                logger.warning(
                    "Skipping invalid active address record: %s",
                    item,
                )
                continue

            records.append(
                {
                    "time": record_time,
                    "value": record_value,
                    "source": "blockchain.com",
                }
            )

        logger.info(
            "Collected %d active address records from Blockchain.com",
            len(records),
        )

        return records

    async def close(self) -> None:
        """Close the HTTP session if this collector owns it."""

        if self.session is not None and self._owns_session:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> "BlockchainCollector":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()