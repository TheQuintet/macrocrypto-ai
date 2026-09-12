"""
Service for collecting and preparing the gold_spot feature.

gold_spot represents the latest gold price collected from Yahoo Finance.
XAUUSD=X is preferred, with GC=F as a fallback.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.collectors.yahoo_finance import YahooFinanceCollector
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)

logger = logging.getLogger(__name__)

GOLD_SPOT_INDICATOR = "gold_spot"


class GoldSpotService:
    """Collect and prepare the gold_spot feature."""

    def __init__(
        self,
        db,
        collector: YahooFinanceCollector | None = None,
    ):
        self.repository = MacroIndicatorRepository(db)
        self.collector = collector or YahooFinanceCollector()
        self._owns_collector = collector is None

    async def close(self) -> None:
        """Close the Yahoo Finance collector when owned by this service."""
        if self._owns_collector:
            await self.collector.close()

    async def collect(self) -> list[dict[str, Any]]:
        """
        Collect the latest gold spot price.

        Returns:
            Gold spot records ready for persistence.
        """

        price = await self.collector.get_gold_spot()

        if price is None:
            logger.warning(
                "No gold spot data available from Yahoo Finance"
            )
            return []

        record = {
            "indicator_name": GOLD_SPOT_INDICATOR,
            "time": datetime.now(timezone.utc),
            "value": float(price),
            "previous_value": None,
            "change_percent": None,
            "source": "yahoo_finance",
        }

        logger.info(
            "Collected %s: %.4f",
            GOLD_SPOT_INDICATOR,
            price,
        )

        return [record]

