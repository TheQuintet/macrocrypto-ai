"""Prediction repository.

Encapsulates all database reads and writes needed by the prediction
generation pipeline:
    - Reading recent BTC price data (target + BTC regressors)
    - Reading recent macro indicator data (macro regressors)
    - Merging both into a single training/prediction frame
    - Reading BTC prices for a historical date range or a specific
      historical timestamp (A5.2)
    - Writing generated predictions to the btc_predictions table
    - Reading stored predictions for the API layer

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - Predictions are validated before insertion, then written in a
      single bulk INSERT.

Feature sources:
    The repository exposes multiple methods for obtaining training
    and prediction frames. They share the same (hours, partition)
    signature so callers can treat them interchangeably:

        fetch_training_frame_legacy(hours)
            DEPRECATED. Reads from btc_prices + macro_indicators
            (10-feature Postgres source).

        fetch_training_frame_from_files(hours, partition)
            Reads from data-service parquet files (50-feature
            canonical source). Requires an explicit partition.

        fetch_training_frame_from_features_db(hours, partition=None)
            Reads from the future feature_store DB table (50-feature
            canonical source). Raises NotImplementedError until the
            table exists.

        fetch_training_frame_for_source(hours, context, partition=None)
            Dispatcher. Chooses the source based on
            settings.feature_source and resolves the default
            partition from the context. This is what callers should
            use — not the individual methods.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.enums import FeatureContext, FeaturePartition
from app.database.tables import (
    btc_predictions,
    btc_prices,
    macro_indicators,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONTEXT -> PARTITION MAP
# ============================================================
# Maps a caller's intent (FeatureContext) to the default partition
# (FeaturePartition) used by the file-based feature source.
#
# Kept as a module-level constant so the dispatcher has exactly
# one source of truth for the mapping. Adding a new context here
# forces the type checker to require a corresponding mapping.
_CONTEXT_TO_PARTITION: Dict[FeatureContext, FeaturePartition] = {
    FeatureContext.TRAINING: FeaturePartition.TRAIN,
    FeatureContext.VALIDATION: FeaturePartition.VAL,
    FeatureContext.TEST: FeaturePartition.TEST,
    FeatureContext.PREDICTION: FeaturePartition.LIVE_FRONTIER,
}


# ============================================================
# ROW DATACLASS
# ============================================================
@dataclass
class PredictionRow:
    """A single prediction row to insert into btc_predictions.

    Attributes:
        time: The forecast timestamp (the time being predicted for).
        prediction_time: When the prediction was made.
        horizon: One of '24h', '7d'.
        model_name: One of 'prophet', 'xgboost', 'lightgbm', ...
        confidence: One of 0.70, 0.85, 0.95.
        predicted_price: The point forecast.
        lower_bound: Lower confidence bound.
        upper_bound: Upper confidence bound.
    """

    time: datetime
    prediction_time: datetime
    horizon: str
    model_name: str
    confidence: float
    predicted_price: float
    lower_bound: float
    upper_bound: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict suitable for SQLAlchemy insert()."""
        return {
            "time": self.time,
            "prediction_time": self.prediction_time,
            "horizon": self.horizon,
            "model_name": self.model_name,
            "confidence": self.confidence,
            "predicted_price": self.predicted_price,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
        }


# ============================================================
# REPOSITORY
# ============================================================
class PredictionRepository:
    """Repository for reading source data and writing predictions.

    All methods are async and take/return DataFrames, rows, or
    scalars. The repository does not commit — the caller controls
    transactions via session_scope().

    Example:
        async with session_scope() as session:
            repo = PredictionRepository(session)
            df = await repo.fetch_recent_btc_data(hours=200)
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: An AsyncSession bound to the target database.
        """
        self.session = session

    # ============================================================
    # READS — source data
    # ============================================================
    async def fetch_recent_btc_data(self, hours: int) -> pd.DataFrame:
        """Fetch the last `hours` of BTC price data.

        Args:
            hours: Number of most recent hours to fetch.

        Returns:
            DataFrame with columns:
                time, close, volume, volatility, dominance,
                active_addresses, price_lag_7d
            Sorted ascending by time.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(
                btc_prices.c.time,
                btc_prices.c.close,
                btc_prices.c.volume,
                btc_prices.c.volatility,
                btc_prices.c.dominance,
                btc_prices.c.active_addresses,
                btc_prices.c.price_lag_7d,
            )
            .where(btc_prices.c.time >= since)
            .order_by(btc_prices.c.time.asc())
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        logger.debug(
            f"Fetched {len(rows)} BTC price rows (hours={hours})"
        )

        return pd.DataFrame(
            [
                {
                    "time": r["time"],
                    "close": r["close"],
                    "volume": r["volume"],
                    "volatility": r["volatility"],
                    "dominance": r["dominance"],
                    "active_addresses": r["active_addresses"],
                    "price_lag_7d": r["price_lag_7d"],
                }
                for r in rows
            ]
        )

    async def fetch_recent_macro_data(self, hours: int) -> pd.DataFrame:
        """Fetch the last `hours` of macro indicator data.

        Args:
            hours: Number of most recent hours to fetch.

        Returns:
            DataFrame with columns:
                time, cpi, interest_rate, m2_growth, dxy, treasury_yield
            Sorted ascending by time.
        """
        since = datetime.now(timezone.utc) - timedelta(hours=hours)

        stmt = (
            select(
                macro_indicators.c.time,
                macro_indicators.c.cpi,
                macro_indicators.c.interest_rate,
                macro_indicators.c.m2_growth,
                macro_indicators.c.dxy,
                macro_indicators.c.treasury_yield,
            )
            .where(macro_indicators.c.time >= since)
            .order_by(macro_indicators.c.time.asc())
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        logger.debug(
            f"Fetched {len(rows)} macro rows (hours={hours})"
        )

        return pd.DataFrame(
            [
                {
                    "time": r["time"],
                    "cpi": r["cpi"],
                    "interest_rate": r["interest_rate"],
                    "m2_growth": r["m2_growth"],
                    "dxy": r["dxy"],
                    "treasury_yield": r["treasury_yield"],
                }
                for r in rows
            ]
        )

    # ============================================================
    # READS — training / prediction frames (multi-source)
    # ============================================================
    async def fetch_training_frame_legacy(self, hours: int) -> pd.DataFrame:
        """Fetch and merge BTC + macro data from the legacy Postgres tables.

        DEPRECATED (2026-XX): This method reads the 10-feature
        Postgres source (btc_prices + macro_indicators), which has
        been superseded by the 50-feature canonical dataset. Kept
        for reference during the current migration; do not call
        from new code.

        See known_issues.md #1, #2, #3, #17 for the migration
        context.

        Args:
            hours: Number of most recent hours to fetch from each
                source.

        Returns:
            DataFrame with columns:
                ds, y, cpi, interest_rate, m2_growth, dxy,
                treasury_yield, volume, volatility, dominance,
                active_addresses, price_lag_7d
            Sorted ascending by ds.
        """
        btc_df = await self.fetch_recent_btc_data(hours=hours)
        macro_df = await self.fetch_recent_macro_data(hours=hours)

        if btc_df.empty:
            logger.warning("BTC data is empty — returning empty frame")
            return pd.DataFrame()

        # Rename BTC columns to Prophet's expected names
        btc_df = btc_df.rename(columns={"time": "ds", "close": "y"})

        # If macro is empty, still return BTC-only frame (with NaN macro)
        if macro_df.empty:
            logger.warning("Macro data is empty — using BTC only")
            merged = btc_df.copy()
        else:
            merged = pd.merge(
                btc_df,
                macro_df,
                left_on="ds",
                right_on="time",
                how="left",
            ).drop(columns=["time"])

            # Forward-fill macro columns (daily → hourly)
            macro_cols = [
                "cpi",
                "interest_rate",
                "m2_growth",
                "dxy",
                "treasury_yield",
            ]
            merged[macro_cols] = merged[macro_cols].ffill()

        # Ensure sorted ascending by ds
        merged = merged.sort_values("ds").reset_index(drop=True)

        logger.info(
            f"Built legacy training frame: {len(merged)} rows, "
            f"{len(merged.columns)} columns"
        )

        return merged

    async def fetch_training_frame_from_files(
        self,
        hours: int,
        partition: FeaturePartition,
    ) -> pd.DataFrame:
        """Read a training frame from the data-service parquet files.

        Loads the requested partition (train / val / test /
        live_frontier), then slices to the last `hours` of rows. The
        returned DataFrame carries the canonical 50-feature set with
        the model-expected column names.

        Unlike the legacy source, this method returns the frame as
        stored on disk — no column renames beyond the timestamp and
        target aliases, no forward-fill. The parquet files are the
        source of truth.

        Args:
            hours: How much history to return (in hours). The
                partition is sliced to its last `hours` rows.
            partition: Which partition to load, as a FeaturePartition
                value. Callers who do not want to reason about
                partitions directly should use
                fetch_training_frame_for_source() with a
                FeatureContext.

        Returns:
            DataFrame with the canonical 50 features plus timestamp
            and target columns, sorted ascending by time.

        Raises:
            FileNotFoundError: If the parquet file for the requested
                partition does not exist.
            ValueError: If the partition value is not recognized.
        """
        # Imported locally to avoid a hard dependency between the
        # repository package and the utils package at module load.
        from app.utils.feature_loader import FeatureLoader

        loader = FeatureLoader()
        df = loader.load_partition(partition.value)

        if df.empty:
            logger.warning(
                f"Partition '{partition.value}' is empty — "
                f"returning empty frame"
            )
            return df

        # Slice to the last `hours` rows.
        #
        # The parquet files are ordered ascending by time (the
        # data-service writes them that way). We take the tail so
        # "the last N hours" reads naturally regardless of the
        # file's actual size.
        if len(df) > hours:
            df = df.tail(hours).reset_index(drop=True)

        # Rename the timestamp and target columns to the model
        # adapters' expected names if they came from the file with
        # alternative names.
        rename_map = {
            "observation_date": "ds",
            "target_next_price": "y",
        }
        rename_map = {
            k: v for k, v in rename_map.items() if k in df.columns
        }
        if rename_map:
            df = df.rename(columns=rename_map)

        # ---- NEW: strip timezone from ds ----
        # Prophet requires `ds` to be timezone-naive. The parquet
        # files write it as tz-aware (UTC); strip the tz here so
        # every consumer sees a consistent, Prophet-compatible
        # timestamp column. Tree models ignore `ds`, so this is
        # safe for them too.
        if "ds" in df.columns:
            df["ds"] = pd.to_datetime(df["ds"]).dt.tz_localize(None)


        logger.info(
            f"Loaded training frame from parquet "
            f"(partition='{partition.value}', hours={hours}, "
            f"rows={len(df)}, cols={len(df.columns)})"
        )

        return df

    async def fetch_training_frame_from_features_db(
        self,
        hours: int,
        partition: Optional[FeaturePartition] = None,
    ) -> pd.DataFrame:
        """Read a training frame from the future features DB table.

        PLACEHOLDER — not yet implemented. The table does not exist
        yet; it will be created by a future migration and populated
        by the data-service (or a dedicated sync job). When that
        happens, replace the body of this method with the actual
        query.

        The signature matches fetch_training_frame_from_files so
        callers can treat both sources interchangeably.

        Args:
            hours: How much history to return (in hours).
            partition: Optional partition filter. When the table
                exists, this may map to a partition column, or be
                ignored if partitions are not modeled in the DB.

        Returns:
            DataFrame with the canonical 50 features.

        Raises:
            NotImplementedError: Always, until the table is built.
        """
        raise NotImplementedError(
            "The features_db source is not yet implemented. "
            "The future feature_store table has not been created. "
            "Use feature_source='parquet' until the migration lands."
        )

    async def fetch_training_frame_for_source(
        self,
        hours: int,
        context: FeatureContext,
        partition: Optional[FeaturePartition] = None,
    ) -> pd.DataFrame:
        """Dispatch to the configured feature source.

        Chooses the source based on settings.feature_source and
        resolves the default partition (for the file source) from
        the caller's context. This is the method new code should
        call — not the individual source-specific methods.

        Args:
            hours: How much history to return (in hours).
            context: What the caller is doing. Determines the
                default partition for the file-based source:
                    TRAINING    -> train
                    VALIDATION  -> val
                    TEST        -> test
                    PREDICTION  -> live_frontier
            partition: Optional explicit partition override. When
                provided, takes precedence over the context-derived
                default.

        Returns:
            DataFrame from the selected source.

        Raises:
            ValueError: If feature_source is unknown.
            NotImplementedError: If feature_source="features_db"
                and the future table has not been created yet.
        """
        source = settings.feature_source

        # Resolve the partition.
        resolved_partition = (
            partition
            if partition is not None
            else _CONTEXT_TO_PARTITION[context]
        )

        if source == "parquet":
            return await self.fetch_training_frame_from_files(
                hours=hours,
                partition=resolved_partition,
            )

        if source == "features_db":
            return await self.fetch_training_frame_from_features_db(
                hours=hours,
                partition=resolved_partition,
            )

        raise ValueError(
            f"Unsupported feature_source '{source}'. "
            f"Expected 'parquet' or 'features_db'."
        )

    # ============================================================
    # READS — historical BTC (A5.2)
    # ============================================================
    async def fetch_btc_price_at(
        self,
        target_time: datetime,
        *,
        tolerance_hours: int = 1,
    ) -> Optional[float]:
        """Fetch the BTC close price nearest to a given historical time.

        Used by A5.2's reaction calculation to get "the price 24h
        before the event" and "the price 24h after the event". The
        price series is hourly, so an exact match on ``target_time``
        is not guaranteed; the method returns the closest row within
        ``tolerance_hours``.

        The search is bounded by ``tolerance_hours`` in each
        direction. If no row falls within the tolerance, returns
        None so the caller can record the event as skipped.

        Args:
            target_time: The historical timestamp to look near. Must
                be timezone-aware; a naive datetime is interpreted
                as UTC.
            tolerance_hours: Maximum distance in hours between
                ``target_time`` and the returned row's time. Default
                1 hour.

        Returns:
            The close price as a float, or None if no row is within
            tolerance.
        """
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        lower_bound = target_time - timedelta(hours=tolerance_hours)
        upper_bound = target_time + timedelta(hours=tolerance_hours)

        stmt = (
            select(btc_prices.c.close)
            .where(
                btc_prices.c.time >= lower_bound,
                btc_prices.c.time <= upper_bound,
            )
            .order_by(btc_prices.c.time.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)
        value = result.scalar_one_or_none()

        if value is None:
            logger.debug(
                f"No BTC price within {tolerance_hours}h of "
                f"{target_time.isoformat()}"
            )
            return None

        return float(value)

    async def fetch_btc_prices_range(
        self,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """Fetch every BTC price row in the inclusive time range.

        Used by A5.2's volatility calculation, which needs the full
        series over the reaction window, not just the two endpoints.
        Returns a DataFrame with columns ``time`` and ``close``,
        sorted ascending by time.

        Args:
            start: Earliest timestamp to include. Must be
                timezone-aware; a naive datetime is interpreted as
                UTC.
            end: Latest timestamp to include. Must be
                timezone-aware; a naive datetime is interpreted as
                UTC.

        Returns:
            DataFrame with columns ``time`` (tz-aware datetime) and
            ``close`` (float). Empty when no rows match.
        """
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)

        stmt = (
            select(btc_prices.c.time, btc_prices.c.close)
            .where(
                btc_prices.c.time >= start,
                btc_prices.c.time <= end,
            )
            .order_by(btc_prices.c.time.asc())
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        logger.debug(
            f"Fetched {len(rows)} BTC price rows in "
            f"[{start.isoformat()}, {end.isoformat()}]"
        )

        return pd.DataFrame(
            [
                {"time": r["time"], "close": r["close"]}
                for r in rows
            ]
        )

    # ============================================================
    # READS — stored predictions (API layer)
    # ============================================================
    async def fetch_latest_predictions(
        self,
        horizon: str = "24h",
        model_name: str = "prophet",
        confidence: float = 0.85,
    ) -> List[PredictionRow]:
        """Fetch the most recent prediction batch for the given key.

        A "batch" is all rows sharing the same `prediction_time` for
        a given (horizon, model_name, confidence). The generator
        writes each forecast run as a batch of N rows (24 for a
        daily horizon, 168 for a weekly one).

        Returns an empty list if no rows exist for the given key.

        Args:
            horizon: Horizon label ('24h' or '7d').
            model_name: Model identifier ('prophet', 'xgboost', ...).
            confidence: Confidence level (0.70, 0.85, 0.95).

        Returns:
            List of PredictionRow instances ordered by `time` ascending.
            Empty if there are no matching rows.
        """
        from sqlalchemy import func

        # Subquery: latest prediction_time for this key
        latest_ts_stmt = select(
            func.max(btc_predictions.c.prediction_time)
        ).where(
            btc_predictions.c.horizon == horizon,
            btc_predictions.c.model_name == model_name,
            btc_predictions.c.confidence == confidence,
        )

        result = await self.session.execute(latest_ts_stmt)
        latest_ts = result.scalar_one_or_none()

        if latest_ts is None:
            logger.debug(
                f"No predictions found for "
                f"(horizon={horizon}, model={model_name}, "
                f"confidence={confidence})"
            )
            return []

        # Fetch all rows in that batch
        stmt = (
            select(
                btc_predictions.c.time,
                btc_predictions.c.prediction_time,
                btc_predictions.c.horizon,
                btc_predictions.c.model_name,
                btc_predictions.c.confidence,
                btc_predictions.c.predicted_price,
                btc_predictions.c.lower_bound,
                btc_predictions.c.upper_bound,
            )
            .where(
                btc_predictions.c.horizon == horizon,
                btc_predictions.c.model_name == model_name,
                btc_predictions.c.confidence == confidence,
                btc_predictions.c.prediction_time == latest_ts,
            )
            .order_by(btc_predictions.c.time.asc())
        )

        result = await self.session.execute(stmt)
        rows = result.mappings().all()

        logger.debug(
            f"Fetched {len(rows)} prediction rows for "
            f"(horizon={horizon}, model={model_name}, "
            f"confidence={confidence}, prediction_time={latest_ts})"
        )

        return [
            PredictionRow(
                time=r["time"],
                prediction_time=r["prediction_time"],
                horizon=r["horizon"],
                model_name=r["model_name"],
                confidence=r["confidence"],
                predicted_price=r["predicted_price"],
                lower_bound=r["lower_bound"],
                upper_bound=r["upper_bound"],
            )
            for r in rows
        ]

    async def fetch_latest_predictions_batch(
        self,
        model_names: List[str],
        horizon: str = "24h",
        confidence: float = 0.85,
    ) -> Dict[str, List[PredictionRow]]:
        """Fetch the latest prediction batch for each requested model.

        Runs two queries regardless of how many models are requested:
            1. The latest `prediction_time` per model (GROUP BY
               model_name).
            2. All rows in those batches, filtered by an OR of
               (model_name, prediction_time) pairs.

        Returns a mapping keyed by model name. Models with no stored
        rows do not appear as keys — the caller decides whether to
        surface them as "missing".

        Called by the M6a multi-model comparison endpoint; the two-
        query design keeps latency flat as the model count grows.

        Args:
            model_names: Names of the models to fetch. Empty input
                short-circuits without touching the DB.
            horizon: Horizon label ('24h' or '7d').
            confidence: Confidence level (0.70, 0.85, 0.95).

        Returns:
            Dict mapping model_name → List[PredictionRow], ordered
            by `time` ascending within each batch. Missing models
            are omitted from the result.
        """
        from sqlalchemy import and_, func, or_

        if not model_names:
            logger.debug(
                "fetch_latest_predictions_batch called with empty "
                "model_names list"
            )
            return {}

        # ---- Step 1: latest prediction_time per model ----
        latest_stmt = (
            select(
                btc_predictions.c.model_name,
                func.max(btc_predictions.c.prediction_time).label(
                    "latest_ts"
                ),
            )
            .where(
                btc_predictions.c.horizon == horizon,
                btc_predictions.c.model_name.in_(model_names),
                btc_predictions.c.confidence == confidence,
            )
            .group_by(btc_predictions.c.model_name)
        )

        result = await self.session.execute(latest_stmt)
        latest_by_model: Dict[str, Any] = {
            row["model_name"]: row["latest_ts"]
            for row in result.mappings().all()
        }

        if not latest_by_model:
            logger.debug(
                f"No latest batches found for "
                f"(models={model_names}, horizon={horizon}, "
                f"confidence={confidence})"
            )
            return {}

        # ---- Step 2: fetch all rows in those batches ----
        conditions = [
            and_(
                btc_predictions.c.model_name == name,
                btc_predictions.c.prediction_time == ts,
            )
            for name, ts in latest_by_model.items()
        ]

        rows_stmt = (
            select(
                btc_predictions.c.time,
                btc_predictions.c.prediction_time,
                btc_predictions.c.horizon,
                btc_predictions.c.model_name,
                btc_predictions.c.confidence,
                btc_predictions.c.predicted_price,
                btc_predictions.c.lower_bound,
                btc_predictions.c.upper_bound,
            )
            .where(
                btc_predictions.c.horizon == horizon,
                btc_predictions.c.confidence == confidence,
                or_(*conditions),
            )
            .order_by(
                btc_predictions.c.model_name.asc(),
                btc_predictions.c.time.asc(),
            )
        )

        result = await self.session.execute(rows_stmt)

        batches: Dict[str, List[PredictionRow]] = {}
        for r in result.mappings().all():
            batches.setdefault(r["model_name"], []).append(
                PredictionRow(
                    time=r["time"],
                    prediction_time=r["prediction_time"],
                    horizon=r["horizon"],
                    model_name=r["model_name"],
                    confidence=r["confidence"],
                    predicted_price=r["predicted_price"],
                    lower_bound=r["lower_bound"],
                    upper_bound=r["upper_bound"],
                )
            )

        logger.debug(
            f"Fetched batches for "
            f"{len(batches)}/{len(model_names)} models "
            f"(horizon={horizon}, confidence={confidence})"
        )

        return batches

    async def fetch_latest_close_price(self) -> Optional[float]:
        """Fetch the most recent BTC close price.

        Reads from the Data Ingestion Service's `btc_prices` table.

        Returns:
            The latest close price as a float, or None if the table
            is empty or unavailable.
        """
        stmt = (
            select(btc_prices.c.close)
            .order_by(btc_prices.c.time.desc())
            .limit(1)
        )

        try:
            result = await self.session.execute(stmt)
            value = result.scalar_one_or_none()
        except Exception as e:
            logger.warning(
                f"Failed to fetch latest close price from btc_prices: {e}"
            )
            return None

        if value is None:
            logger.debug("btc_prices is empty — no current price available")
            return None

        return float(value)

    # ============================================================
    # WRITES
    # ============================================================
    async def save_predictions(
        self, rows: List[PredictionRow]
    ) -> int:
        """Bulk-insert prediction rows into btc_predictions.

        Supports all horizons (`'24h'`, `'7d'`) and all models
        (`'prophet'`, and later `'xgboost'`/`'lightgbm'`). The
        `horizon` and `model_name` are taken from each PredictionRow.

        Validates all rows before insertion. Does not commit — the
        caller controls the transaction via session_scope().

        Args:
            rows: List of PredictionRow instances.

        Returns:
            Number of rows inserted (0 if rows is empty).

        Raises:
            ValueError: If any row fails validation.
        """
        if not rows:
            logger.debug("save_predictions called with empty list")
            return 0

        # Validate all rows before touching the database.
        # Imported locally to avoid a circular import: validators.py
        # imports PredictionRow from this module.
        from app.database.validators import validate_prediction_rows

        validate_prediction_rows(rows)

        payload = [r.to_dict() for r in rows]

        stmt = insert(btc_predictions).values(payload)
        await self.session.execute(stmt)
        await self.session.flush()

        logger.info(f"Inserted {len(payload)} prediction rows")

        return len(payload)

    # ============================================================
    # CONVENIENCE
    # ============================================================
    async def fetch_latest_prediction_time(
        self, horizon: str, model_name: str
    ) -> Optional[datetime]:
        """Return the latest prediction_time for a given horizon/model.

        Useful for idempotency checks (avoid re-inserting the same
        prediction batch twice).

        Args:
            horizon: '24h' or '7d'.
            model_name: 'prophet', 'xgboost', 'lightgbm', ...

        Returns:
            Latest prediction_time, or None if no rows exist.
        """
        from sqlalchemy import func

        stmt = select(func.max(btc_predictions.c.prediction_time)).where(
            btc_predictions.c.horizon == horizon,
            btc_predictions.c.model_name == model_name,
        )

        result = await self.session.execute(stmt)
        value = result.scalar_one_or_none()

        return value