"""Prediction repository.

Encapsulates all database reads and writes needed by the prediction
generation pipeline:
    - Reading recent BTC price data (target + BTC regressors)
    - Reading recent macro indicator data (macro regressors)
    - Merging both into a single training/prediction frame
    - Writing generated predictions to the btc_predictions table
    - Reading stored predictions for the API layer

Design:
    - Takes an AsyncSession in the constructor. Callers wire the
      session from app.database.engine.session_scope().
    - Uses SQLAlchemy Core for queries (typesafe, parameterized).
    - The merged DataFrame is prepared for Prophet (columns: ds, y,
      plus all 10 regressors).
    - Predictions are validated before insertion, then written in a
      single bulk INSERT.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.tables import (
    btc_predictions,
    btc_prices,
    macro_indicators,
)

logger = logging.getLogger(__name__)


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

    async def fetch_training_frame(self, hours: int) -> pd.DataFrame:
        """Fetch and merge BTC + macro data into a single frame.

        Merges on `time` (outer join), forward-fills macro columns
        (macro data is daily → hourly needs ffill), renames `time` to
        `ds` and `close` to `y`, and returns a frame ready for Prophet.

        Args:
            hours: Number of most recent hours to fetch from each source.

        Returns:
            DataFrame with columns:
                ds, y, cpi, interest_rate, m2_growth, dxy, treasury_yield,
                volume, volatility, dominance, active_addresses, price_lag_7d
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
            f"Built training frame: {len(merged)} rows, "
            f"{len(merged.columns)} columns"
        )

        return merged

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