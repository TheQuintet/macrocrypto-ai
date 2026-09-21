"""Model performance repository.

Encapsulates all database reads and writes for the model_performance
table (created in M7):
    - Writing per-run aggregate rows (from the aggregation job)
    - Reading the latest metrics per (model, horizon)
    - Reading historical time series for one (model, horizon)
    - Batch reads for the M8 multi-model performance API

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Validates rows before insertion, then writes in a single
      bulk INSERT.
    - Does not commit — the caller controls the transaction.

Distinction from PerformanceRepository:
    - PerformanceRepository reads/writes prediction_performance,
      which stores one row per evaluated point (millions of rows).
    - ModelPerformanceRepository reads/writes model_performance,
      which stores one aggregate row per (model, horizon, run)
      (dozens of rows). Queries against this table are cheap.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import model_performance

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class ModelPerformanceRow:
    """A single row to insert into model_performance.

    Attributes:
        model_name: Model identifier ('prophet_fresh', ...).
        horizon: Horizon label ('24h' or '7d').
        sample_size: Number of evaluated points that contributed
            to this aggregate. Must be positive.
        calculated_at: When the aggregation was computed (UTC).
        mae: Mean Absolute Error in USD (nullable).
        rmse: Root Mean Square Error in USD (nullable).
        mape: Mean Absolute Percentage Error in percent (nullable).
        directional_accuracy: Percentage of correct direction
            predictions (0-100, nullable).
    """

    model_name: str
    horizon: str
    sample_size: int
    calculated_at: datetime
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    directional_accuracy: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "model_name": self.model_name,
            "horizon": self.horizon,
            "mae": self.mae,
            "rmse": self.rmse,
            "mape": self.mape,
            "directional_accuracy": self.directional_accuracy,
            "sample_size": self.sample_size,
            "calculated_at": self.calculated_at,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ModelPerformanceRow("
            f"model_name='{self.model_name}', "
            f"horizon='{self.horizon}', "
            f"sample_size={self.sample_size}, "
            f"mae={self.mae}, "
            f"calculated_at={self.calculated_at})"
        )


# ============================================================
# REPOSITORY
# ============================================================
class ModelPerformanceRepository:
    """Repository for model_performance reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().

    Example:
        async with session_scope() as session:
            repo = ModelPerformanceRepository(session)
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
        self, rows: List[ModelPerformanceRow]
    ) -> int:
        """Bulk-insert model performance rows.

        Validates all rows before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        Args:
            rows: List of ModelPerformanceRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).

        Raises:
            ValueError: If any row fails validation.
        """
        if not rows:
            logger.debug("save_rows called with empty list")
            return 0

        # Validate all rows before touching the database.
        from app.database.validators import validate_model_performance_rows

        dict_rows = [r.to_dict() for r in rows]
        validate_model_performance_rows(dict_rows)

        stmt = insert(model_performance).values(dict_rows)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(
            f"Inserted {len(dict_rows)} model_performance rows"
        )

        return len(dict_rows)

    # ============================================================
    # READS — latest per model
    # ============================================================
    async def fetch_latest_per_model(
        self,
        horizon: Optional[str] = None,
        days: int = 30,
        model_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch the latest row for each (model, horizon) pair.

        Returns one row per distinct (model_name, horizon), keeping
        the row with the maximum calculated_at. Uses a single query
        with ORDER BY + Python-side deduplication, matching the
        pattern used by PerformanceRepository.fetch_latest_metrics_batch.

        Args:
            horizon: Optional horizon filter ('24h' or '7d').
            days: Look-back window in days.
            model_names: Optional list of model names to include.

        Returns:
            List of dicts with keys: model_name, horizon, mae, rmse,
            mape, directional_accuracy, sample_size, calculated_at,
            created_at.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(
            model_performance.c.id,
            model_performance.c.model_name,
            model_performance.c.horizon,
            model_performance.c.mae,
            model_performance.c.rmse,
            model_performance.c.mape,
            model_performance.c.directional_accuracy,
            model_performance.c.sample_size,
            model_performance.c.calculated_at,
            model_performance.c.created_at,
        ).where(
            model_performance.c.calculated_at >= since,
        )

        if horizon is not None:
            stmt = stmt.where(model_performance.c.horizon == horizon)
        if model_names:
            stmt = stmt.where(
                model_performance.c.model_name.in_(model_names)
            )

        stmt = stmt.order_by(
            model_performance.c.model_name.asc(),
            model_performance.c.horizon.asc(),
            desc(model_performance.c.calculated_at),
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        # Deduplicate in Python: keep the first row per (model, horizon).
        # Rows are already sorted by calculated_at DESC within each group.
        seen: set = set()
        latest: List[Dict[str, Any]] = []
        for row in rows:
            key = (row["model_name"], row["horizon"])
            if key in seen:
                continue
            seen.add(key)
            latest.append(dict(row))

        logger.debug(
            f"Fetched {len(latest)} latest model_performance rows "
            f"(days={days}, horizon={horizon})"
        )

        return latest

    # ============================================================
    # READS — history for one (model, horizon)
    # ============================================================
    async def fetch_history(
        self,
        model_name: str,
        horizon: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch the time series of aggregates for one (model, horizon).

        Returns rows ordered ascending by calculated_at, so the
        caller can plot a trend without sorting.

        Args:
            model_name: Model identifier.
            horizon: Horizon label ('24h' or '7d').
            days: Look-back window in days.

        Returns:
            List of dicts ordered by calculated_at ascending.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                model_performance.c.model_name,
                model_performance.c.horizon,
                model_performance.c.mae,
                model_performance.c.rmse,
                model_performance.c.mape,
                model_performance.c.directional_accuracy,
                model_performance.c.sample_size,
                model_performance.c.calculated_at,
            )
            .where(
                model_performance.c.model_name == model_name,
                model_performance.c.horizon == horizon,
                model_performance.c.calculated_at >= since,
            )
            .order_by(model_performance.c.calculated_at.asc())
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    # ============================================================
    # READS — best model by MAE
    # ============================================================
    async def fetch_best_model_by_mae(
        self,
        horizon: str,
        days: int = 30,
        model_names: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Return the model with the lowest mean MAE in the window.

        Averages MAE per model across all aggregate rows in the
        look-back window, then picks the smallest. Models with no
        MAE data in the window are excluded.

        Args:
            horizon: Horizon label ('24h' or '7d').
            days: Look-back window in days.
            model_names: Optional list of model names to restrict
                the search to.

        Returns:
            Model name with the lowest mean MAE, or None if no
            model has MAE data in the window.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = select(
            model_performance.c.model_name,
            func.avg(model_performance.c.mae).label("mean_mae"),
        ).where(
            model_performance.c.horizon == horizon,
            model_performance.c.calculated_at >= since,
            model_performance.c.mae.isnot(None),
        )

        if model_names:
            stmt = stmt.where(
                model_performance.c.model_name.in_(model_names)
            )

        stmt = (
            stmt.group_by(model_performance.c.model_name)
            .order_by(func.avg(model_performance.c.mae).asc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.mappings().first()

        if row is None:
            logger.debug(
                f"No MAE data found for "
                f"(horizon={horizon}, days={days})"
            )
            return None

        return str(row["model_name"])

    # ============================================================
    # COUNTS
    # ============================================================
    async def count_rows(
        self,
        horizon: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> int:
        """Return the total number of rows, optionally filtered.

        Useful for tests and monitoring.

        Args:
            horizon: Optional horizon filter.
            model_name: Optional model filter.

        Returns:
            Row count.
        """
        stmt = select(func.count()).select_from(model_performance)

        if horizon is not None:
            stmt = stmt.where(model_performance.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(
                model_performance.c.model_name == model_name
            )

        result = await self.session.execute(stmt)
        return int(result.scalar_one())