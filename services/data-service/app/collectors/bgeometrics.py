import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class BGeometricsCollector:
    """Collector for historical Bitcoin market metrics."""

    BASE_URL = "https://bitcoin-data.com"
    BTC_DOMINANCE_ENDPOINT = "/v1/bitcoin-dominance"

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Accept": "application/json"},
            timeout=30.0,
        )

    async def get_btc_dominance_history(self) -> list[dict[str, Any]]:
        """Fetch historical daily Bitcoin dominance."""

        response = await self.client.get(
            self.BTC_DOMINANCE_ENDPOINT,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            raise RuntimeError(
                "Unexpected BGeometrics BTC dominance response"
            )

        return data

    async def close(self) -> None:
        await self.client.aclose()