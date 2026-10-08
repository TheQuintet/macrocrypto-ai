"""
Repository for btc_prices_hourly.

All writes use ON CONFLICT (time) DO NOTHING so that:
  - re-running a writer is a no-op
  - concurrent writers (scheduler + backfill) do not race
  - historical rows are immutable by default
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.btc_prices_hourly import BTCPriceHourly

logger = logging.getLogger(__name__)


class BTCPriceHourlyRepository:
    """Database operations for btc_prices_hourly."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_many(
        self,
        rows: Iterable[dict[str, Any]],
    ) -> int:
        """
        Insert rows, ignoring any whose time already exists.

        Returns the number of rows attempted (not the number
        actually inserted — Postgres does not report that
        cheaply for a batch DO NOTHING).
        """
        rows = list(rows)
        if not rows:
            return 0

        stmt = insert(BTCPriceHourly).values(rows)
        stmt = stmt.on_conflict_do_nothing(index_elements=["time"])

        self.db.execute(stmt)
        self.db.commit()

        return len(rows)

    def get_by_time(
        self,
        hour: datetime,
    ) -> BTCPriceHourly | None:
        return (
            self.db.query(BTCPriceHourly)
            .filter(BTCPriceHourly.time == hour)
            .first()
        )

    def existing_hours(
        self,
        start: datetime,
        end: datetime,
    ) -> set[datetime]:
        """
        Return the set of hour timestamps already present in
        [start, end). Used by backfill to skip work.
        """
        rows = (
            self.db.query(BTCPriceHourly.time)
            .filter(
                BTCPriceHourly.time >= start,
                BTCPriceHourly.time < end,
            )
            .all()
        )
        return {row[0] for row in rows}