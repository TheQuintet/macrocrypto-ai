"""
Repository for storing macroeconomic indicators
in TimescaleDB.
"""

import logging

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from app.models.macro_indicator import MacroIndicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

        stmt = insert(
            MacroIndicator
        ).values(
            indicators
        )

        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_macro_indicator_time_name"
        )

        result = self.db.execute(stmt)

        self.db.commit()

        logger.info(
            f"Processed {len(indicators)} macro indicator records"
        )

        return indicators