"""
Service for processing and storing macroeconomic indicators.

Responsibilities:
- Fetch data from FRED
- Parse observations
- Calculate previous values
- Calculate percentage changes
- Store historical data
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any


from app.collectors.fred import FREDCollector
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IndicatorService:
    """
    Handles macroeconomic indicator processing.
    """


    def __init__(self, db):

        self.collector = FREDCollector()

        self.repository = MacroIndicatorRepository(
            db
        )


    def calculate_change_percent(
        self,
        current_value: float,
        previous_value: float | None,
    ) -> float | None:
        """
        Calculate percentage change.
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
            []
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

                    previous_raw = observations[index + 1]["value"]

                    if previous_raw != ".":
                        previous_value = float(previous_raw)


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


                records.append(
                    record
                )


            except Exception as error:

                logger.error(
                    f"Invalid observation for "
                    f"{indicator_name}: {error}"
                )


        return records


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


            logger.info(
                f"{indicator_name}: "
                f"stored {len(stored)} records"
            )


            return stored


        except Exception as error:

            logger.error(
                f"Failed updating "
                f"{indicator_name}: {error}"
            )

            return []


    async def update_all_indicators(self):
        """
        Fetch and store all FRED indicators.
        """


        indicators = {

            "cpi":
                self.collector.get_cpi,

            "federal_funds_rate":
                self.collector.get_federal_funds_rate,

            "m2_money_supply":
                self.collector.get_m2_money_supply,

            "dxy":
                self.collector.get_dxy,

            "ten_year_treasury":
                self.collector.get_ten_year_treasury,

            "gdp":
                self.collector.get_gdp,

            "unemployment":
                self.collector.get_unemployment,
        }


        results = {}


        for name, function in indicators.items():

            results[name] = await self.update_indicator(
                name,
                function,
            )


        return results


    async def close(self):

        await self.collector.close()