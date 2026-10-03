"""Threshold repository.

Encapsulates reads and writes for the threshold_breaches table
(created in T5.4):
    - Writing breach rows during the daily accuracy check
    - Reading recent breaches for T5.6's escalation logic
    - Counting consecutive-day streaks
    - Batch reads for the T5.6 performance API

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Does not commit — the caller controls the transaction.

CLI isolation:
    When settings.cli_mode is True, all reads and writes on the
    threshold_breaches table are routed to threshold_breaches_cli
    instead. Routing is handled by `_resolve_threshold_table()`.

    Note: `fetch_latest_breaches_batch` uses raw SQL via text().
    The table name is interpolated from the resolved table's name,
    which comes from a settings-controlled source — never from
    user input — so the interpolation is safe.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.tables import (
    threshold_breaches,
    threshold_breaches_cli,
)

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
    # CLI ROUTING HELPER
    # ============================================================
    def _resolve_threshold_table(self):
        """Return the active threshold_breaches table.

        In CLI mode (settings.cli_mode=True), returns
        threshold_breaches_cli so CLI runs are sandboxed. Otherwise
        returns the production table.

        Returns:
            A SQLAlchemy Table object.
        """
        if settings.cli_mode:
            return threshold_breaches_cli
        return threshold_breaches

    # ============================================================
    # WRITES
    # ============================================================
    async def save_breaches(
        self, rows: List[ThresholdBreachRow]
    ) -> int:
        """Bulk-insert threshold breach rows.

        Does not commit — the caller controls the transaction.

        CLI mode: when settings.cli_mode is True, rows are written
        to threshold_breaches_cli instead.

        Args:
            rows: List of ThresholdBreachRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).
        """
        if not rows:
            logger.debug("save_breaches called with empty list")
            return 0

        table = self._resolve_threshold_table()
        payload = [r.to_dict() for r in rows]

        stmt = insert(table).values(payload)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(
            f"Inserted {len(payload)} rows into {table.name}"
        )

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
        table = self._resolve_threshold_table()
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                table.c.id,
                table.c.detected_at,
                table.c.horizon,
                table.c.model_name,
                table.c.metric,
                table.c.metric_unit,
                table.c.value,
                table.c.threshold,
                table.c.breach_direction,
                table.c.consecutive_days,
                table.c.model_version,
                table.c.notes,
            )
            .where(
                table.c.horizon == horizon,
                table.c.model_name == model_name,
                table.c.detected_at >= since,
            )
            .order_by(desc(table.c.detected_at))
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
        table = self._resolve_threshold_table()

        stmt = (
            select(
                table.c.id,
                table.c.detected_at,
                table.c.consecutive_days,
                table.c.value,
                table.c.threshold,
            )
            .where(
                table.c.horizon == horizon,
                table.c.model_name == model_name,
                table.c.metric == metric,
            )
            .order_by(desc(table.c.detected_at))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.mappings().first()
        return dict(row) if row else None

    async def fetch_latest_breaches_batch(
        self,
        since_days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch the latest breach per (model, horizon, metric).

        Uses Postgres's DISTINCT ON to return one row per distinct
        (model_name, horizon, metric) tuple — the row with the
        maximum `detected_at`.

        Intended for the T5.6 performance API: it lets us surface
        current streaks for every model-horizon-metric combination
        in a single query instead of dozens.

        Args:
            since_days: Only consider breaches within the last N
                days. Older streaks are irrelevant.

        Returns:
            List of dicts with keys: model_name, horizon, metric,
            consecutive_days, detected_at.
        """
        table = self._resolve_threshold_table()
        since = datetime.now(timezone.utc) - timedelta(days=since_days)

        # DISTINCT ON requires ORDER BY to start with the DISTINCT
        # ON columns, then by whatever determines "the row we want"
        # — here, the newest detected_at.
        #
        # The table name is interpolated because DISTINCT ON uses
        # raw SQL. The name comes from settings, never from user
        # input, so the interpolation is safe.
        stmt = text(
            f"""
            SELECT DISTINCT ON (model_name, horizon, metric)
                model_name,
                horizon,
                metric,
                consecutive_days,
                detected_at
            FROM {table.name}
            WHERE detected_at >= :since
            ORDER BY model_name, horizon, metric, detected_at DESC
            """
        )

        result = await self.session.execute(stmt, {"since": since})
        return [dict(row) for row in result.mappings().all()]

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
        table = self._resolve_threshold_table()
        stmt = select(func.count()).select_from(table)

        if horizon is not None:
            stmt = stmt.where(table.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(table.c.model_name == model_name)
        if since_days is not None:
            since = datetime.now(timezone.utc) - timedelta(days=since_days)
            stmt = stmt.where(table.c.detected_at >= since)

        result = await self.session.execute(stmt)
        return int(result.scalar_one())