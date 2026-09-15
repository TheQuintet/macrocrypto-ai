"""BTC-vs-macro correlation repository.

Encapsulates all database reads and writes for the
btc_macro_correlation table (created in A1.1):
    - Writing per-run correlation rows (from A1.2's calculation)
    - Reading the latest correlation per (indicator, window)
    - Reading historical time series for one (indicator, window)
    - Reading the latest across all indicators for a given window
      (the A1.6 API pattern)

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Validates rows before insertion.
    - Does not commit — the caller controls the transaction.

Distinction from other repositories:
    - ModelPerformanceRepository reads/writes model_performance,
      which stores per-model aggregates keyed by (model, horizon).
    - This repository reads/writes btc_macro_correlation, which
      stores BTC-vs-macro correlations keyed by (indicator, window).
    The two tables are unrelated in shape and lifecycle, so they
    live in separate repositories.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import btc_macro_correlation

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class CorrelationRow:
    """A single row to insert into btc_macro_correlation.

    Attributes:
        indicator_name: Product-facing indicator label. One of
            'inflation', 'rates', 'gdp', 'unemployment'.
        window_days: Rolling window length. One of 30, 90, 365.
        calculated_at: When the correlation was computed (UTC).
        correlation_coefficient: Pearson correlation in [-1, 1].
        strength: Derived strength label. One of 'strong',
            'medium', 'weak'.
        direction: Derived direction label. One of 'positive',
            'negative'.
        p_value: Two-tailed p-value in [0, 1], or None if not yet
            computed (A1.4 populates it).
    """

    indicator_name: str
    window_days: int
    calculated_at: datetime
    correlation_coefficient: float
    strength: str
    direction: str
    p_value: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "indicator_name": self.indicator_name,
            "window_days": self.window_days,
            "calculated_at": self.calculated_at,
            "correlation_coefficient": self.correlation_coefficient,
            "strength": self.strength,
            "direction": self.direction,
            "p_value": self.p_value,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"CorrelationRow("
            f"indicator_name='{self.indicator_name}', "
            f"window_days={self.window_days}, "
            f"coefficient={self.correlation_coefficient:.4f}, "
            f"strength='{self.strength}', "
            f"direction='{self.direction}', "
            f"calculated_at={self.calculated_at})"
        )


# ============================================================
# REPOSITORY
# ============================================================
class CorrelationRepository:
    """Repository for btc_macro_correlation reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().

    Example:
        async with session_scope() as session:
            repo = CorrelationRepository(session)
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
        self, rows: List[CorrelationRow]
    ) -> int:
        """Bulk-insert correlation rows.

        Validates all rows before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        Args:
            rows: List of CorrelationRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).

        Raises:
            ValueError: If any row fails validation.
        """
        if not rows:
            logger.debug("save_rows called with empty list")
            return 0

        # Validate all rows before touching the database.
        from app.database.validators import validate_correlation_rows

        dict_rows = [r.to_dict() for r in rows]
        validate_correlation_rows(dict_rows)

        stmt = insert(btc_macro_correlation).values(dict_rows)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(f"Inserted {len(dict_rows)} correlation rows")

        return len(dict_rows)

    # ============================================================
    # READS — latest per (indicator, window)
    # ============================================================
    async def fetch_latest_per_indicator(
        self,
        window_days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch the latest row for each (indicator, window) pair.

        Returns one row per distinct (indicator_name, window_days),
        keeping the row with the maximum calculated_at. Uses a
        single query with ORDER BY + Python-side deduplication,
        matching the pattern used by the other repositories.

        Args:
            window_days: Optional window filter. When provided, only
                rows for that window are considered.

        Returns:
            List of dicts with keys: indicator_name, window_days,
            calculated_at, correlation_coefficient, strength,
            direction, p_value, created_at.
        """
        stmt = select(
            btc_macro_correlation.c.indicator_name,
            btc_macro_correlation.c.window_days,
            btc_macro_correlation.c.calculated_at,
            btc_macro_correlation.c.correlation_coefficient,
            btc_macro_correlation.c.strength,
            btc_macro_correlation.c.direction,
            btc_macro_correlation.c.p_value,
            btc_macro_correlation.c.created_at,
        )

        if window_days is not None:
            stmt = stmt.where(
                btc_macro_correlation.c.window_days == window_days
            )

        stmt = stmt.order_by(
            btc_macro_correlation.c.indicator_name.asc(),
            btc_macro_correlation.c.window_days.asc(),
            desc(btc_macro_correlation.c.calculated_at),
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        # Deduplicate in Python: keep the first row per
        # (indicator, window). Rows are already sorted by
        # calculated_at DESC within each group.
        seen: set = set()
        latest: List[Dict[str, Any]] = []
        for row in rows:
            key = (row["indicator_name"], row["window_days"])
            if key in seen:
                continue
            seen.add(key)
            latest.append(dict(row))

        logger.debug(
            f"Fetched {len(latest)} latest correlation rows "
            f"(window_days={window_days})"
        )

        return latest

    # ============================================================
    # READS — history for one (indicator, window)
    # ============================================================
    async def fetch_history(
        self,
        indicator_name: str,
        window_days: int,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch the time series of correlations for one pair.

        Returns rows ordered ascending by calculated_at, so the
        caller can plot a trend without sorting.

        Args:
            indicator_name: Indicator label.
            window_days: Window length in days (30/90/365).
            days: Look-back window in days.

        Returns:
            List of dicts ordered by calculated_at ascending.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                btc_macro_correlation.c.indicator_name,
                btc_macro_correlation.c.window_days,
                btc_macro_correlation.c.calculated_at,
                btc_macro_correlation.c.correlation_coefficient,
                btc_macro_correlation.c.strength,
                btc_macro_correlation.c.direction,
                btc_macro_correlation.c.p_value,
            )
            .where(
                btc_macro_correlation.c.indicator_name == indicator_name,
                btc_macro_correlation.c.window_days == window_days,
                btc_macro_correlation.c.calculated_at >= since,
            )
            .order_by(btc_macro_correlation.c.calculated_at.asc())
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    # ============================================================
    # READS — strongest correlation for a window
    # ============================================================
    async def fetch_strongest_for_window(
        self,
        window_days: int,
    ) -> Optional[Dict[str, Any]]:
        """Return the indicator with the highest |coefficient| in a window.

        Considers only the latest row per indicator. Returns None if
        the window has no data.

        Args:
            window_days: Window length in days (30/90/365).

        Returns:
            Dict with the same shape as fetch_latest_per_indicator,
            or None.
        """
        latest = await self.fetch_latest_per_indicator(
            window_days=window_days
        )

        if not latest:
            return None

        # max by absolute coefficient. The row with the smallest
        # absolute value loses. Tie-breaking is by indicator name
        # for determinism.
        return max(
            latest,
            key=lambda r: (
                abs(r["correlation_coefficient"]),
                r["indicator_name"],
            ),
        )

    # ============================================================
    # COUNTS
    # ============================================================
    async def count_rows(
        self,
        indicator_name: Optional[str] = None,
        window_days: Optional[int] = None,
    ) -> int:
        """Return the total number of rows, optionally filtered.

        Useful for tests and monitoring.

        Args:
            indicator_name: Optional indicator filter.
            window_days: Optional window filter.

        Returns:
            Row count.
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(btc_macro_correlation)

        if indicator_name is not None:
            stmt = stmt.where(
                btc_macro_correlation.c.indicator_name == indicator_name
            )
        if window_days is not None:
            stmt = stmt.where(
                btc_macro_correlation.c.window_days == window_days
            )

        result = await self.session.execute(stmt)
        return int(result.scalar_one())