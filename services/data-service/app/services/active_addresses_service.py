"""
Service for collecting and preparing the active_addresses feature.

active_addresses represents the daily number of unique Bitcoin addresses
used on the blockchain, collected from Blockchain.com.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.collectors.blockchain import BlockchainCollector
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)

logger = logging.getLogger(__name__)

ACTIVE_ADDRESSES_INDICATOR = "active_addresses"

TIMESPAN = "1year"


class ActiveAddressesService:
    """Collect and prepare the active_addresses feature."""

    def __init__(
        self,
        db,
        collector: BlockchainCollector | None = None,
    ):
        self.repository = MacroIndicatorRepository(db)
        self.collector = collector or BlockchainCollector()
        self._owns_collector = collector is None

    async def close(self) -> None:
        """Close the Blockchain collector when owned by this service."""
        if self._owns_collector:
            await self.collector.close()

    async def calculate(self) -> list[dict[str, Any]]:
        """
        Collect daily active-address observations.

        Returns:
            Active-address records ready for persistence.
        """

        records = await self.collector.get_active_addresses(
            timespan=TIMESPAN,
        )

        if not records:
            logger.warning(
                "No active address data available from Blockchain.com"
            )
            return []

        # Ensure observations are processed chronologically.
        records = sorted(
            records,
            key=lambda record: record["time"],
        )

        result: list[dict[str, Any]] = []

        for index, record in enumerate(records):
            current_value = float(record["value"])
            record_time = record["time"]

            previous_value: float | None = None
            change_percent: float | None = None

            if index > 0:
                previous_value = float(records[index - 1]["value"])

                if previous_value != 0:
                    change_percent = (
                        (current_value - previous_value)
                        / previous_value
                    ) * 100

            result.append(
                {
                    "indicator_name": ACTIVE_ADDRESSES_INDICATOR,
                    "time": record_time,
                    "value": current_value,
                    "previous_value": previous_value,
                    "change_percent": (
                        round(change_percent, 4)
                        if change_percent is not None
                        else None
                    ),
                    "source": "blockchain.com",
                }
            )

        logger.info(
            "Collected %d %s records",
            len(result),
            ACTIVE_ADDRESSES_INDICATOR,
        )

        return result