"""Job definitions for the AI Service scheduler.

Each job is a self-contained async function that:
    - Performs its work in a fresh database session
    - Returns a structured result dict (or raises on failure)
    - Never assumes anything about the scheduler that invokes it

Jobs currently registered:
    - daily_retrain_job: retrain all 6 models (6:00 AM UTC)
    - hourly_prediction_job: generate 24h BTC predictions once per hour
    - daily_7d_prediction_job: generate 7d BTC predictions (6:30 AM UTC)

Design:
    - Each job opens its own DB session via session_scope(); the
      scheduler does not manage sessions
    - Jobs raise on failure so the SchedulerManager can record the
      failure, apply retries, and update job state. The manager wraps
      every invocation.
    - Job functions are pure async callables with no scheduler
      dependencies — easy to unit test directly
"""

import logging
from typing import Any, Dict

from app.ai.comparison import build_default_engine
from app.ai.models import (
    LightGBMModel,
    ProphetModel,
    XGBoostModel,
)
from app.ai.orchestrator import RetrainingOrchestrator
from app.config import settings
from app.database.engine import session_scope
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.prediction.generator import PredictionGenerator

logger = logging.getLogger(__name__)


# ============================================================
# JOB NAME CONSTANTS
# ============================================================
JOB_DAILY_RETRAIN = "daily_retrain"
JOB_HOURLY_PREDICTION = "hourly_prediction"
JOB_DAILY_7D_PREDICTION = "daily_7d_prediction"


# ============================================================
# MODEL REGISTRY
# ============================================================
def _build_model_registry() -> Dict[str, Any]:
    """Build the dictionary of models to retrain daily.

    Registers all 6 model variants shipped with the AI Service:
        1. prophet_fresh       — Prophet, fresh
        2. prophet_warm        — Prophet, warm-start
        3. xgboost_fresh       — XGBoost, fresh
        4. xgboost_incremental — XGBoost, incremental
        5. lightgbm_fresh      — LightGBM, fresh
        6. lightgbm_incremental — LightGBM, incremental

    The registry is built fresh on each call so the orchestrator
    works with a clean set of untrained instances.

    Returns:
        Dictionary mapping model name → ForecastModel instance.
    """
    return {
        "prophet_fresh": ProphetModel(strategy="fresh"),
        "prophet_warm": ProphetModel(strategy="warm"),
        "xgboost_fresh": XGBoostModel(strategy="fresh"),
        "xgboost_incremental": XGBoostModel(strategy="incremental"),
        "lightgbm_fresh": LightGBMModel(strategy="fresh"),
        "lightgbm_incremental": LightGBMModel(strategy="incremental"),
    }


# ============================================================
# DAILY RETRAIN JOB
# ============================================================
async def daily_retrain_job() -> Dict[str, Any]:
    """Retrain all 6 models on the latest historical data.

    Runs daily at 6:00 AM UTC. Steps:
        1. Open a DB session and fetch 90 days of training data.
        2. Build a fresh model registry (all 6 variants).
        3. Run the RetrainingOrchestrator.
        4. Return a structured result.

    The job raises on failure so the SchedulerManager records the
    failure, applies retries, and updates job state. If the whole
    job fails, the previously saved models remain on disk — the
    next 6:30 AM prediction job (T2.2) continues to use them.

    Returns:
        Dict with keys: models_retrained (int),
        models_succeeded (int), models_failed (int),
        results (per-model dict), elapsed_seconds.

    Raises:
        RuntimeError: If training data cannot be fetched or is
            insufficient.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_retrain_job")

    # ---- 1. Fetch training data ----
    # 90 days of history (2160 hours) — enough for weekly seasonality
    # and tree-model lag features.
    history_hours = 2160

    async with session_scope() as session:
        repository = PredictionRepository(session)
        training_frame = await repository.fetch_training_frame(
            hours=history_hours
        )

    if training_frame is None or training_frame.empty:
        raise RuntimeError(
            "Cannot retrain: training data is empty or unavailable"
        )

    if len(training_frame) < 60:
        raise RuntimeError(
            f"Cannot retrain: insufficient training data "
            f"({len(training_frame)} rows, need at least 60)"
        )

    logger.info(
        f"Fetched {len(training_frame)} rows of training data "
        f"({history_hours}h)"
    )

    # ---- 2. Build the registry and orchestrator ----
    models = _build_model_registry()
    model_save_dir = settings.model_save_dir

    orchestrator = RetrainingOrchestrator(
        models=models,
        model_save_dir=model_save_dir,
    )

    # ---- 3. Retrain all models ----
    results = orchestrator.retrain_all(data=training_frame)

    # ---- 4. Summarize ----
    succeeded = sum(
        1 for r in results.values() if r["status"] == "success"
    )
    failed = len(results) - succeeded
    elapsed = time.monotonic() - start

    summary = {
        "models_retrained": len(results),
        "models_succeeded": succeeded,
        "models_failed": failed,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_retrain_job complete: "
        f"{succeeded}/{len(results)} models succeeded "
        f"in {elapsed:.3f}s"
    )

    if failed > 0:
        # Surface partial failures so the manager can retry
        failed_names = [
            name
            for name, r in results.items()
            if r["status"] != "success"
        ]
        raise RuntimeError(
            f"{failed} model(s) failed to retrain: {failed_names}"
        )

    return summary


# ============================================================
# HOURLY 24H PREDICTION JOB
# ============================================================
async def hourly_prediction_job() -> Dict[str, Any]:
    """Generate 24h BTC predictions for the current hour.

    Steps:
        1. Load the trained Prophet model from disk.
        2. Open a DB session.
        3. Build a PredictionGenerator (24h horizon, 0.85 confidence).
        4. Run generate().
        5. Return a structured result.

    The job does NOT catch its own exceptions — it raises so the
    SchedulerManager can record the failure, apply retries, and
    update job state. This keeps the job function focused on the
    work itself.

    Returns:
        Dict with keys: horizon, model_name, rows_generated,
        rows_saved, elapsed_seconds, prediction_time, succeeded.

    Raises:
        FileNotFoundError: If the trained model is missing.
        RuntimeError: If generation fails for any other reason.
    """
    logger.info("Running hourly_prediction_job")

    # ---- 1. Load the trained model ----
    model_path = settings.prophet_24h_model_path
    logger.debug(f"Loading Prophet model from '{model_path}'")

    model = ProphetModel(strategy="fresh")
    model.load(model_path)

    if not model.is_model_trained():
        raise RuntimeError(
            f"Loaded model from '{model_path}' is not marked as trained"
        )

    # ---- 2. Run generation in a fresh session ----
    async with session_scope() as session:
        repository = PredictionRepository(session)

        generator = PredictionGenerator(
            model=model,
            repository=repository,
            horizon="24h",
            horizon_hours=24,
            confidence=0.85,
        )

        result = await generator.generate()

    # ---- 3. Evaluate the outcome ----
    if not result.succeeded:
        raise RuntimeError(
            f"Prediction generation failed: {result.error}"
        )

    summary = {
        "horizon": result.horizon,
        "model_name": result.model_name,
        "prediction_time": result.prediction_time.isoformat(),
        "rows_generated": result.rows_generated,
        "rows_saved": result.rows_saved,
        "elapsed_seconds": result.elapsed_seconds,
        "succeeded": result.succeeded,
    }

    logger.info(
        f"hourly_prediction_job completed: "
        f"{result.rows_saved} rows saved in {result.elapsed_seconds:.3f}s"
    )

    return summary


# ============================================================
# DAILY 7D PREDICTION JOB
# ============================================================
async def daily_7d_prediction_job() -> Dict[str, Any]:
    """Generate 7d BTC predictions once per day.

    Runs daily at 6:30 AM UTC, shortly after the daily retrain
    (6:00 AM UTC) so the 7d forecast always uses a fresh model.

    Steps:
        1. Load the trained 7d Prophet model from disk.
        2. Open a DB session.
        3. Build a PredictionGenerator (7d horizon, 0.85 confidence).
        4. Run generate().
        5. Return a structured result.

    The job raises on failure so the SchedulerManager records the
    failure and applies retries.

    Returns:
        Dict with keys: horizon, model_name, rows_generated,
        rows_saved, elapsed_seconds, prediction_time, succeeded.

    Raises:
        FileNotFoundError: If the trained model is missing.
        RuntimeError: If generation fails for any other reason.
    """
    logger.info("Running daily_7d_prediction_job")

    # ---- 1. Load the trained model ----
    model_path = settings.prophet_7d_model_path
    logger.debug(f"Loading Prophet model from '{model_path}'")

    model = ProphetModel(strategy="fresh")
    model.load(model_path)

    if not model.is_model_trained():
        raise RuntimeError(
            f"Loaded model from '{model_path}' is not marked as trained"
        )

    # ---- 2. Run generation in a fresh session ----
    async with session_scope() as session:
        repository = PredictionRepository(session)

        generator = PredictionGenerator(
            model=model,
            repository=repository,
            horizon="7d",
            horizon_hours=168,  # 7 * 24
            confidence=0.85,
            history_hours=2160,  # 90 days of history
        )

        result = await generator.generate()

    # ---- 3. Evaluate the outcome ----
    if not result.succeeded:
        raise RuntimeError(
            f"Prediction generation failed: {result.error}"
        )

    summary = {
        "horizon": result.horizon,
        "model_name": result.model_name,
        "prediction_time": result.prediction_time.isoformat(),
        "rows_generated": result.rows_generated,
        "rows_saved": result.rows_saved,
        "elapsed_seconds": result.elapsed_seconds,
        "succeeded": result.succeeded,
    }

    logger.info(
        f"daily_7d_prediction_job completed: "
        f"{result.rows_saved} rows saved in {result.elapsed_seconds:.3f}s"
    )

    return summary