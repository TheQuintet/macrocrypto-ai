"""Walk-forward backtesting for forecasting models.

This module implements walk-forward backtesting: for each of the
last N days, it retrains a model on data up to that day, predicts
the target horizon, and compares against actuals observed later.

The engine is model-agnostic — it depends only on the ForecastModel
interface. It supports both fresh models (trained from scratch each
iteration) and warm-start strategies (chained across iterations).

Design:
    - Async interface; each iteration is awaited
    - Model factory pattern: the caller supplies a callable that
      returns a fresh, untrained ForecastModel instance for each
      iteration
    - Warm-start chaining: after each iteration, the model is saved
      to a per-run temp directory; the next iteration loads it as
      the seed (only for warm/incremental strategies)
    - Aggregation: MAE, RMSE, MAPE, and directional accuracy are
      computed across all evaluated points of all iterations
    - Not responsible for DB writes; the caller persists results

Algorithm:
    For iteration i in [0, iterations):
        t_i = last_timestamp - (iterations - i) * horizon_step
        train_data = data[ds <= t_i]
        actual_data = data[ds > t_i, ds <= t_i + horizon]

        model = build_model()
        if strategy in ("warm", "incremental") and previous_model_path:
            model.train(train_data, warm_start=True,
                        previous_model_path=previous_model_path)
        else:
            model.train(train_data)

        predictions = model.predict(future_frame(t_i, horizon))
        compare predictions vs actual_data
        save model to temp dir (for next iteration's warm-start)
        record per-iteration MAE/RMSE/MAPE + matched pairs
    Aggregate.
"""

import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.ai.base import ForecastModel
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Strategies that support chaining across iterations
WARM_STRATEGIES = ("warm", "incremental")

# Minimum rows required to train a model in any given iteration
MIN_ITERATION_TRAINING_ROWS = 60


# ============================================================
# RESULT TYPES
# ============================================================
@dataclass
class IterationResult:
    """Result of one walk-forward iteration.

    Attributes:
        iteration: Zero-based index of this iteration.
        train_cutoff: The timestamp up to which training data was used.
        forecast_start: The first forecast timestamp.
        forecast_end: The last forecast timestamp.
        training_rows: Number of rows in the training slice.
        forecast_points: Number of forecast points produced.
        matched_points: Number of points with both prediction and actual.
        mae: Mean Absolute Error for this iteration.
        rmse: Root Mean Square Error for this iteration.
        mape: Mean Absolute Percentage Error for this iteration.
        directional_accuracy: Percentage of correct direction predictions.
        matched_data: Raw (forecast_date, predicted_price, actual_price)
            tuples for every matched point in this iteration. Populated
            so the caller can persist per-point rows (T5.2).
        error: If the iteration failed, the error message.
    """

    iteration: int
    train_cutoff: datetime
    forecast_start: datetime
    forecast_end: datetime
    training_rows: int = 0
    forecast_points: int = 0
    matched_points: int = 0
    mae: float = 0.0
    rmse: float = 0.0
    mape: float = 0.0
    directional_accuracy: float = 0.0
    matched_data: List[Tuple[datetime, float, float]] = field(
        default_factory=list
    )
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict.

        Note: `matched_data` is intentionally omitted to keep log
        output small. Callers who need the raw pairs should read
        the attribute directly.
        """
        return {
            "iteration": self.iteration,
            "train_cutoff": self.train_cutoff.isoformat(),
            "forecast_start": self.forecast_start.isoformat(),
            "forecast_end": self.forecast_end.isoformat(),
            "training_rows": self.training_rows,
            "forecast_points": self.forecast_points,
            "matched_points": self.matched_points,
            "mae": self.mae,
            "rmse": self.rmse,
            "mape": self.mape,
            "directional_accuracy": self.directional_accuracy,
            "error": self.error,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        status = "ok" if self.error is None else "failed"
        return (
            f"IterationResult(iteration={self.iteration}, "
            f"status='{status}', "
            f"mae={self.mae:.2f}, "
            f"matched={self.matched_points})"
        )


@dataclass
class BacktestResult:
    """Aggregated result of a walk-forward backtest run.

    Attributes:
        model_name: Name of the model under test.
        horizon: Horizon label ('24h' or '7d').
        horizon_hours: Number of hours per iteration's forecast window.
        iterations: Number of iterations attempted.
        iterations_succeeded: Number of iterations that produced metrics.
        iterations_failed: Number of iterations that failed.
        total_matched_points: Total (prediction, actual) pairs evaluated.
        mae: Aggregate Mean Absolute Error.
        rmse: Aggregate Root Mean Square Error.
        mape: Aggregate Mean Absolute Percentage Error.
        directional_accuracy: Aggregate percentage of correct directions.
        iteration_results: Per-iteration results.
        elapsed_seconds: Wall-clock duration.
        error: If the whole run failed, the error message.
    """

    model_name: str
    horizon: str
    horizon_hours: int
    iterations: int = 0
    iterations_succeeded: int = 0
    iterations_failed: int = 0
    total_matched_points: int = 0
    mae: float = 0.0
    rmse: float = 0.0
    mape: float = 0.0
    directional_accuracy: float = 0.0
    iteration_results: List[IterationResult] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        """Return True if at least one iteration succeeded."""
        return self.iterations_succeeded > 0 and self.error is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dict."""
        return {
            "model_name": self.model_name,
            "horizon": self.horizon,
            "horizon_hours": self.horizon_hours,
            "iterations": self.iterations,
            "iterations_succeeded": self.iterations_succeeded,
            "iterations_failed": self.iterations_failed,
            "total_matched_points": self.total_matched_points,
            "mae": self.mae,
            "rmse": self.rmse,
            "mape": self.mape,
            "directional_accuracy": self.directional_accuracy,
            "elapsed_seconds": self.elapsed_seconds,
            "succeeded": self.succeeded,
            "error": self.error,
            "iteration_results": [r.to_dict() for r in self.iteration_results],
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"BacktestResult(model='{self.model_name}', "
            f"horizon='{self.horizon}', "
            f"iterations={self.iterations_succeeded}/{self.iterations}, "
            f"mae={self.mae:.2f})"
        )


# ============================================================
# BACKTESTER
# ============================================================
class WalkForwardBacktester:
    """Walk-forward backtester for a single model + horizon.

    Each call to `run()` executes N iterations. Each iteration:
        1. Slices training data up to the iteration's cutoff
        2. Trains a fresh model on the slice (or warm-starts)
        3. Predicts the horizon
        4. Compares to actuals
        5. Saves the model to a temp dir for the next iteration

    The engine is not responsible for DB writes. It returns a
    BacktestResult that the caller persists.

    Example:
        bt = WalkForwardBacktester(
            horizon="24h",
            horizon_hours=24,
            iterations=30,
        )
        result = await bt.run(
            model_name="prophet_fresh",
            build_model=lambda: ProphetModel(strategy="fresh"),
            training_data=df,
            actuals=df,
        )
    """

    def __init__(
        self,
        horizon: str,
        horizon_hours: int,
        iterations: Optional[int] = None,
        full_trajectory: Optional[bool] = None,
        model_dir: Optional[str] = None,
    ) -> None:
        """Initialize the backtester.

        Args:
            horizon: Horizon label ('24h' or '7d').
            horizon_hours: Number of hours per forecast window
                (24 for 24h, 168 for 7d).
            iterations: Number of walk-forward iterations. If None,
                uses settings.backtest_iterations.
            full_trajectory: If True, evaluate all forecast points;
                if False, evaluate only the endpoint. If None, uses
                settings.backtest_full_trajectory.
            model_dir: Temp directory for chained models. If None,
                uses settings.backtest_model_dir.

        Raises:
            ValueError: If horizon_hours <= 0 or iterations <= 0.
        """
        if horizon_hours <= 0:
            raise ValueError(
                f"horizon_hours must be positive, got {horizon_hours}"
            )

        iterations = (
            iterations
            if iterations is not None
            else settings.backtest_iterations
        )
        if iterations <= 0:
            raise ValueError(
                f"iterations must be positive, got {iterations}"
            )

        self.horizon = horizon
        self.horizon_hours = horizon_hours
        self.iterations = iterations
        self.full_trajectory = (
            full_trajectory
            if full_trajectory is not None
            else settings.backtest_full_trajectory
        )
        self.model_dir = model_dir or settings.backtest_model_dir

    # ============================================================
    # PUBLIC API
    # ============================================================
    async def run(
        self,
        model_name: str,
        build_model: Callable[[], ForecastModel],
        training_data: pd.DataFrame,
        actuals: Optional[pd.DataFrame] = None,
    ) -> BacktestResult:
        """Execute the walk-forward backtest.

        Args:
            model_name: Name of the model under test
                (e.g. 'prophet_fresh').
            build_model: A zero-arg callable returning a fresh,
                untrained ForecastModel instance.
            training_data: Full history to slice from. Must have
                'ds' and 'y' columns (and regressors if the model
                needs them).
            actuals: Optional separate frame of actuals. If None,
                uses `training_data`.

        Returns:
            BacktestResult with aggregated metrics.
        """
        import time

        start = time.monotonic()
        result = BacktestResult(
            model_name=model_name,
            horizon=self.horizon,
            horizon_hours=self.horizon_hours,
            iterations=self.iterations,
        )

        try:
            # Resolve the actuals frame. We intentionally avoid the
            # `actuals or training_data` pattern because pandas
            # DataFrames raise on bool() coercion — the `or` would
            # trigger "truth value of a DataFrame is ambiguous".
            actuals_frame = (
                actuals if actuals is not None else training_data
            )

            self._validate_inputs(training_data, actuals_frame)

            # Sort + normalize inputs once
            training_data = training_data.sort_values("ds").reset_index(
                drop=True
            )
            actuals_df = actuals_frame.sort_values("ds").reset_index(
                drop=True
            )

            # Determine the timestamp boundaries
            boundaries = self._compute_iteration_boundaries(training_data)

            # Temp dir for chaining warm-start models
            tmp_dir = tempfile.mkdtemp(
                prefix=f"backtest_{model_name}_",
                dir=self._safe_model_dir(),
            )
            logger.info(
                f"Backtest {model_name} ({self.horizon}): "
                f"{len(boundaries)} iterations, temp dir {tmp_dir}"
            )

            try:
                prev_model_path: Optional[str] = None

                for i, (cutoff, f_start, f_end) in enumerate(boundaries):
                    iter_result, prev_model_path = self._run_iteration(
                        iteration=i,
                        model_name=model_name,
                        build_model=build_model,
                        training_data=training_data,
                        actuals=actuals_df,
                        cutoff=cutoff,
                        forecast_start=f_start,
                        forecast_end=f_end,
                        prev_model_path=prev_model_path,
                        tmp_dir=tmp_dir,
                    )
                    result.iteration_results.append(iter_result)

                    if iter_result.error is None:
                        result.iterations_succeeded += 1
                    else:
                        result.iterations_failed += 1

                # Aggregate
                self._aggregate(result)
            finally:
                # Clean up temp dir
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception as e:
                    logger.warning(
                        f"Failed to clean up backtest temp dir "
                        f"'{tmp_dir}': {e}"
                    )

        except Exception as e:
            result.error = str(e)
            logger.error(
                f"Backtest {model_name} ({self.horizon}) failed: {e}",
                exc_info=True,
            )

        result.elapsed_seconds = time.monotonic() - start

        logger.info(
            f"Backtest {model_name} ({self.horizon}) complete: "
            f"{result.iterations_succeeded}/{result.iterations} iterations "
            f"succeeded, MAE={result.mae:.2f}, "
            f"RMSE={result.rmse:.2f}, MAPE={result.mape:.2f}%, "
            f"in {result.elapsed_seconds:.2f}s"
        )

        return result

    # ============================================================
    # INPUT VALIDATION
    # ============================================================
    def _validate_inputs(
        self,
        training_data: pd.DataFrame,
        actuals: pd.DataFrame,
    ) -> None:
        """Validate the input frames.

        Raises:
            ValueError: If inputs are invalid.
        """
        if training_data is None or training_data.empty:
            raise ValueError("training_data is empty")

        if "ds" not in training_data.columns or "y" not in training_data.columns:
            raise ValueError(
                "training_data must have 'ds' and 'y' columns"
            )

        if actuals is None or actuals.empty:
            raise ValueError("actuals is empty")

        if "ds" not in actuals.columns or "y" not in actuals.columns:
            raise ValueError("actuals must have 'ds' and 'y' columns")

        required = self.iterations * self.horizon_hours + MIN_ITERATION_TRAINING_ROWS
        if len(training_data) < required:
            raise ValueError(
                f"training_data has {len(training_data)} rows; "
                f"need at least {required} for "
                f"{self.iterations} iterations of {self.horizon_hours}h"
            )

    # ============================================================
    # BOUNDARY COMPUTATION
    # ============================================================
    def _compute_iteration_boundaries(
        self, data: pd.DataFrame
    ) -> List[tuple]:
        """Compute (cutoff, forecast_start, forecast_end) per iteration.

        Iterations are contiguous and end at the last timestamp in
        the data. Each iteration's cutoff is `iterations - i` steps
        back from the end.

        Args:
            data: Sorted DataFrame with 'ds' column.

        Returns:
            List of (cutoff, forecast_start, forecast_end) tuples,
            each a pandas Timestamp.
        """
        max_ds = pd.to_datetime(data["ds"]).max()
        step = timedelta(hours=self.horizon_hours)

        boundaries = []
        for i in range(self.iterations):
            # Each iteration advances the cutoff back by one step
            steps_from_end = self.iterations - i
            cutoff = max_ds - steps_from_end * step
            f_start = cutoff + timedelta(hours=1)
            f_end = f_start + step - timedelta(hours=1)
            boundaries.append((cutoff, f_start, f_end))

        return boundaries

    # ============================================================
    # SINGLE ITERATION
    # ============================================================
    def _run_iteration(
        self,
        iteration: int,
        model_name: str,
        build_model: Callable[[], ForecastModel],
        training_data: pd.DataFrame,
        actuals: pd.DataFrame,
        cutoff: pd.Timestamp,
        forecast_start: pd.Timestamp,
        forecast_end: pd.Timestamp,
        prev_model_path: Optional[str],
        tmp_dir: str,
    ) -> tuple:
        """Run one walk-forward iteration.

        Returns:
            Tuple of (IterationResult, next_prev_model_path).
        """
        logger.debug(
            f"[{model_name} #{iteration}] cutoff={cutoff}, "
            f"forecast {forecast_start}..{forecast_end}"
        )

        base_result = IterationResult(
            iteration=iteration,
            train_cutoff=cutoff.to_pydatetime(),
            forecast_start=forecast_start.to_pydatetime(),
            forecast_end=forecast_end.to_pydatetime(),
        )

        try:
            # ---- 1. Slice training data ----
            train_slice = training_data[
                pd.to_datetime(training_data["ds"]) <= cutoff
            ].reset_index(drop=True)

            if len(train_slice) < MIN_ITERATION_TRAINING_ROWS:
                raise ValueError(
                    f"Training slice has {len(train_slice)} rows; "
                    f"need at least {MIN_ITERATION_TRAINING_ROWS}"
                )

            base_result.training_rows = len(train_slice)

            # ---- 2. Build + train the model ----
            model = build_model()

            strategy = getattr(model, "strategy", "fresh")
            use_warm = (
                strategy in WARM_STRATEGIES
                and prev_model_path is not None
            )

            if use_warm:
                model.train(
                    train_slice,
                    warm_start=True,
                    previous_model_path=prev_model_path,
                )
            else:
                model.train(train_slice)

            # ---- 3. Build the future frame for prediction ----
            future_frame = self._build_future_frame(
                train_slice, forecast_start, forecast_end
            )

            # ---- 4. Predict ----
            predictions = model.predict(future_frame)

            if predictions is None or predictions.empty:
                raise ValueError("Model returned empty predictions")

            # Trim predictions to the requested window
            predictions = predictions.copy()
            predictions["ds"] = pd.to_datetime(predictions["ds"])
            predictions = predictions[
                (predictions["ds"] >= forecast_start)
                & (predictions["ds"] <= forecast_end)
            ].reset_index(drop=True)

            # Optionally reduce to endpoint
            if not self.full_trajectory:
                predictions = predictions.tail(1).reset_index(drop=True)

            base_result.forecast_points = len(predictions)

            # ---- 5. Match with actuals ----
            actual_slice = actuals[
                (pd.to_datetime(actuals["ds"]) >= forecast_start)
                & (pd.to_datetime(actuals["ds"]) <= forecast_end)
            ].reset_index(drop=True)

            merged = pd.merge(
                predictions[["ds", "yhat"]],
                actual_slice[["ds", "y"]],
                on="ds",
                how="inner",
            )

            if merged.empty:
                raise ValueError(
                    "No overlapping (prediction, actual) timestamps"
                )

            if not self.full_trajectory:
                # For endpoint evaluation, keep only the last matched point
                merged = merged.tail(1).reset_index(drop=True)

            base_result.matched_points = len(merged)

            # ---- 6. Record matched pairs (for per-point persistence) ----
            base_result.matched_data = [
                (
                    row["ds"].to_pydatetime(),
                    float(row["yhat"]),
                    float(row["y"]),
                )
                for _, row in merged.iterrows()
            ]

            # ---- 7. Compute metrics ----
            metrics = self._compute_metrics(
                actual=merged["y"].values,
                predicted=merged["yhat"].values,
            )
            base_result.mae = metrics["mae"]
            base_result.rmse = metrics["rmse"]
            base_result.mape = metrics["mape"]
            base_result.directional_accuracy = metrics["directional_accuracy"]

            # ---- 8. Save this iteration's model for the next one ----
            next_path = self._save_iteration_model(
                model=model,
                iteration=iteration,
                model_name=model_name,
                tmp_dir=tmp_dir,
            )

            return base_result, next_path

        except Exception as e:
            base_result.error = str(e)
            logger.warning(
                f"[{model_name} #{iteration}] iteration failed: {e}"
            )

            logger.debug(
                f"[{model_name} #{iteration}] "
                f"train={len(train_slice)} "
                f"future={len(future_frame)} "
                f"pred={len(predictions)} "
                f"actual={len(actual_slice)} "
                f"matched={len(merged)} "
                f"pred_ds={predictions['ds'].iloc[0] if len(predictions) else None}.."
                f"{predictions['ds'].iloc[-1] if len(predictions) else None} "
                f"actual_ds={actual_slice['ds'].iloc[0] if len(actual_slice) else None}.."
                f"{actual_slice['ds'].iloc[-1] if len(actual_slice) else None}"
            )

            # Carry the previous path forward (chain continues from last good)
            return base_result, prev_model_path

    # ============================================================
    # FUTURE FRAME
    # ============================================================
    def _build_future_frame(
        self,
        train_slice: pd.DataFrame,
        forecast_start: pd.Timestamp,
        forecast_end: pd.Timestamp,
    ) -> pd.DataFrame:
        """Build a future frame for prediction.

        Uses the last known row's regressor values (forward-fill)
        and generates hourly timestamps in the forecast window.

        Args:
            train_slice: Training data slice.
            forecast_start: First forecast timestamp (inclusive).
            forecast_end: Last forecast timestamp (inclusive).

        Returns:
            DataFrame with the same columns as train_slice, with
            'ds' replaced by forecast timestamps.
        """
        future_times = pd.date_range(
            start=forecast_start,
            end=forecast_end,
            freq="h",
        )

        last_row = train_slice.iloc[-1].to_dict()

        rows = []
        for ts in future_times:
            row = dict(last_row)
            row["ds"] = ts
            rows.append(row)

        return pd.DataFrame(rows)

    # ============================================================
    # METRICS
    # ============================================================
    def _compute_metrics(
        self,
        actual: np.ndarray,
        predicted: np.ndarray,
    ) -> Dict[str, float]:
        """Compute MAE, RMSE, MAPE, directional accuracy.

        Args:
            actual: Array of actual values.
            predicted: Array of predicted values.

        Returns:
            Dictionary with mae, rmse, mape, directional_accuracy.
        """
        mae = float(np.mean(np.abs(predicted - actual)))
        rmse = float(np.sqrt(np.mean((predicted - actual) ** 2)))

        with np.errstate(divide="ignore", invalid="ignore"):
            mape_values = np.abs((predicted - actual) / actual) * 100
            mape_values = mape_values[np.isfinite(mape_values)]
            mape = float(np.mean(mape_values)) if len(mape_values) > 0 else 0.0

        # Directional accuracy: fraction of steps where the direction
        # of change matches (only defined if we have >1 point)
        if len(actual) > 1:
            actual_diff = np.diff(actual)
            predicted_diff = np.diff(predicted)
            correct = np.sum(np.sign(actual_diff) == np.sign(predicted_diff))
            directional_accuracy = float(correct / len(actual_diff) * 100)
        else:
            directional_accuracy = 0.0

        return {
            "mae": mae,
            "rmse": rmse,
            "mape": mape,
            "directional_accuracy": directional_accuracy,
        }

    # ============================================================
    # AGGREGATION
    # ============================================================
    def _aggregate(self, result: BacktestResult) -> None:
        """Aggregate per-iteration results into the BacktestResult.

        Metrics are averaged across iterations (weighted by
        matched_points). Directional accuracy is averaged across
        iterations with a simple mean (since it's already a rate).
        """
        successful = [
            r for r in result.iteration_results if r.error is None
        ]
        if not successful:
            result.error = "All iterations failed"
            return

        total_points = sum(r.matched_points for r in successful)
        result.total_matched_points = total_points

        if total_points == 0:
            result.error = "No matched points across all iterations"
            return

        # Weighted average for continuous metrics
        def _weighted(attr: str) -> float:
            numerator = sum(
                getattr(r, attr) * r.matched_points for r in successful
            )
            return float(numerator / total_points)

        result.mae = _weighted("mae")
        result.rmse = _weighted("rmse")
        result.mape = _weighted("mape")

        # Directional accuracy: simple mean across iterations
        result.directional_accuracy = float(
            np.mean([r.directional_accuracy for r in successful])
        )

    # ============================================================
    # MODEL SAVE / TEMP DIR
    # ============================================================
    def _save_iteration_model(
        self,
        model: ForecastModel,
        iteration: int,
        model_name: str,
        tmp_dir: str,
    ) -> Optional[str]:
        """Save the model for the next iteration's warm-start.

        Returns the path on success, None on failure.
        """
        try:
            path = f"{tmp_dir}/{model_name}_iter{iteration}.model"
            model.save(path)
            return path
        except Exception as e:
            logger.warning(
                f"Failed to save iteration {iteration} model: {e}"
            )
            return None

    def _safe_model_dir(self) -> Optional[str]:
        """Return the model dir if it exists, else None (use system tmp).

        We want temp dirs under our own tree when possible, but if
        the directory doesn't exist we fall back to the system tmp
        so tests and CI don't fail on missing directories.
        """
        import os

        if os.path.isdir(self.model_dir):
            return self.model_dir
        try:
            os.makedirs(self.model_dir, exist_ok=True)
            return self.model_dir
        except Exception:
            return None