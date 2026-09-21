"""Historical event impact repository.

Encapsulates all database reads and writes for the
``historical_event_impacts`` table (created in A5.1):
    - Writing per-event impact rows (from A5.2's calculation)
    - Reading all events, filtered by event name, date range, or
      impact level
    - Counting rows

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Validates rows before insertion.
    - Does not commit — the caller controls the transaction.

Distinction from other repositories:
    - This repository reads/writes historical_event_impacts, which
      stores one row per event and the BTC reaction to it.
    - The events themselves live only in this table; there is no
      separate events table. Adding an event to the impact table
      implicitly defines the event.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import historical_event_impacts

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class EventImpactRow:
    """A single row to insert into historical_event_impacts.

    Attributes:
        event_name: Event name (e.g. 'FOMC', 'CPI Release', 'NFP').
        event_date: Calendar date the event occurred.
        impact_level: Classified significance. One of 'high',
            'medium', 'low'.
        btc_price_before: BTC price 24 hours before the event.
        btc_price_after: BTC price 24 hours after the event.
        price_change_percent: Percentage change from before to
            after (signed).
        volatility: Standard deviation of percentage returns over
            the window.
        direction: Derived direction. One of 'up', 'down',
            'neutral'.
    """

    event_name: str
    event_date: date
    impact_level: str
    btc_price_before: float
    btc_price_after: float
    price_change_percent: float
    volatility: float
    direction: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "event_name": self.event_name,
            "event_date": self.event_date,
            "impact_level": self.impact_level,
            "btc_price_before": self.btc_price_before,
            "btc_price_after": self.btc_price_after,
            "price_change_percent": self.price_change_percent,
            "volatility": self.volatility,
            "direction": self.direction,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"EventImpactRow("
            f"event_name='{self.event_name}', "
            f"event_date={self.event_date}, "
            f"impact_level='{self.impact_level}', "
            f"direction='{self.direction}', "
            f"change={self.price_change_percent:+.2f}%)"
        )


# ============================================================
# REPOSITORY
# ============================================================
class EventImpactRepository:
    """Repository for historical_event_impacts reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().

    Example:
        async with session_scope() as session:
            repo = EventImpactRepository(session)
            count = await repo.save_rows(rows)
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: An AsyncSession bound to the target database.
        """
        self.session = session

    # ============================================================
    # WRITES
    # ============================================================
    async def save_rows(
        self, rows: List[EventImpactRow]
    ) -> int:
        """Bulk-insert event impact rows.

        Validates all rows before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        Note: the table has a UNIQUE (event_name, event_date)
        constraint. A caller that may re-process an event should
        either delete the prior row first or use an upsert; this
        method does a plain INSERT and will raise on conflict.

        Args:
            rows: List of EventImpactRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).

        Raises:
            ValueError: If any row fails validation.
        """
        if not rows:
            logger.debug("save_rows called with empty list")
            return 0

        # Validate all rows before touching the database.
        from app.database.validators import (
            validate_historical_event_impact_rows,
        )

        dict_rows = [r.to_dict() for r in rows]
        validate_historical_event_impact_rows(dict_rows)

        stmt = insert(historical_event_impacts).values(dict_rows)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(f"Inserted {len(dict_rows)} event impact rows")

        return len(dict_rows)

    async def delete_by_event(
        self, event_name: str, event_date: date
    ) -> bool:
        """Delete a single row by its natural key.

        Helper for callers that want to re-insert an event after
        correcting its data, working around the UNIQUE constraint.

        Does not commit.

        Args:
            event_name: Event name.
            event_date: Calendar date.

        Returns:
            True if a row was removed, False if it did not exist.
        """
        stmt = (
            delete(historical_event_impacts)
            .where(
                historical_event_impacts.c.event_name == event_name,
                historical_event_impacts.c.event_date == event_date,
            )
            .returning(historical_event_impacts.c.id)
        )
        result = await self.session.execute(stmt)
        removed = result.scalar_one_or_none() is not None
        if removed:
            await self.session.flush()
            logger.info(
                f"Deleted event impact {event_name!r}/{event_date}"
            )
        return removed

    # ============================================================
    # READS
    # ============================================================
    async def fetch_all(
        self,
        impact_level: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch every event impact row, newest first.

        Args:
            impact_level: Optional filter ('high', 'medium', 'low').
            limit: Maximum number of rows to return.

        Returns:
            List of dicts ordered by event_date descending.
        """
        stmt = select(
            historical_event_impacts.c.id,
            historical_event_impacts.c.event_name,
            historical_event_impacts.c.event_date,
            historical_event_impacts.c.impact_level,
            historical_event_impacts.c.btc_price_before,
            historical_event_impacts.c.btc_price_after,
            historical_event_impacts.c.price_change_percent,
            historical_event_impacts.c.volatility,
            historical_event_impacts.c.direction,
            historical_event_impacts.c.created_at,
        )

        if impact_level is not None:
            stmt = stmt.where(
                historical_event_impacts.c.impact_level == impact_level
            )

        stmt = stmt.order_by(
            historical_event_impacts.c.event_date.desc(),
            historical_event_impacts.c.event_name.asc(),
        ).limit(limit)

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_by_event_name(
        self,
        event_name: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch every event impact row for a given event name.

        Args:
            event_name: Event name.
            limit: Maximum number of rows to return.

        Returns:
            List of dicts ordered by event_date descending.
        """
        stmt = (
            select(
                historical_event_impacts.c.id,
                historical_event_impacts.c.event_name,
                historical_event_impacts.c.event_date,
                historical_event_impacts.c.impact_level,
                historical_event_impacts.c.btc_price_before,
                historical_event_impacts.c.btc_price_after,
                historical_event_impacts.c.price_change_percent,
                historical_event_impacts.c.volatility,
                historical_event_impacts.c.direction,
                historical_event_impacts.c.created_at,
            )
            .where(historical_event_impacts.c.event_name == event_name)
            .order_by(historical_event_impacts.c.event_date.desc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_by_date_range(
        self,
        start_date: date,
        end_date: date,
        impact_level: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch every event impact row within a date range (inclusive).

        Args:
            start_date: Earliest event_date to include.
            end_date: Latest event_date to include.
            impact_level: Optional filter.
            limit: Maximum number of rows to return.

        Returns:
            List of dicts ordered by event_date descending.
        """
        stmt = select(
            historical_event_impacts.c.id,
            historical_event_impacts.c.event_name,
            historical_event_impacts.c.event_date,
            historical_event_impacts.c.impact_level,
            historical_event_impacts.c.btc_price_before,
            historical_event_impacts.c.btc_price_after,
            historical_event_impacts.c.price_change_percent,
            historical_event_impacts.c.volatility,
            historical_event_impacts.c.direction,
            historical_event_impacts.c.created_at,
        ).where(
            historical_event_impacts.c.event_date >= start_date,
            historical_event_impacts.c.event_date <= end_date,
        )

        if impact_level is not None:
            stmt = stmt.where(
                historical_event_impacts.c.impact_level == impact_level
            )

        stmt = stmt.order_by(
            historical_event_impacts.c.event_date.desc()
        ).limit(limit)

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    # ============================================================
    # COUNTS
    # ============================================================
    async def count_rows(
        self,
        event_name: Optional[str] = None,
        impact_level: Optional[str] = None,
    ) -> int:
        """Return the total number of rows, optionally filtered.

        Useful for tests and monitoring.

        Args:
            event_name: Optional event name filter.
            impact_level: Optional impact level filter.

        Returns:
            Row count.
        """
        stmt = select(func.count()).select_from(historical_event_impacts)

        if event_name is not None:
            stmt = stmt.where(
                historical_event_impacts.c.event_name == event_name
            )
        if impact_level is not None:
            stmt = stmt.where(
                historical_event_impacts.c.impact_level == impact_level
            )

        result = await self.session.execute(stmt)
        return int(result.scalar_one())


__all__ = ["EventImpactRepository", "EventImpactRow"]