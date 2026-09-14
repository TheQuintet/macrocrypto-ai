"""Job definitions for the AI Service scheduler.

Each job is a self-contained async function that:
    - Performs its work in a fresh database session
    - Returns a structured result dict (or raises on failure)
    - Never assumes anything about the scheduler that invokes it

Jobs currently registered:
    - hourly_prediction_job: generate 24h BTC predictions once per hour

Design:
    - Each job opens its own DB session via session_scope(); the
      scheduler does not manage sessions
    - Each job catches its own exceptions? No — jobs raise so the
      SchedulerManager can record failures, apply retries, and
      update the job state. The manager wraps every invocation.
    - Job functions are pure async callables with no scheduler
      dependencies — easy to unit test directly
"""

import logging
from typing import Any, Dict

from app.ai.models.prophet_model import ProphetModel
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
JOB_HOURLY_PREDICTION = "hourly_prediction"


# ============================================================
# HOURLY PREDICTION JOB
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
        # Generation returned a structured error — surface it as an
        # exception so the scheduler records a failure and can retry
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