"""Performance repository.

Encapsulates all database reads and writes for the
prediction_performance table (created in T5.1):
    - Writing per-point evaluation rows (from T5.2's backtester)
    - Reading the latest aggregated metrics per (horizon, model)
    - Reading historical metrics over a time window

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Validates rows before insertion, then writes in a single
      bulk INSERT.
    - Does not commit — the caller controls the transaction.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import prediction_performance

logger = logging.getLogger(__name__)


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class PerformanceRow:
    """A single row to insert into prediction_performance.

    Attributes:
        horizon: Horizon label ('24h' or '7d').
        model_name: Model identifier ('prophet_fresh', ...).
        model_version: Version string (e.g. '1.0.0').
        forecast_date: Timestamp the prediction was FOR.
        predicted_price: Predicted BTC price.
        actual_price: Actual BTC price observed at forecast_date.
        mae: Rolling MAE in USD (nullable).
        rmse: Rolling RMSE in USD (nullable).
        mape: Rolling MAPE in percent (nullable).
        market_condition: Market classification or None.
        prediction_id: FK to btc_predictions.id, or None for
            backtest rows.
    """

    horizon: str
    model_name: str
    model_version: str
    forecast_date: datetime
    predicted_price: float
    actual_price: float
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    market_condition: Optional[str] = None
    prediction_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "prediction_id": self.prediction_id,
            "horizon": self.horizon,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "forecast_date": self.forecast_date,
            "predicted_price": self.predicted_price,
            "actual_price": self.actual_price,
            "mae": self.mae,
            "rmse": self.rmse,
            "mape": self.mape,
            "market_condition": self.market_condition,
        }


# ============================================================
# REPOSITORY
# ============================================================
class PerformanceRepository:
    """Repository for prediction_performance reads and writes.

    All methods are async. The repository does not commit — the
    caller controls the transaction via session_scope().

    Example:
        async with session_scope() as session:
            repo = PerformanceRepository(session)
            count = await repo.save_performance_rows(rows)
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
    async def save_performance_rows(
        self, rows: List[PerformanceRow]
    ) -> int:
        """Bulk-insert performance rows into prediction_performance.

        Validates all rows before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        Args:
            rows: List of PerformanceRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).

        Raises:
            ValueError: If any row fails validation.
        """
        if not rows:
            logger.debug("save_performance_rows called with empty list")
            return 0

        # Validate all rows before touching the database.
        # Imported locally to avoid a circular import: validators.py
        # doesn't import from this module, but keeping the import
        # local mirrors PredictionRepository's pattern.
        from app.database.validators import validate_performance_rows

        # The validator accepts dicts or objects. Convert to dicts
        # for a uniform interface.
        dict_rows = [r.to_dict() for r in rows]
        validate_performance_rows(dict_rows)

        stmt = insert(prediction_performance).values(dict_rows)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(
            f"Inserted {len(dict_rows)} prediction_performance rows"
        )

        return len(dict_rows)

    # ============================================================
    # READS
    # ============================================================
    async def fetch_latest_metrics(
        self,
        horizon: str,
        model_name: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch the latest aggregated metrics for a (horizon, model).

        Returns the row with the maximum forecast_date whose mae is
        not NULL. The row's mae/rmse/mape are the aggregate metrics
        for the most recent evaluation of this key.

        Args:
            horizon: Horizon label ('24h' or '7d').
            model_name: Model identifier.

        Returns:
            Dict with keys: horizon, model_name, model_version,
            forecast_date, mae, rmse, mape, market_condition,
            created_at. Or None if no rows exist.
        """
        stmt = (
            select(
                prediction_performance.c.horizon,
                prediction_performance.c.model_name,
                prediction_performance.c.model_version,
                prediction_performance.c.forecast_date,
                prediction_performance.c.mae,
                prediction_performance.c.rmse,
                prediction_performance.c.mape,
                prediction_performance.c.market_condition,
                prediction_performance.c.created_at,
            )
            .where(
                prediction_performance.c.horizon == horizon,
                prediction_performance.c.model_name == model_name,
                prediction_performance.c.mae.isnot(None),
            )
            .order_by(desc(prediction_performance.c.forecast_date))
            .limit(1)
        )

        result = await self.session.execute(stmt)
        row = result.mappings().first()

        if row is None:
            logger.debug(
                f"No metrics found for "
                f"(horizon={horizon}, model={model_name})"
            )
            return None

        return dict(row)

    async def fetch_metrics_history(
        self,
        horizon: str,
        model_name: str,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Fetch metrics history over the last N days.

        Returns one row per distinct (forecast_date) evaluation,
        ordered ascending by forecast_date.

        Args:
            horizon: Horizon label.
            model_name: Model identifier.
            days: Number of days to look back.

        Returns:
            List of dicts (one per evaluation batch).
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                prediction_performance.c.forecast_date,
                prediction_performance.c.mae,
                prediction_performance.c.rmse,
                prediction_performance.c.mape,
                prediction_performance.c.directional_accuracy
                if "directional_accuracy" in prediction_performance.c
                else func.avg(prediction_performance.c.mae).label("da"),
                prediction_performance.c.created_at,
            )
            .where(
                prediction_performance.c.horizon == horizon,
                prediction_performance.c.model_name == model_name,
                prediction_performance.c.mae.isnot(None),
                prediction_performance.c.forecast_date >= since,
            )
            .distinct(prediction_performance.c.forecast_date)
            .order_by(prediction_performance.c.forecast_date.asc())
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

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
        stmt = select(func.count()).select_from(prediction_performance)

        if horizon is not None:
            stmt = stmt.where(prediction_performance.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(
                prediction_performance.c.model_name == model_name
            )

        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def fetch_latest_forecast_date(
        self,
        horizon: str,
        model_name: str,
    ) -> Optional[datetime]:
        """Return the latest forecast_date for a (horizon, model).

        Used for idempotency: avoid running the same backtest twice
        on the same day.

        Args:
            horizon: Horizon label.
            model_name: Model identifier.

        Returns:
            Latest forecast_date, or None.
        """
        stmt = select(
            func.max(prediction_performance.c.forecast_date)
        ).where(
            prediction_performance.c.horizon == horizon,
            prediction_performance.c.model_name == model_name,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()