"""Model comparison engine for forecasting models.

This module provides the ModelComparisonEngine, which runs multiple
forecasting models against the same future data, collects their
predictions, and produces a structured comparison.

The engine is model-agnostic and N-model aware:
    - It depends only on the ForecastModel interface
    - It works with any number of registered models (3, 6, or more)
    - It isolates errors per model (one failure does not stop others)
    - It supports both sequential and parallel execution modes

The engine is responsible for:
    - Running each registered model's predict() method
    - Collecting predictions from all models
    - Calculating an agreement score across models
    - Identifying the best model based on historical MAE
    - Producing a consensus (average) prediction
    - Tracking per-model execution time
    - Isolating failures per model

The module also provides build_default_engine(), a convenience
factory that registers all 6 model variants shipped with the AI
Service (Prophet fresh/warm, XGBoost fresh/incremental,
LightGBM fresh/incremental).
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from app.ai.base import ForecastModel

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================
# Agreement score bounds
AGREEMENT_SCORE_MIN = 0.0
AGREEMENT_SCORE_MAX = 1.0

# Clamp helper bounds
_CLAMP_LOW = 0.0
_CLAMP_HIGH = 1.0

# Default model variant keys registered by build_default_engine()
DEFAULT_MODEL_KEYS = (
    "prophet_fresh",
    "prophet_warm",
    "xgboost_fresh",
    "xgboost_incremental",
    "lightgbm_fresh",
    "lightgbm_incremental",
)


# ============================================================
# RESULT TYPES
# ============================================================
@dataclass
class ModelPrediction:
    """Result of running a single model.

    Attributes:
        model_name: Name of the model (e.g., 'prophet_fresh').
        predictions: DataFrame with ds, yhat, yhat_lower, yhat_upper.
            None if the model failed.
        metrics: The model's training metrics (mae, rmse, mape, ...).
            Empty dict if the model has no metrics.
        elapsed_seconds: Wall-clock time taken to run this model.
        error: Error message if the model failed, else None.
    """

    model_name: str
    predictions: Optional[pd.DataFrame]
    metrics: Dict[str, float] = field(default_factory=dict)
    elapsed_seconds: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict for event publishing and API responses.

        Returns:
            Dictionary with model_name, metrics, elapsed_seconds,
            error, and (if present) the predictions DataFrame
            converted to a list of dicts.
        """
        return {
            "model_name": self.model_name,
            "predictions": (
                self.predictions.to_dict(orient="records")
                if self.predictions is not None
                else None
            ),
            "metrics": self.metrics,
            "elapsed_seconds": self.elapsed_seconds,
            "error": self.error,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        status = "failed" if self.error else "success"
        return (
            f"ModelPrediction(model_name='{self.model_name}', "
            f"status='{status}', "
            f"elapsed={self.elapsed_seconds:.3f}s)"
        )


@dataclass
class ComparisonResult:
    """Result of running and comparing all models.

    Attributes:
        predictions: Mapping of model_name → ModelPrediction.
        consensus: DataFrame with mean yhat (and mean bounds) across
            all successful models. None if no model succeeded.
        agreement_score: A score in [0, 1] measuring how closely
            the models agree. 1.0 = perfect agreement.
        best_model: Name of the model with the lowest historical MAE.
            None if no model has metrics.
        models_run: Names of models that succeeded.
        models_failed: Names of models that failed.
        total_elapsed_seconds: Total wall-clock time.
    """

    predictions: Dict[str, ModelPrediction] = field(default_factory=dict)
    consensus: Optional[pd.DataFrame] = None
    agreement_score: float = 0.0
    best_model: Optional[str] = None
    models_run: List[str] = field(default_factory=list)
    models_failed: List[str] = field(default_factory=list)
    total_elapsed_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dict for event publishing and API responses.

        Returns:
            Dictionary with all fields serialized. DataFrames are
            converted to lists of records.
        """
        return {
            "predictions": {
                name: pred.to_dict()
                for name, pred in self.predictions.items()
            },
            "consensus": (
                self.consensus.to_dict(orient="records")
                if self.consensus is not None
                else None
            ),
            "agreement_score": self.agreement_score,
            "best_model": self.best_model,
            "models_run": self.models_run,
            "models_failed": self.models_failed,
            "total_elapsed_seconds": self.total_elapsed_seconds,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ComparisonResult("
            f"models_run={len(self.models_run)}, "
            f"models_failed={len(self.models_failed)}, "
            f"agreement={self.agreement_score:.3f}, "
            f"best='{self.best_model}')"
        )


# ============================================================
# COMPARISON ENGINE
# ============================================================
class ModelComparisonEngine:
    """Runs multiple forecasting models and compares their predictions.

    The engine is N-model agnostic. It depends only on the
    ForecastModel interface, so any model implementing the interface
    can be registered and compared.

    Execution modes:
        - sequential (default): Runs models one after another, timing each.
          Simpler, deterministic, easier to test.
        - parallel: Runs models concurrently using ThreadPoolExecutor.
          Faster when models are CPU-heavy and release the GIL.

    Dependencies (all injected via constructor):
        - models: Dictionary of model name → ForecastModel instance
        - parallel: Whether to run models concurrently (default False)
        - max_workers: Max threads for parallel mode (default = #models)

    Example:
        # Compare a custom subset of 3 models
        engine = ModelComparisonEngine(
            models={
                "prophet_fresh": ProphetModel(strategy="fresh"),
                "xgboost_fresh": XGBoostModel(strategy="fresh"),
                "lightgbm_fresh": LightGBMModel(strategy="fresh"),
            },
        )
        result = engine.compare(future_data)

        # Compare all 6 default variants
        engine = build_default_engine()
        result = engine.compare(future_data)
    """

    def __init__(
        self,
        models: Dict[str, ForecastModel],
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ) -> None:
        """Initialize the comparison engine.

        Args:
            models: Dictionary mapping model names to ForecastModel
                instances. Must contain at least one model.
            parallel: If True, run models concurrently using a
                ThreadPoolExecutor. If False (default), run
                sequentially with per-model timing.
            max_workers: Maximum number of worker threads for parallel
                mode. Ignored when parallel=False. Defaults to the
                number of registered models.

        Raises:
            ValueError: If models is empty.
        """
        if not models:
            raise ValueError("At least one model must be registered")

        self.models = models
        self.parallel = parallel
        self.max_workers = max_workers or len(models)

        # Tracking
        self.last_comparison_time: Optional[datetime] = None

        logger.info(
            f"ModelComparisonEngine initialized with {len(models)} models: "
            f"{list(models.keys())} (parallel={parallel})"
        )

    # ============================================================
    # PUBLIC API
    # ============================================================
    def compare(self, future_data: pd.DataFrame) -> ComparisonResult:
        """Run all registered models and produce a comparison.

        Each model is run independently. If one model fails, the
        remaining models continue, and the failure is captured in
        the result's models_failed list.

        Args:
            future_data: DataFrame with 'ds', base features, and
                (optionally) 'y' for lag features.

        Returns:
            ComparisonResult with per-model predictions, consensus,
            agreement score, best model, and timing info.

        Raises:
            ValueError: If future_data is None or empty.
        """
        if future_data is None or future_data.empty:
            raise ValueError("future_data cannot be empty")

        logger.info(
            f"Starting comparison of {len(self.models)} models "
            f"(parallel={self.parallel})"
        )

        start_time = datetime.now(timezone.utc)

        # Run all models (sequential or parallel)
        if self.parallel:
            model_predictions = self._run_parallel(future_data)
        else:
            model_predictions = self._run_sequential(future_data)

        # Separate successes from failures
        successful = {
            name: pred
            for name, pred in model_predictions.items()
            if pred.error is None and pred.predictions is not None
        }
        failed = {
            name: pred
            for name, pred in model_predictions.items()
            if pred.error is not None or pred.predictions is None
        }

        # Build consensus from successful models
        consensus = self._build_consensus(successful)

        # Calculate agreement score
        agreement_score = self._calculate_agreement(successful)

        # Identify best model by historical MAE
        best_model = self._identify_best_model(successful)

        # Wrap up
        self.last_comparison_time = datetime.now(timezone.utc)
        total_elapsed = (
            self.last_comparison_time - start_time
        ).total_seconds()

        result = ComparisonResult(
            predictions=model_predictions,
            consensus=consensus,
            agreement_score=agreement_score,
            best_model=best_model,
            models_run=list(successful.keys()),
            models_failed=list(failed.keys()),
            total_elapsed_seconds=total_elapsed,
        )

        logger.info(
            f"Comparison complete: {len(successful)} succeeded, "
            f"{len(failed)} failed, agreement={agreement_score:.3f}, "
            f"best='{best_model}', total={total_elapsed:.2f}s"
        )

        return result

    def get_registered_models(self) -> List[str]:
        """Return the list of registered model names."""
        return list(self.models.keys())

    def register_model(self, model_name: str, model: ForecastModel) -> None:
        """Register a new model with the engine.

        Args:
            model_name: Name to register the model under.
            model: ForecastModel instance.

        Raises:
            ValueError: If model_name is already registered.
        """
        if model_name in self.models:
            raise ValueError(f"Model '{model_name}' is already registered")

        self.models[model_name] = model
        logger.info(f"Model '{model_name}' registered")

    def unregister_model(self, model_name: str) -> None:
        """Unregister a model from the engine.

        Args:
            model_name: Name of the model to unregister.

        Raises:
            KeyError: If model_name is not registered.
        """
        if model_name not in self.models:
            raise KeyError(f"Model '{model_name}' is not registered")

        del self.models[model_name]
        logger.info(f"Model '{model_name}' unregistered")

    # ============================================================
    # EXECUTION MODES
    # ============================================================
    def _run_sequential(
        self, future_data: pd.DataFrame
    ) -> Dict[str, ModelPrediction]:
        """Run models sequentially, timing each one.

        Args:
            future_data: DataFrame to predict on.

        Returns:
            Mapping of model_name → ModelPrediction.
        """
        results: Dict[str, ModelPrediction] = {}
        for model_name, model in self.models.items():
            results[model_name] = self._run_single_model(
                model_name, model, future_data
            )
        return results

    def _run_parallel(
        self, future_data: pd.DataFrame
    ) -> Dict[str, ModelPrediction]:
        """Run models concurrently using a ThreadPoolExecutor.

        Args:
            future_data: DataFrame to predict on.

        Returns:
            Mapping of model_name → ModelPrediction.
        """
        results: Dict[str, ModelPrediction] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._run_single_model, name, model, future_data
                ): name
                for name, model in self.models.items()
            }

            for future in as_completed(futures):
                model_name = futures[future]
                try:
                    results[model_name] = future.result()
                except Exception as e:
                    # Defensive: _run_single_model catches its own errors,
                    # so this branch is only reachable if the executor
                    # itself misbehaves. Still handle it gracefully.
                    logger.error(
                        f"Unexpected error running '{model_name}' "
                        f"in parallel: {e}",
                        exc_info=True,
                    )
                    results[model_name] = ModelPrediction(
                        model_name=model_name,
                        predictions=None,
                        error=f"Unexpected error: {e}",
                    )

        return results

    def _run_single_model(
        self,
        model_name: str,
        model: ForecastModel,
        future_data: pd.DataFrame,
    ) -> ModelPrediction:
        """Run a single model's predict() with error isolation.

        Args:
            model_name: Name of the model.
            model: ForecastModel instance.
            future_data: DataFrame to predict on.

        Returns:
            ModelPrediction with predictions, metrics, timing, or error.
        """
        start = datetime.now(timezone.utc)

        try:
            # Check if model is trained
            if not model.is_model_trained():
                raise RuntimeError(
                    f"Model '{model_name}' is not trained"
                )

            predictions = model.predict(future_data)
            elapsed = (
                datetime.now(timezone.utc) - start
            ).total_seconds()

            metrics = model.get_metrics()

            logger.debug(
                f"Model '{model_name}' predicted {len(predictions)} rows "
                f"in {elapsed:.3f}s"
            )

            return ModelPrediction(
                model_name=model_name,
                predictions=predictions,
                metrics=metrics,
                elapsed_seconds=elapsed,
                error=None,
            )

        except Exception as e:
            elapsed = (
                datetime.now(timezone.utc) - start
            ).total_seconds()

            logger.warning(
                f"Model '{model_name}' failed after {elapsed:.3f}s: {e}"
            )

            return ModelPrediction(
                model_name=model_name,
                predictions=None,
                metrics={},
                elapsed_seconds=elapsed,
                error=str(e),
            )

    # ============================================================
    # CONSENSUS
    # ============================================================
    def _build_consensus(
        self,
        successful: Dict[str, ModelPrediction],
    ) -> Optional[pd.DataFrame]:
        """Build a consensus (mean) prediction across successful models.

        The consensus is the arithmetic mean of each model's yhat at
        each timestamp. Bounds are the mean of each model's
        yhat_lower and yhat_upper.

        Args:
            successful: Mapping of successful model_name → ModelPrediction.

        Returns:
            DataFrame with ds, yhat, yhat_lower, yhat_upper.
            None if no successful models.
        """
        if not successful:
            return None

        # Collect all prediction DataFrames
        frames = []
        for pred in successful.values():
            if pred.predictions is not None:
                frames.append(pred.predictions[["ds", "yhat"]])

        if not frames:
            return None

        # Align by ds and compute mean
        merged = frames[0].rename(columns={"yhat": "yhat_0"})
        for i, frame in enumerate(frames[1:], start=1):
            renamed = frame.rename(columns={"yhat": f"yhat_{i}"})
            merged = merged.merge(renamed, on="ds", how="inner")

        yhat_cols = [c for c in merged.columns if c.startswith("yhat_")]
        consensus = pd.DataFrame(
            {
                "ds": merged["ds"],
                "yhat": merged[yhat_cols].mean(axis=1),
            }
        )

        # Compute mean bounds from models that provided them
        lower_frames = []
        upper_frames = []
        for pred in successful.values():
            if pred.predictions is not None:
                if "yhat_lower" in pred.predictions.columns:
                    lower_frames.append(
                        pred.predictions[["ds", "yhat_lower"]]
                    )
                if "yhat_upper" in pred.predictions.columns:
                    upper_frames.append(
                        pred.predictions[["ds", "yhat_upper"]]
                    )

        if lower_frames:
            merged_lower = lower_frames[0].rename(
                columns={"yhat_lower": "lower_0"}
            )
            for i, frame in enumerate(lower_frames[1:], start=1):
                renamed = frame.rename(
                    columns={"yhat_lower": f"lower_{i}"}
                )
                merged_lower = merged_lower.merge(
                    renamed, on="ds", how="inner"
                )
            lower_cols = [
                c for c in merged_lower.columns if c.startswith("lower_")
            ]
            consensus = consensus.merge(
                pd.DataFrame(
                    {
                        "ds": merged_lower["ds"],
                        "yhat_lower": merged_lower[lower_cols].mean(axis=1),
                    }
                ),
                on="ds",
                how="left",
            )

        if upper_frames:
            merged_upper = upper_frames[0].rename(
                columns={"yhat_upper": "upper_0"}
            )
            for i, frame in enumerate(upper_frames[1:], start=1):
                renamed = frame.rename(
                    columns={"yhat_upper": f"upper_{i}"}
                )
                merged_upper = merged_upper.merge(
                    renamed, on="ds", how="inner"
                )
            upper_cols = [
                c for c in merged_upper.columns if c.startswith("upper_")
            ]
            consensus = consensus.merge(
                pd.DataFrame(
                    {
                        "ds": merged_upper["ds"],
                        "yhat_upper": merged_upper[upper_cols].mean(axis=1),
                    }
                ),
                on="ds",
                how="left",
            )

        return consensus

    # ============================================================
    # AGREEMENT SCORE
    # ============================================================
    def _calculate_agreement(
        self,
        successful: Dict[str, ModelPrediction],
    ) -> float:
        """Calculate the agreement score across successful models.

        The agreement score uses the coefficient of variation:
            agreement = 1 - (std(yhats) / mean(yhats))

        It is clamped to [0, 1]. A score of 1.0 means all models
        predict exactly the same value at every timestamp. A score
        of 0.0 means the spread equals or exceeds the mean.

        If fewer than 2 models succeed, returns 1.0 (a single model
        trivially agrees with itself).

        Args:
            successful: Mapping of successful model_name → ModelPrediction.

        Returns:
            Agreement score in [0, 1].
        """
        if len(successful) < 2:
            return 1.0

        # Collect yhat arrays, aligned by ds
        frames = []
        for pred in successful.values():
            if pred.predictions is not None:
                frames.append(pred.predictions[["ds", "yhat"]])

        if len(frames) < 2:
            return 1.0

        # Align by ds
        merged = frames[0].rename(columns={"yhat": "yhat_0"})
        for i, frame in enumerate(frames[1:], start=1):
            renamed = frame.rename(columns={"yhat": f"yhat_{i}"})
            merged = merged.merge(renamed, on="ds", how="inner")

        yhat_cols = [c for c in merged.columns if c.startswith("yhat_")]
        if len(merged) == 0:
            return 1.0

        # Mean across models at each timestamp
        means_per_timestamp = merged[yhat_cols].mean(axis=1)
        stds_per_timestamp = merged[yhat_cols].std(axis=1)

        # Avoid division by zero
        safe_means = means_per_timestamp.replace(0, np.nan)
        cvs = stds_per_timestamp / safe_means
        cvs = cvs.dropna()

        if len(cvs) == 0:
            return 1.0

        mean_cv = float(cvs.mean())
        agreement = 1.0 - mean_cv

        return float(np.clip(agreement, _CLAMP_LOW, _CLAMP_HIGH))

    # ============================================================
    # BEST MODEL
    # ============================================================
    def _identify_best_model(
        self,
        successful: Dict[str, ModelPrediction],
    ) -> Optional[str]:
        """Identify the best model by historical MAE.

        Reads the 'mae' key from each model's metrics dict. Lower is
        better. Models without a 'mae' metric are skipped.

        Args:
            successful: Mapping of successful model_name → ModelPrediction.

        Returns:
            Name of the model with the lowest MAE, or None if no
            model has an MAE metric.
        """
        candidates: List[tuple] = []
        for name, pred in successful.items():
            mae = pred.metrics.get("mae")
            if mae is not None and np.isfinite(mae):
                candidates.append((name, float(mae)))

        if not candidates:
            return None

        best_name, _ = min(candidates, key=lambda x: x[1])
        return best_name

    # ============================================================
    # DUNDER METHODS
    # ============================================================
    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"ModelComparisonEngine("
            f"models={list(self.models.keys())}, "
            f"parallel={self.parallel}, "
            f"last_comparison={self.last_comparison_time})"
        )


# ============================================================
# FACTORY
# ============================================================
def build_default_engine(
    parallel: bool = False,
    max_workers: Optional[int] = None,
) -> ModelComparisonEngine:
    """Build a ModelComparisonEngine with all 6 default model variants.

    Registers the 6 model variants shipped with the AI Service:
        1. prophet_fresh        — Prophet, fresh strategy
        2. prophet_warm         — Prophet, warm-start strategy
        3. xgboost_fresh        — XGBoost, fresh strategy
        4. xgboost_incremental  — XGBoost, incremental strategy
        5. lightgbm_fresh       — LightGBM, fresh strategy
        6. lightgbm_incremental — LightGBM, incremental strategy

    Callers who want a subset can either construct ModelComparisonEngine
    directly with a custom dict, or filter the engine's models dict
    after construction.

    Note: models are registered but NOT trained. The caller is
    responsible for training them (e.g., via RetrainingOrchestrator)
    before calling engine.compare().

    Args:
        parallel: Whether to run models concurrently.
        max_workers: Max threads for parallel mode.

    Returns:
        ModelComparisonEngine configured with all 6 default variants.
    """
    # Import here to avoid circular imports at module load time
    from app.ai.models import (
        LightGBMModel,
        ProphetModel,
        XGBoostModel,
    )

    models: Dict[str, ForecastModel] = {
        "prophet_fresh": ProphetModel(strategy="fresh"),
        "prophet_warm": ProphetModel(strategy="warm"),
        "xgboost_fresh": XGBoostModel(strategy="fresh"),
        "xgboost_incremental": XGBoostModel(strategy="incremental"),
        "lightgbm_fresh": LightGBMModel(strategy="fresh"),
        "lightgbm_incremental": LightGBMModel(strategy="incremental"),
    }

    logger.info(
        f"Building default ModelComparisonEngine with {len(models)} "
        f"model variants: {list(models.keys())}"
    )

    return ModelComparisonEngine(
        models=models,
        parallel=parallel,
        max_workers=max_workers,
    )