"""
Service for processing and storing macroeconomic indicators.

Responsibilities:

- Fetch data from FRED
- Parse observations
- Calculate previous values
- Calculate percentage changes
- Store historical data
- Invalidate Redis cache after updates
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any

from app.collectors.fred import FREDCollector
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)


logger = logging.getLogger(__name__)


class IndicatorService:
    """
    Handles macroeconomic indicator processing.

    Responsibilities:

    - Collect macroeconomic data from FRED.
    - Transform FRED observations.
    - Store indicator history in TimescaleDB.
    - Provide indicator data to the API.
    """

    def __init__(
        self,
        db,
        cache_client=None,
    ):
        """
        Initialize indicator service.

        Args:
            db:
                Database session.

            cache_client:
                Optional Redis cache client.
        """

        # Lazy initialization.
        # API reads do not need FRED.
        self.collector = None

        self.repository = MacroIndicatorRepository(
            db
        )

        self.cache_client = cache_client

    def get_collector(self):
        """
        Lazy initialize FRED collector.

        FRED is only required when updating
        indicators, not when reading them.
        """

        if self.collector is None:
            self.collector = FREDCollector()

        return self.collector

    def calculate_change_percent(
        self,
        current_value: float,
        previous_value: float | None,
    ) -> float | None:
        """
        Calculate percentage change between values.
        """

        if previous_value is None:
            return None

        if previous_value == 0:
            return None

        return (
            (current_value - previous_value)
            / previous_value
        ) * 100

    def parse_observations(
        self,
        indicator_name: str,
        response: Dict[str, Any],
    ) -> list[dict]:
        """
        Convert FRED observations into database records.
        """

        observations = response.get(
            "observations",
            [],
        )

        if not observations:
            logger.warning(
                f"No observations found for {indicator_name}"
            )

            return []

        records = []

        for index, observation in enumerate(
            observations
        ):
            try:
                value = observation["value"]

                if value == ".":
                    continue

                current_value = float(value)

                previous_value = None

                if index + 1 < len(observations):
                    previous_raw = (
                        observations[index + 1]["value"]
                    )

                    if previous_raw != ".":
                        previous_value = float(
                            previous_raw
                        )

                change_percent = (
                    self.calculate_change_percent(
                        current_value,
                        previous_value,
                    )
                )

                record = {
                    "indicator_name": indicator_name,
                    "time": datetime.fromisoformat(
                        observation["date"]
                    ).replace(
                        tzinfo=timezone.utc
                    ),
                    "value": current_value,
                    "previous_value": previous_value,
                    "change_percent": change_percent,
                    "source": "fred",
                }

                records.append(record)

            except Exception as error:
                logger.error(
                    f"Invalid observation for "
                    f"{indicator_name}: {error}"
                )

        return records

    async def invalidate_cache(
        self,
    ):
        """
        Remove cached macro indicator responses.

        The API stores separate cache entries for:
            macro_indicators:latest
            macro_indicators:30d
            macro_indicators:90d
            macro_indicators:1y
            macro_indicators:5y

        All are invalidated after an indicator update.
        """

        if not self.cache_client:
            return

        cache_keys = [
            "macro_indicators:latest",
            "macro_indicators:30d",
            "macro_indicators:90d",
            "macro_indicators:1y",
            "macro_indicators:5y",
        ]

        for cache_key in cache_keys:
            try:
                await self.cache_client.delete(
                    cache_key
                )

                logger.info(
                    f"Macro indicators cache invalidated: "
                    f"{cache_key}"
                )

            except Exception as error:
                logger.warning(
                    f"Failed invalidating cache "
                    f"{cache_key}: {error}"
                )

    async def update_indicator(
        self,
        indicator_name: str,
        fetch_function,
    ):
        """
        Fetch and store historical indicator data.
        """

        try:
            response = await fetch_function()

            records = self.parse_observations(
                indicator_name,
                response,
            )

            if not records:
                return []

            stored = self.repository.create_many(
                records
            )

            await self.invalidate_cache()

            return stored

        except Exception as error:
            logger.error(
                f"Failed updating "
                f"{indicator_name}: {error}"
            )

            return []

    async def update_all_indicators(
        self,
    ):
        """
        Fetch and store all supported FRED indicators.
        """

        collector = self.get_collector()

        indicators = {
            "cpi": collector.get_cpi,
            "federal_funds_rate":
                collector.get_federal_funds_rate,
            "m2_money_supply":
                collector.get_m2_money_supply,
            "dxy": collector.get_dxy,
            "vix": collector.get_vix,
            "ten_year_treasury":
                collector.get_ten_year_treasury,
            "gdp": collector.get_gdp,
            "unemployment":
                collector.get_unemployment,
        }

        results = {}

        for name, function in indicators.items():
            results[name] = await self.update_indicator(
                name,
                function,
            )

        return results

    async def get_indicators(
        self,
        period: str | None = None,
    ) -> list[dict]:
        """
        Retrieve latest macroeconomic indicators
        directly from TimescaleDB.

        Caching is intentionally handled by the API
        endpoint so that the API can return immediately
        on a cache hit without creating a database
        session.
        """

        logger.info(
            f"Reading indicators from TimescaleDB "
            f"(period={period})"
        )

        indicators = (
            self.repository.get_latest_indicators(
                period=period
            )
        )

        results = []

        for indicator in indicators:
            change = indicator.change_percent

            if change is None:
                trend = "→"
            elif change > 0:
                trend = "↑"
            elif change < 0:
                trend = "↓"
            else:
                trend = "→"

            results.append(
                {
                    "indicator_name":
                        indicator.indicator_name,
                    "time": indicator.time,
                    "current_value":
                        indicator.value,
                    "previous_value":
                        indicator.previous_value,
                    "change_percent":
                        indicator.change_percent,
                    "trend": trend,
                    "source":
                        indicator.source,
                }
            )

        return results

    async def close(self):
        """
        Close external collector connections.
        """

        if self.collector:
            await self.collector.close()