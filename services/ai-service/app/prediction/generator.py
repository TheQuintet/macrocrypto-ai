"""Prediction generator.

This module provides PredictionGenerator, which orchestrates the
end-to-end flow for generating a batch of forecasts:
    1. Load recent history from the database (via repository)
    2. Build a future frame for the target horizon
    3. Call the forecast model's predict()
    4. Persist predictions to the database (via repository)
    5. Invalidate the response cache for the affected key

The generator is model-agnostic — it depends only on the
ForecastModel interface. The same class works with Prophet today
and with any other ForecastModel implementation (including a
multi-model comparison engine wrapper) without modification.

Design:
    - Async (repository calls are async)
    - Fails loudly on missing model or insufficient data
    - Returns a structured GenerationResult
    - Does not commit — the caller controls the transaction
    - Cache invalidation is best-effort: failures are logged but
      do not affect the generation result
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from app.ai.base import ForecastModel
from app.database.repositories.prediction_repository import (
    PredictionRepository,
    PredictionRow,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Minimum rows of history needed to build a future frame.
# Must exceed the largest lag (30 days for tree models), but
# Prophet is more forgiving. 60 rows is our service-wide floor.
MIN_HISTORY_ROWS = 60

# Default confidence level for stored predictions
DEFAULT_CONFIDENCE = 0.85

# Pandas frequency alias for hourly data.
# Note: pandas 3.x removed the uppercase "H" alias — lowercase "h"
# is the canonical form and works across pandas 2.2 and 3.x.
HOURLY_FREQ = "h"


# ============================================================
# RESULT DATACLASS
# ============================================================
@dataclass
class GenerationResult:
    """Structured result of a prediction generation run.

    Attributes:
        horizon: Horizon label (e.g., '24h', '7d').
        model_name: Name of the model that produced predictions.
        prediction_time: When predictions were generated (UTC).
        rows_generated: Number of prediction rows produced by the model.
        rows_saved: Number of rows persisted to the database.
        confidence: Confidence level the bounds are expressed at.
        elapsed_seconds: Wall-clock time of the whole run.
        predictions: The raw predictions DataFrame (None on failure).
        error: Error message if the run failed, else None.
    """

    horizon: str
    model_name: str
    prediction_time: datetime
    rows_generated: int = 0
    rows_saved: int = 0
    confidence: float = DEFAULT_CONFIDENCE
    elapsed_seconds: float = 0.0
    predictions: Optional[pd.DataFrame] = None
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        """Return True if the run completed without error."""
        return self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict for logging and event publishing.

        The predictions DataFrame is converted to a list of records
        with datetimes serialized as ISO strings.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "horizon": self.horizon,
            "model_name": self.model_name,
            "prediction_time": self.prediction_time.isoformat(),
            "rows_generated": self.rows_generated,
            "rows_saved": self.rows_saved,
            "confidence": self.confidence,
            "elapsed_seconds": self.elapsed_seconds,
            "succeeded": self.succeeded,
            "error": self.error,
            "predictions": (
                self.predictions.to_dict(orient="records")
                if self.predictions is not None
                else None
            ),
        }

    def __repr__(self) -> str:
        """Return string representation."""
        status = "ok" if self.succeeded else "failed"
        return (
            f"GenerationResult("
            f"horizon='{self.horizon}', "
            f"model='{self.model_name}', "
            f"rows_saved={self.rows_saved}, "
            f"status='{status}')"
        )


# ============================================================
# GENERATOR
# ============================================================
class PredictionGenerator:
    """Generates a batch of predictions and persists them.

    The generator is model-agnostic — it depends on the
    ForecastModel abstract interface, not on any concrete model.

    Example:
        generator = PredictionGenerator(
            model=prophet_model,
            repository=repository,
            horizon="24h",
            horizon_hours=24,
            confidence=0.85,
        )
        result = await generator.generate()
    """

    def __init__(
        self,
        model: ForecastModel,
        repository: PredictionRepository,
        horizon: str = "24h",
        horizon_hours: int = 24,
        confidence: float = DEFAULT_CONFIDENCE,
        history_hours: int = 720,
    ) -> None:
        """Initialize the generator.

        Args:
            model: A ForecastModel instance (trained).
            repository: A PredictionRepository bound to a session.
            horizon: Horizon label, e.g. '24h' or '7d'.
            horizon_hours: Number of future hours to predict.
                For '24h' use 24. For '7d' use 168.
            confidence: Confidence level for stored bounds.
                One of 0.70, 0.85, 0.95.
            history_hours: How many hours of history to fetch.
                Defaults to 720 (30 days).

        Raises:
            ValueError: If confidence is not 0.70, 0.85, or 0.95.
            ValueError: If horizon_hours is not positive.
        """
        if confidence not in (0.70, 0.85, 0.95):
            raise ValueError(
                f"Invalid confidence {confidence}. "
                f"Must be one of 0.70, 0.85, 0.95."
            )

        if horizon_hours <= 0:
            raise ValueError(
                f"horizon_hours must be positive, got {horizon_hours}"
            )

        self.model = model
        self.repository = repository
        self.horizon = horizon
        self.horizon_hours = horizon_hours
        self.confidence = confidence
        self.history_hours = history_hours

        logger.info(
            f"PredictionGenerator initialized "
            f"(model={model.get_name()}, horizon={horizon}, "
            f"hours={horizon_hours}, confidence={confidence})"
        )

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def generate(self) -> GenerationResult:
        """Run one prediction generation cycle.

        Fetches history, builds a future frame, calls the model,
        persists predictions, invalidates the response cache, and
        returns a structured result.

        Never raises on data/model errors — instead returns a
        GenerationResult with `error` set. Only raises on truly
        unexpected failures (e.g., programming errors).

        Returns:
            GenerationResult with rows_generated, rows_saved,
            elapsed_seconds, and the raw predictions.
        """
        prediction_time = datetime.now(timezone.utc)
        start = prediction_time

        result = GenerationResult(
            horizon=self.horizon,
            model_name=self.model.get_name(),
            prediction_time=prediction_time,
            confidence=self.confidence,
        )

        try:
            # ---- 1. Verify the model is trained ----
            if not self.model.is_model_trained():
                raise RuntimeError(
                    f"Model '{self.model.get_name()}' is not trained. "
                    f"Cannot generate predictions."
                )

            # ---- 2. Fetch recent history ----
            logger.debug(
                f"Fetching {self.history_hours}h of history "
                f"for horizon={self.horizon}"
            )
            history = await self.repository.fetch_training_frame(
                hours=self.history_hours
            )

            if history is None or history.empty:
                raise ValueError(
                    "No history available from repository. "
                    "Cannot generate predictions."
                )

            if len(history) < MIN_HISTORY_ROWS:
                raise ValueError(
                    f"Insufficient history: got {len(history)} rows, "
                    f"need at least {MIN_HISTORY_ROWS}."
                )

            # ---- 3. Build future frame ----
            future_frame = self._build_future_frame(history)

            # ---- 4. Run the model ----
            logger.debug(
                f"Calling {self.model.get_name()}.predict() "
                f"for {len(future_frame)} future rows"
            )
            predictions = self.model.predict(future_frame)

            if predictions is None or predictions.empty:
                raise ValueError("Model returned empty predictions.")

            result.rows_generated = len(predictions)
            result.predictions = predictions

            # ---- 5. Convert to PredictionRow list ----
            rows = self._predictions_to_rows(
                predictions=predictions,
                prediction_time=prediction_time,
            )

            # ---- 6. Save to database ----
            logger.debug(f"Saving {len(rows)} prediction rows")
            saved = await self.repository.save_predictions(rows)
            result.rows_saved = saved

            # ---- 7. Invalidate the response cache (best-effort) ----
            await self._invalidate_cache()

            # ---- 8. Compute elapsed ----
            elapsed = (
                datetime.now(timezone.utc) - start
            ).total_seconds()
            result.elapsed_seconds = elapsed

            logger.info(
                f"Generated {result.rows_generated} predictions "
                f"({result.rows_saved} saved) for "
                f"model={result.model_name}, horizon={self.horizon} "
                f"in {elapsed:.3f}s"
            )

            return result

        except Exception as e:
            elapsed = (
                datetime.now(timezone.utc) - start
            ).total_seconds()
            result.elapsed_seconds = elapsed
            result.error = str(e)

            logger.error(
                f"Prediction generation failed for "
                f"model={self.model.get_name()}, horizon={self.horizon} "
                f"after {elapsed:.3f}s: {e}",
                exc_info=True,
            )

            return result

    async def _invalidate_cache(self) -> None:
        """Invalidate the response cache for this generator's key.

        Best-effort: failures are logged but never raised. Imported
        locally to avoid a hard dependency between the prediction
        package and the cache package.
        """
        try:
            from app.cache.prediction_cache import (
                invalidate_prediction_cache,
            )

            await invalidate_prediction_cache(
                horizon=self.horizon,
                model_name=self.model.get_name(),
                confidence=self.confidence,
            )
        except Exception as e:
            logger.warning(
                f"Cache invalidation failed after prediction save: {e}"
            )

    # ============================================================
    # FUTURE FRAME BUILDING
    # ============================================================
    def _build_future_frame(self, history: pd.DataFrame) -> pd.DataFrame:
        """Build a future frame for the model to predict on.

        The frame contains `horizon_hours` future timestamps, one
        per hour, starting after the last timestamp in `history`.
        All feature columns are forward-filled from the last known
        row so Prophet and tree models both receive valid inputs.

        Prophet ignores the `y` column when predicting. Tree models
        need `y` for lag feature engineering, so we fill it with
        the last known price.

        Args:
            history: DataFrame with at least a 'ds' column and
                regressor columns.

        Returns:
            DataFrame with `horizon_hours` rows and the same
            columns as `history`.

        Raises:
            ValueError: If history lacks a 'ds' column or is empty.
        """
        if "ds" not in history.columns:
            raise ValueError(
                "History frame is missing the 'ds' column."
            )

        if history.empty:
            raise ValueError("Cannot build future frame from empty history.")

        # Determine the last known timestamp
        last_ds = pd.to_datetime(history["ds"]).max()

        # Create the future timestamps (hourly)
        # Note: pandas 3.x requires lowercase "h" (uppercase "H" removed)
        future_times = pd.date_range(
            start=last_ds + timedelta(hours=1),
            periods=self.horizon_hours,
            freq=HOURLY_FREQ,
        )

        # Take the last known row as the template
        last_row = history.iloc[-1].to_dict()

        # Build the future frame
        future_rows = []
        for ts in future_times:
            row = dict(last_row)
            row["ds"] = ts
            future_rows.append(row)

        future_df = pd.DataFrame(future_rows)

        logger.debug(
            f"Built future frame: {len(future_df)} rows, "
            f"{len(future_df.columns)} columns, "
            f"from {future_times[0]} to {future_times[-1]}"
        )

        return future_df

    # ============================================================
    # ROW CONVERSION
    # ============================================================
    def _predictions_to_rows(
        self,
        predictions: pd.DataFrame,
        prediction_time: datetime,
    ) -> List[PredictionRow]:
        """Convert a predictions DataFrame into PredictionRow objects.

        The model returns a DataFrame with columns:
            ds, yhat, yhat_lower, yhat_upper

        These map to:
            time              = ds
            predicted_price   = yhat
            lower_bound       = yhat_lower
            upper_bound       = yhat_upper
            prediction_time   = the batch timestamp
            horizon           = self.horizon
            model_name        = self.model.get_name()
            confidence        = self.confidence

        Args:
            predictions: DataFrame from model.predict().
            prediction_time: The batch timestamp.

        Returns:
            List of PredictionRow instances.

        Raises:
            ValueError: If predictions is missing a required column.
        """
        required = {"ds", "yhat", "yhat_lower", "yhat_upper"}
        missing = required - set(predictions.columns)
        if missing:
            raise ValueError(
                f"Predictions are missing required columns: {missing}"
            )

        rows: List[PredictionRow] = []
        for _, row in predictions.iterrows():
            rows.append(
                PredictionRow(
                    time=pd.to_datetime(row["ds"]).to_pydatetime(),
                    prediction_time=prediction_time,
                    horizon=self.horizon,
                    model_name=self.model.get_name(),
                    confidence=self.confidence,
                    predicted_price=float(row["yhat"]),
                    lower_bound=float(row["yhat_lower"]),
                    upper_bound=float(row["yhat_upper"]),
                )
            )

        return rows

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"PredictionGenerator("
            f"model='{self.model.get_name()}', "
            f"horizon='{self.horizon}', "
            f"hours={self.horizon_hours}, "
            f"confidence={self.confidence})"
        )