"""Retraining orchestrator for forecasting models.

This module provides the RetrainingOrchestrator, which handles the
retraining process for all registered forecasting models.

The orchestrator is model-agnostic — it depends only on the
ForecastModel interface and doesn't know how each model trains
internally. This decouples the retraining workflow from
model-specific logic.

The orchestrator is responsible for:
    - Iterating over registered models
    - Calling each model's train() method
    - Saving each model to disk
    - Collecting metrics from all models
    - Logging metrics to MLflow
    - Publishing events for downstream services
    - Isolating errors (one model's failure doesn't stop others)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import pandas as pd

from app.ai.base import ForecastModel

logger = logging.getLogger(__name__)


# ============================================================
# RESULTS
# ============================================================
class RetrainResult:
    """Result of retraining a single model."""

    def __init__(
        self,
        model_name: str,
        status: str,
        metrics: Optional[Dict[str, float]] = None,
        error: Optional[str] = None,
        duration_seconds: Optional[float] = None,
    ) -> None:
        """Initialize a retrain result.

        Args:
            model_name: Name of the model.
            status: Either 'success' or 'failed'.
            metrics: Performance metrics if successful.
            error: Error message if failed.
            duration_seconds: Time taken to retrain.
        """
        self.model_name = model_name
        self.status = status
        self.metrics = metrics or {}
        self.error = error
        self.duration_seconds = duration_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for event publishing."""
        return {
            "model_name": self.model_name,
            "status": self.status,
            "metrics": self.metrics,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"RetrainResult(model_name='{self.model_name}', "
            f"status='{self.status}')"
        )


# ============================================================
# ORCHESTRATOR
# ============================================================
class RetrainingOrchestrator:
    """Orchestrates retraining of all registered forecasting models.

    The orchestrator is decoupled from specific models. It depends
    on the ForecastModel interface only, so any model implementing
    the interface can be registered and retrained.

    Dependencies (all injected via constructor):
        - models: Dictionary of model name → ForecastModel instance
        - mlflow_tracker: Optional MLflow tracker for logging
        - event_publisher: Optional event publisher for events
        - model_save_dir: Directory to save trained models

    Example:
        orchestrator = RetrainingOrchestrator(
            models={
                "prophet_fresh": ProphetModel(),
                "xgboost_fresh": XGBoostModel(),
            },
            model_save_dir="models",
        )
        results = orchestrator.retrain_all(data)
    """

    def __init__(
        self,
        models: Dict[str, ForecastModel],
        mlflow_tracker: Optional[Any] = None,
        event_publisher: Optional[Any] = None,
        model_save_dir: str = "models",
    ) -> None:
        """Initialize the orchestrator.

        Args:
            models: Dictionary mapping model names to ForecastModel instances.
            mlflow_tracker: Optional MLflow tracker for logging metrics.
            event_publisher: Optional event publisher for downstream events.
            model_save_dir: Directory to save trained models.
        """
        if not models:
            raise ValueError("At least one model must be registered")

        self.models = models
        self.mlflow_tracker = mlflow_tracker
        self.event_publisher = event_publisher
        self.model_save_dir = model_save_dir

        # Tracking
        self.last_retrain_time: Optional[datetime] = None
        self.retrain_history: list[Dict[str, Any]] = []

        logger.info(
            f"RetrainingOrchestrator initialized with {len(models)} models: "
            f"{list(models.keys())}"
        )

    # ============================================================
    # PUBLIC API
    # ============================================================
    def retrain_all(
        self,
        data: pd.DataFrame,
        warm_start: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """Retrain all registered models.

        Each model is retrained independently. If one model fails,
        the remaining models continue training.

        Args:
            data: Training data (DataFrame with ds, y, regressors).
            warm_start: If True, uses previous model state for training
                (only for models that support it).

        Returns:
            Dictionary mapping model name → result dict
            (including status, metrics, error, duration).
        """
        if data is None or data.empty:
            raise ValueError("Training data cannot be empty")

        logger.info(
            f"Starting retraining for {len(self.models)} models "
            f"(warm_start={warm_start})"
        )

        results: Dict[str, Dict[str, Any]] = {}
        start_time = datetime.now(timezone.utc)

        for model_name, model in self.models.items():
            result = self._retrain_single(
                model_name=model_name,
                model=model,
                data=data,
                warm_start=warm_start,
            )
            results[model_name] = result.to_dict()

        # Update tracking
        self.last_retrain_time = datetime.now(timezone.utc)

        # Publish event
        self._publish_retrained_event(results, start_time)

        # Log to history
        self.retrain_history.append(
            {
                "timestamp": start_time.isoformat(),
                "duration_seconds": (
                    self.last_retrain_time - start_time
                ).total_seconds(),
                "results": results,
            }
        )

        success_count = sum(
            1 for r in results.values() if r["status"] == "success"
        )
        failed_count = len(results) - success_count

        logger.info(
            f"Retraining complete: {success_count} succeeded, "
            f"{failed_count} failed"
        )

        return results

    def retrain_model(
        self,
        model_name: str,
        data: pd.DataFrame,
        warm_start: bool = False,
    ) -> Dict[str, Any]:
        """Retrain a specific model by name.

        Args:
            model_name: Name of the model to retrain.
            data: Training data (DataFrame with ds, y, regressors).
            warm_start: If True, uses previous model state.

        Returns:
            Result dictionary (status, metrics, error, duration).

        Raises:
            KeyError: If model_name is not registered.
        """
        if model_name not in self.models:
            raise KeyError(
                f"Model '{model_name}' is not registered. "
                f"Available models: {list(self.models.keys())}"
            )

        if data is None or data.empty:
            raise ValueError("Training data cannot be empty")

        logger.info(f"Retraining single model: {model_name}")

        model = self.models[model_name]
        result = self._retrain_single(
            model_name=model_name,
            model=model,
            data=data,
            warm_start=warm_start,
        )

        return result.to_dict()

    def get_last_retrain_time(self) -> Optional[datetime]:
        """Return the timestamp of the last retrain."""
        return self.last_retrain_time

    def get_retrain_history(self) -> list[Dict[str, Any]]:
        """Return the retraining history."""
        return self.retrain_history.copy()

    def get_registered_models(self) -> list[str]:
        """Return the list of registered model names."""
        return list(self.models.keys())

    def register_model(
        self, model_name: str, model: ForecastModel
    ) -> None:
        """Register a new model with the orchestrator.

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
        """Unregister a model from the orchestrator.

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
    # INTERNAL HELPERS
    # ============================================================
    def _retrain_single(
        self,
        model_name: str,
        model: ForecastModel,
        data: pd.DataFrame,
        warm_start: bool,
    ) -> RetrainResult:
        """Retrain a single model with error handling.

        Args:
            model_name: Name of the model.
            model: ForecastModel instance.
            data: Training data.
            warm_start: If True, uses previous model state.

        Returns:
            RetrainResult with status, metrics, and duration.
        """
        logger.info(f"Retraining model: {model_name}")
        start = datetime.now(timezone.utc)

        try:
            # Determine previous model path (for warm_start)
            previous_model_path = None
            if warm_start:
                previous_model_path = (
                    f"{self.model_save_dir}/{model_name}.pkl"
                )

            # Train the model
            metrics = model.train(
                data=data,
                warm_start=warm_start,
                previous_model_path=previous_model_path,
            )

            # Save the trained model
            save_path = f"{self.model_save_dir}/{model_name}.pkl"
            model.save(save_path)

            # Log to MLflow (if tracker available)
            self._log_to_mlflow(model_name, metrics)

            duration = (
                datetime.now(timezone.utc) - start
            ).total_seconds()

            logger.info(
                f"Model '{model_name}' retrained successfully "
                f"in {duration:.2f}s"
            )

            return RetrainResult(
                model_name=model_name,
                status="success",
                metrics=metrics,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = (
                datetime.now(timezone.utc) - start
            ).total_seconds()

            logger.error(
                f"Model '{model_name}' failed to retrain "
                f"after {duration:.2f}s: {e}",
                exc_info=True,
            )

            return RetrainResult(
                model_name=model_name,
                status="failed",
                error=str(e),
                duration_seconds=duration,
            )

    def _log_to_mlflow(
        self, model_name: str, metrics: Dict[str, float]
    ) -> None:
        """Log metrics to MLflow (if tracker is available).

        Args:
            model_name: Name of the model.
            metrics: Performance metrics to log.
        """
        if self.mlflow_tracker is None:
            logger.debug(
                f"MLflow tracker not configured, skipping log for "
                f"'{model_name}'"
            )
            return

        try:
            self.mlflow_tracker.log_metrics(model_name, metrics)
            logger.debug(f"Logged metrics to MLflow for '{model_name}'")
        except Exception as e:
            logger.warning(
                f"Failed to log metrics to MLflow for '{model_name}': {e}"
            )

    def _publish_retrained_event(
        self,
        results: Dict[str, Dict[str, Any]],
        start_time: datetime,
    ) -> None:
        """Publish a ModelsRetrained event (if publisher available).

        Args:
            results: Results dictionary from retrain_all().
            start_time: When the retraining started.
        """
        if self.event_publisher is None:
            logger.debug(
                "Event publisher not configured, skipping event"
            )
            return

        try:
            event = {
                "event_type": "ModelsRetrained",
                "event_version": "1.0",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "ai-service",
                "data": {
                    "started_at": start_time.isoformat(),
                    "completed_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                    "models": results,
                },
            }

            self.event_publisher.publish(event)
            logger.debug("ModelsRetrained event published")

        except Exception as e:
            logger.warning(
                f"Failed to publish ModelsRetrained event: {e}"
            )

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"RetrainingOrchestrator("
            f"models={list(self.models.keys())}, "
            f"last_retrain={self.last_retrain_time})"
        )