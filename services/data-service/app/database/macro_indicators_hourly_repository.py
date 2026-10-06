"""
Repository for macro_indicators_hourly.

All writes use ON CONFLICT (time) DO NOTHING. Same idempotency
and immutability guarantees as btc_prices_hourly.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.macro_indicators_hourly import MacroIndicatorHourly

logger = logging.getLogger(__name__)


class MacroIndicatorHourlyRepository:
    """Database operations for macro_indicators_hourly."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_many(
        self,
        rows: Iterable[dict[str, Any]],
    ) -> int:
        """
        Insert rows, ignoring any whose time already exists.

        Returns the number of rows attempted (not the number
        actually inserted).
        """
        rows = list(rows)
        if not rows:
            return 0

        stmt = insert(MacroIndicatorHourly).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["time"])

        self.db.execute(stmt)
        self.db.commit()

        return len(rows)

    def get_by_time(
        self,
        hour: datetime,
    ) -> MacroIndicatorHourly | None:
        return (
            self.db.query(MacroIndicatorHourly)
            .filter(MacroIndicatorHourly.time == hour)
            .first()
        )

    def existing_hours(
        self,
        start: datetime,
        end: datetime,
    ) -> set[datetime]:
        """
        Return the set of hour timestamps already present in
        [start, end).
        """
        rows = (
            self.db.query(MacroIndicatorHourly.time)
            .filter(
                MacroIndicatorHourly.time >= start,
                MacroIndicatorHourly.time < end,
            )
            .all()
        )
        return {row[0] for row in rows}