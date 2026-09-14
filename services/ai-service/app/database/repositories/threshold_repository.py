"""Threshold repository.

Encapsulates reads and writes for the threshold_breaches table
(created in T5.4):
    - Writing breach rows during the daily accuracy check
    - Reading recent breaches for T5.6's escalation logic
    - Counting consecutive-day streaks

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Does not commit — the caller controls the transaction.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import threshold_breaches

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class ThresholdBreachRow:
    """A single row to insert into threshold_breaches.

    Attributes:
        horizon: Horizon label ('24h' or '7d').
        model_name: Model identifier.
        metric: 'mae_pct', 'rmse_pct', 'mape', or
            'directional_accuracy'.
        metric_unit: 'percent' or 'usd'.
        value: The actual value that breached.
        threshold: The configured threshold.
        breach_direction: 'above' or 'below'.
        consecutive_days: Number of consecutive daily breaches.
        model_version: Optional model version string.
        notes: Optional free-form note.
    """

    horizon: str
    model_name: str
    metric: str
    metric_unit: str
    value: float
    threshold: float
    breach_direction: str
    consecutive_days: int = 1
    model_version: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "horizon": self.horizon,
            "model_name": self.model_name,
            "metric": self.metric,
            "metric_unit": self.metric_unit,
            "value": self.value,
            "threshold": self.threshold,
            "breach_direction": self.breach_direction,
            "consecutive_days": self.consecutive_days,
            "model_version": self.model_version,
            "notes": self.notes,
        }


# ============================================================
# REPOSITORY
# ============================================================
class ThresholdRepository:
    """Repository for threshold_breaches reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().
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
    async def save_breaches(
        self, rows: List[ThresholdBreachRow]
    ) -> int:
        """Bulk-insert threshold breach rows.

        Does not commit — the caller controls the transaction.

        Args:
            rows: List of ThresholdBreachRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).
        """
        if not rows:
            logger.debug("save_breaches called with empty list")
            return 0

        payload = [r.to_dict() for r in rows]

        stmt = insert(threshold_breaches).values(payload)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(f"Inserted {len(payload)} threshold breach rows")

        return len(payload)

    # ============================================================
    # READS
    # ============================================================
    async def fetch_recent_breaches(
        self,
        horizon: str,
        model_name: str,
        days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Fetch recent breach rows for a (horizon, model).

        Args:
            horizon: Horizon label.
            model_name: Model identifier.
            days: Look back this many days.

        Returns:
            List of dicts, newest first.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                threshold_breaches.c.id,
                threshold_breaches.c.detected_at,
                threshold_breaches.c.horizon,
                threshold_breaches.c.model_name,
                threshold_breaches.c.metric,
                threshold_breaches.c.metric_unit,
                threshold_breaches.c.value,
                threshold_breaches.c.threshold,
                threshold_breaches.c.breach_direction,
                threshold_breaches.c.consecutive_days,
                threshold_breaches.c.model_version,
                threshold_breaches.c.notes,
            )
            .where(
                threshold_breaches.c.horizon == horizon,
                threshold_breaches.c.model_name == model_name,
                threshold_breaches.c.detected_at >= since,
            )
            .order_by(desc(threshold_breaches.c.detected_at))
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def fetch_latest_breach(
        self,
        horizon: str,
        model_name: str,
        metric: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch the most recent breach for a specific metric.

        Used by the daily job to compute `consecutive_days`.

        Args:
            horizon: Horizon label.
            model_name: Model identifier.
            metric: Metric identifier.

        Returns:
            Dict, or None if no prior breach exists.
        """
        stmt = (
            select(
                threshold_breaches.c.id,
                threshold_breaches.c.detected_at,
                threshold_breaches.c.consecutive_days,
                threshold_breaches.c.value,
                threshold_breaches.c.threshold,
            )
            .where(
                threshold_breaches.c.horizon == horizon,
                threshold_breaches.c.model_name == model_name,
                threshold_breaches.c.metric == metric,
            )
            .order_by(desc(threshold_breaches.c.detected_at))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.mappings().first()
        return dict(row) if row else None

    async def count_breaches(
        self,
        horizon: Optional[str] = None,
        model_name: Optional[str] = None,
        since_days: Optional[int] = None,
    ) -> int:
        """Count breaches, optionally filtered.

        Args:
            horizon: Optional horizon filter.
            model_name: Optional model filter.
            since_days: Optional look-back window in days.

        Returns:
            Row count.
        """
        stmt = select(func.count()).select_from(threshold_breaches)

        if horizon is not None:
            stmt = stmt.where(threshold_breaches.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(
                threshold_breaches.c.model_name == model_name
            )
        if since_days is not None:
            since = datetime.now(timezone.utc) - timedelta(days=since_days)
            stmt = stmt.where(threshold_breaches.c.detected_at >= since)

        result = await self.session.execute(stmt)
        return int(result.scalar_one())