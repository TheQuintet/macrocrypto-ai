"""Performance repository.

Encapsulates all database reads and writes for the
prediction_performance table (created in T5.1):
    - Writing per-point evaluation rows (from T5.2's backtester)
    - Reading the latest aggregated metrics per (horizon, model)
    - Reading historical metrics over a time window
    - Batch reads for the T5.5 performance API

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Validates rows before insertion, then writes in a single
      bulk INSERT.
    - Does not commit — the caller controls the transaction.

CLI isolation:
    When settings.cli_mode is True, all reads and writes on the
    prediction_performance table are routed to
    prediction_performance_cli instead. This keeps CLI runs
    sandboxed from production data. Routing is handled by
    `_resolve_performance_table()`.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.tables import (
    prediction_performance,
    prediction_performance_cli,
)

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
    # CLI ROUTING HELPER
    # ============================================================
    def _resolve_performance_table(self):
        """Return the active prediction_performance table.

        In CLI mode (settings.cli_mode=True), returns
        prediction_performance_cli so CLI runs are sandboxed.
        Otherwise returns the production table.

        Returns:
            A SQLAlchemy Table object.
        """
        if settings.cli_mode:
            return prediction_performance_cli
        return prediction_performance

    # ============================================================
    # WRITES
    # ============================================================
    async def save_performance_rows(
        self, rows: List[PerformanceRow]
    ) -> int:
        """Bulk-insert performance rows into prediction_performance.

        Validates all rows before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        CLI mode: when settings.cli_mode is True, rows are written
        to prediction_performance_cli instead.

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
        from app.database.validators import validate_performance_rows

        dict_rows = [r.to_dict() for r in rows]
        validate_performance_rows(dict_rows)

        table = self._resolve_performance_table()
        stmt = insert(table).values(dict_rows)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(
            f"Inserted {len(dict_rows)} rows into {table.name}"
        )

        return len(dict_rows)

    # ============================================================
    # READS — single key
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
        table = self._resolve_performance_table()

        stmt = (
            select(
                table.c.horizon,
                table.c.model_name,
                table.c.model_version,
                table.c.forecast_date,
                table.c.mae,
                table.c.rmse,
                table.c.mape,
                table.c.market_condition,
                table.c.created_at,
            )
            .where(
                table.c.horizon == horizon,
                table.c.model_name == model_name,
                table.c.mae.isnot(None),
            )
            .order_by(desc(table.c.forecast_date))
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
        table = self._resolve_performance_table()
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                table.c.forecast_date,
                table.c.mae,
                table.c.rmse,
                table.c.mape,
                table.c.created_at,
            )
            .where(
                table.c.horizon == horizon,
                table.c.model_name == model_name,
                table.c.mae.isnot(None),
                table.c.forecast_date >= since,
            )
            .distinct(table.c.forecast_date)
            .order_by(
                table.c.forecast_date.asc(),
            )
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
        table = self._resolve_performance_table()
        stmt = select(func.count()).select_from(table)

        if horizon is not None:
            stmt = stmt.where(table.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(table.c.model_name == model_name)

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
        table = self._resolve_performance_table()

        stmt = select(
            func.max(table.c.forecast_date)
        ).where(
            table.c.horizon == horizon,
            table.c.model_name == model_name,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ============================================================
    # READS — batch (T5.5 performance API)
    # ============================================================
    async def fetch_latest_metrics_batch(
        self,
        days: int,
        horizon: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch latest aggregated metrics for many (model, horizon) pairs.

        Uses a single query with GROUP BY to return one row per
        distinct (model_name, horizon). If `model_name` or `horizon`
        are provided, results are filtered accordingly.

        The returned row's metrics are the aggregate metrics of the
        most recent evaluation batch for that (model, horizon).
        "Most recent" is determined by `forecast_date`.

        Args:
            days: Look-back window in days.
            horizon: Optional horizon filter.
            model_name: Optional model filter.

        Returns:
            List of dicts with keys: horizon, model_name,
            model_version, forecast_date, mae, rmse, mape,
            directional_accuracy, samples.
        """
        table = self._resolve_performance_table()
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # We use a correlated subquery: "the row with the max
        # forecast_date for this group". This is more portable than
        # DISTINCT ON and works with our composite PK.
        stmt = select(
            table.c.horizon,
            table.c.model_name,
            table.c.model_version,
            table.c.forecast_date,
            table.c.mae,
            table.c.rmse,
            table.c.mape,
        ).where(
            table.c.forecast_date >= since,
            table.c.mae.isnot(None),
        )

        if horizon is not None:
            stmt = stmt.where(table.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(table.c.model_name == model_name)

        stmt = stmt.order_by(
            table.c.model_name.asc(),
            table.c.horizon.asc(),
            desc(table.c.forecast_date),
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        # Deduplicate in Python: keep the first row per (model, horizon)
        # since rows are already sorted by forecast_date DESC within
        # each group.
        seen: set = set()
        latest_rows: List[Dict[str, Any]] = []
        for row in rows:
            key = (row["model_name"], row["horizon"])
            if key in seen:
                continue
            seen.add(key)
            latest_rows.append(dict(row))

        # Compute sample counts per (model, horizon) with a second
        # small aggregation. We need this for the `samples` field.
        counts = await self._fetch_sample_counts(
            since=since,
            horizon=horizon,
            model_name=model_name,
        )

        for row in latest_rows:
            key = (row["model_name"], row["horizon"])
            row["samples"] = counts.get(key, 0)

        return latest_rows

    async def fetch_best_model_by_mae(
        self,
        horizon: str,
        days: int = 30,
        model_names: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Return the model with the lowest MAE in the recent window.

        Averages MAE per model over the look-back window, then picks
        the model with the smallest mean MAE. Models with no MAE
        rows in the window are excluded.

        Called by the M6a multi-model comparison endpoint to surface
        "best model overall" alongside the per-model batches. The
        returned name may not be one of the models in the comparison
        — it reflects the overall best in the window, which is what
        the schema documents.

        Args:
            horizon: Horizon label ('24h' or '7d').
            days: Look-back window in days.
            model_names: Optional list of model names to restrict
                the search to. If None, all models with recent MAE
                data are considered.

        Returns:
            Model name with the lowest mean MAE, or None if no
            model has MAE data in the window.
        """
        table = self._resolve_performance_table()
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # Build the WHERE clause before adding GROUP BY / ORDER BY /
        # LIMIT — SQLAlchemy 2.x requires this ordering.
        stmt = select(
            table.c.model_name,
            func.avg(table.c.mae).label("mean_mae"),
        ).where(
            table.c.horizon == horizon,
            table.c.forecast_date >= since,
            table.c.mae.isnot(None),
        )

        if model_names:
            stmt = stmt.where(table.c.model_name.in_(model_names))

        stmt = (
            stmt.group_by(table.c.model_name)
            .order_by(func.avg(table.c.mae).asc())
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

    async def fetch_market_breakdown(
        self,
        horizon: str,
        model_name: str,
        days: int,
    ) -> List[Dict[str, Any]]:
        """Fetch per-market-condition aggregates.

        Groups the window's rows by `market_condition` and returns
        the mean of each metric per bucket.

        Args:
            horizon: Horizon label.
            model_name: Model identifier.
            days: Look-back window in days.

        Returns:
            List of dicts with keys: market_condition, mae, rmse,
            mape, samples. Only conditions with at least one row
            are returned.
        """
        table = self._resolve_performance_table()
        since = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                table.c.market_condition,
                func.avg(table.c.mae).label("mae"),
                func.avg(table.c.rmse).label("rmse"),
                func.avg(table.c.mape).label("mape"),
                func.count().label("samples"),
            )
            .where(
                table.c.horizon == horizon,
                table.c.model_name == model_name,
                table.c.forecast_date >= since,
                table.c.market_condition.isnot(None),
                table.c.mae.isnot(None),
            )
            .group_by(table.c.market_condition)
            .order_by(table.c.market_condition.asc())
        )

        result = await self.session.execute(stmt)
        return [dict(row) for row in result.mappings().all()]

    async def _fetch_sample_counts(
        self,
        since: datetime,
        horizon: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> Dict[tuple, int]:
        """Return a mapping of (model_name, horizon) → row count.

        Used by `fetch_latest_metrics_batch` to populate the
        `samples` field.

        Args:
            since: Lower bound for forecast_date.
            horizon: Optional horizon filter.
            model_name: Optional model filter.

        Returns:
            Dict keyed by (model_name, horizon), values are ints.
        """
        table = self._resolve_performance_table()

        stmt = (
            select(
                table.c.model_name,
                table.c.horizon,
                func.count().label("samples"),
            )
            .where(
                table.c.forecast_date >= since,
                table.c.mae.isnot(None),
            )
            .group_by(
                table.c.model_name,
                table.c.horizon,
            )
        )

        if horizon is not None:
            stmt = stmt.where(table.c.horizon == horizon)
        if model_name is not None:
            stmt = stmt.where(table.c.model_name == model_name)

        result = await self.session.execute(stmt)
        return {
            (row["model_name"], row["horizon"]): int(row["samples"])
            for row in result.mappings().all()
        }