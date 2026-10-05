"""
Repository for storing macroeconomic indicators
in TimescaleDB.
"""

from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.macro_indicator import MacroIndicator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_INSERT_BATCH_SIZE = 5_000


class MacroIndicatorRepository:
    """
    Handles database operations for macro indicators.
    """

    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def create_indicator(
        self,
        indicator_name: str,
        time,
        value: float,
        previous_value: float | None,
        change_percent: float | None,
        source: str = "fred",
    ) -> MacroIndicator:
        """
        Insert a single macro indicator record.
        """

        indicator = MacroIndicator(
            indicator_name=indicator_name,
            time=time,
            value=value,
            previous_value=previous_value,
            change_percent=change_percent,
            source=source,
        )

        self.db.add(indicator)

        self.db.commit()

        self.db.refresh(indicator)

        logger.info(
            f"Stored {indicator_name} value={value}"
        )

        return indicator

    def create_many(
        self,
        indicators: list[dict],
    ):
        """
        Insert multiple historical observations.

        Ignore duplicates based on:
        (time, indicator_name)
        """

        if not indicators:
            return []

        for start in range(
            0,
            len(indicators),
            MAX_INSERT_BATCH_SIZE,
        ):
            batch = indicators[
                start:start + MAX_INSERT_BATCH_SIZE
            ]

            stmt = insert(
                MacroIndicator
            ).values(
                batch
            )

            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_macro_indicator_time_name"
            )

            self.db.execute(stmt)

        self.db.commit()

        logger.info(
            f"Processed {len(indicators)} macro indicator records"
        )

        return indicators

    def get_latest_indicators(
        self,
        period: str | None = None,
    ):
        """
        Retrieve macroeconomic indicators.

        Without a period:
            Return the latest observation for each indicator.

        With a period:
            Return all observations within the requested
            historical window.

        Supported periods:
            30d - last 30 days
            90d - last 90 days
            1y  - last 365 days
            5y  - last 1825 days
        """

        # --------------------------------------------------
        # No period:
        # Return only the latest value for each indicator.
        # --------------------------------------------------

        if period is None:
            indicators = (
                self.db.query(MacroIndicator)
                .order_by(
                    MacroIndicator.time.desc()
                )
                .all()
            )

            latest = {}

            for indicator in indicators:
                if (
                    indicator.indicator_name
                    not in latest
                ):
                    latest[
                        indicator.indicator_name
                    ] = indicator

            return list(
                latest.values()
            )

        # --------------------------------------------------
        # Historical period mapping
        # --------------------------------------------------

        period_days = {
            "30d": 30,
            "90d": 90,
            "1y": 365,
            "5y": 1825,
        }

        days = period_days.get(period)

        # The API validates supported periods.
        # This protects the repository if it is called
        # directly with an unsupported period.
        if days is None:
            return []

        # --------------------------------------------------
        # Calculate historical start date
        # --------------------------------------------------

        start_date = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=days
            )
        )

        # --------------------------------------------------
        # Return historical observations
        # --------------------------------------------------

        return (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.time >= start_date,
            )
            .order_by(
                MacroIndicator.time.asc()
            )
            .all()
        )

    def get_historical_data(
        self,
        indicator_name: str,
        days: int,
    ):
        """
        Return historical indicator values.
        """

        start_date = (
            datetime.now(
                timezone.utc
            )
            - timedelta(
                days=days
            )
        )

        return (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.indicator_name
                == indicator_name,
                MacroIndicator.time
                >= start_date,
            )
            .order_by(
                MacroIndicator.time.asc()
            )
            .all()
        )

    def get_historical_data_for_similarity(
        self,
        start_date: datetime,
    ):
        """
        Return historical macro indicator observations used
        by the similar historical periods engine.

        Returns all supported indicators from the supplied
        start date onward.
        """

        return (
            self.db.query(MacroIndicator)
            .filter(
                MacroIndicator.time >= start_date,
                MacroIndicator.indicator_name.in_(
                    [
                        "cpi",
                        "federal_funds_rate",
                        "m2_money_supply",
                        "dxy",
                        "ten_year_treasury",
                        "gdp",
                        "unemployment",
                    ]
                ),
            )
            .order_by(
                MacroIndicator.time.asc()
            )
            .all()
        )