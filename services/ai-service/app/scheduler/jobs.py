"""Job definitions for the AI Service scheduler.

Each job is a self-contained async function that:
    - Performs its work in a fresh database session
    - Returns a structured result dict (or raises on failure)
    - Never assumes anything about the scheduler that invokes it

Jobs currently registered:
    - daily_retrain_job: retrain all 6 models (6:00 AM UTC)
    - hourly_prediction_job: generate 24h BTC predictions (hourly)
    - daily_7d_prediction_job: generate 7d BTC predictions (6:30 AM UTC)
    - daily_backtest_job: walk-forward backtest all 6 models
      (6:45 AM UTC)
    - daily_accuracy_job: check metrics against thresholds, record
      breaches (7:00 AM UTC)
    - daily_multi_model_predictions_job: generate and store
      predictions for the 5 non-prophet_fresh variants (6:15 AM UTC,
      M6b)
    - daily_model_performance_aggregation_job: copy the latest
      aggregate metrics from prediction_performance into
      model_performance (7:15 AM UTC, M7b)
    - daily_correlation_job: compute BTC-vs-macro correlations for
      all indicators × windows (2:00 AM UTC, A1.5)
    - daily_export_cleanup_job: delete export files older than the
      configured TTL (3:00 AM UTC, A2.6)
    - daily_event_impact_update_job: recompute BTC reactions for
      every stored event, update on change (4:00 AM UTC, A5.5)

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
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.ai.backtest import BacktestResult, WalkForwardBacktester
from app.ai.models import (
    LightGBMModel,
    ProphetModel,
    XGBoostModel,
)
from app.ai.orchestrator import RetrainingOrchestrator
from app.ai.thresholds import (
    check_thresholds,
    filter_breaches,
)
from app.config import settings
from app.correlation.calculator import CorrelationCalculator
from app.database.engine import session_scope
from app.database.repositories.correlation_repository import (
    CorrelationRepository,
)
from app.database.repositories.event_impact_repository import (
    EventImpactRepository,
)
from app.database.repositories.model_performance_repository import (
    ModelPerformanceRepository,
    ModelPerformanceRow,
)
from app.database.repositories.performance_repository import (
    PerformanceRepository,
    PerformanceRow,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.database.repositories.threshold_repository import (
    ThresholdBreachRow,
    ThresholdRepository,
)
from app.events.reaction import ReactionCalculator
from app.export.storage import get_storage
from app.prediction.generator import PredictionGenerator
from app.prediction.market import classify_market_condition_safe

logger = logging.getLogger(__name__)


# ============================================================
# JOB NAME CONSTANTS
# ============================================================
# Stable identifiers used by SchedulerManager to register and
# track jobs. They appear in run history and log lines, so don't
# rename them without a migration plan.
JOB_DAILY_RETRAIN = "daily_retrain"
JOB_HOURLY_PREDICTION = "hourly_prediction"
JOB_DAILY_7D_PREDICTION = "daily_7d_prediction"
JOB_DAILY_BACKTEST = "daily_backtest"
JOB_DAILY_ACCURACY = "daily_accuracy"
JOB_DAILY_MULTI_MODEL_PREDICTIONS = "daily_multi_model_predictions"
JOB_DAILY_MODEL_PERFORMANCE_AGGREGATION = (
    "daily_model_performance_aggregation"
)
JOB_DAILY_CORRELATION = "daily_correlation"
JOB_DAILY_EXPORT_CLEANUP = "daily_export_cleanup"
JOB_DAILY_EVENT_IMPACT_UPDATE = "daily_event_impact_update"


# ============================================================
# BACKTEST VARIANT SPECS
# ============================================================
# Every (model variant, horizon) combination that the daily
# backtest runs. The variant name matches the keys used by
# `_variant_factory()` and by the model registry built in
# `_build_model_registry()`.
#
# Tuple layout: (variant_name, horizon_label, horizon_hours)
#
# 6 variants × 2 horizons = 12 backtests per daily run.
BACKTEST_VARIANTS: List[Tuple[str, str, int]] = [
    ("prophet_fresh", "24h", 24),
    ("prophet_fresh", "7d", 168),
    ("prophet_warm", "24h", 24),
    ("prophet_warm", "7d", 168),
    ("xgboost_fresh", "24h", 24),
    ("xgboost_fresh", "7d", 168),
    ("xgboost_incremental", "24h", 24),
    ("xgboost_incremental", "7d", 168),
    ("lightgbm_fresh", "24h", 24),
    ("lightgbm_fresh", "7d", 168),
    ("lightgbm_incremental", "24h", 24),
    ("lightgbm_incremental", "7d", 168),
]


# ============================================================
# MULTI-MODEL PREDICTION SPECS (M6b)
# ============================================================
# Every (variant, horizon) pair that the M6b prediction job
# generates and stores. This list deliberately EXCLUDES
# `prophet_fresh` because those predictions are already written
# by hourly_prediction_job (24h) and daily_7d_prediction_job (7d).
# Duplicating them here would produce two competing batches for the
# same key with slightly different timestamps, which would make the
# comparison endpoint's "latest batch" lookup non-deterministic.
#
# Tuple layout: (variant_name, horizon_label, horizon_hours)
#
# 5 variants × 2 horizons = 10 generator runs per daily run.
MULTI_MODEL_VARIANTS: List[Tuple[str, str, int]] = [
    ("prophet_warm", "24h", 24),
    ("prophet_warm", "7d", 168),
    ("xgboost_fresh", "24h", 24),
    ("xgboost_fresh", "7d", 168),
    ("xgboost_incremental", "24h", 24),
    ("xgboost_incremental", "7d", 168),
    ("lightgbm_fresh", "24h", 24),
    ("lightgbm_fresh", "7d", 168),
    ("lightgbm_incremental", "24h", 24),
    ("lightgbm_incremental", "7d", 168),
]


# ============================================================
# ACCURACY CHECK MATRIX
# ============================================================
# (model_name, horizon) pairs that the daily accuracy check
# evaluates. Matches the 12 backtest variants so every model that
# produced metrics is checked against thresholds.
ACCURACY_CHECK_MATRIX: List[Tuple[str, str]] = [
    (name, horizon)
    for name, horizon, _ in BACKTEST_VARIANTS
]


def _variant_factory(variant_name: str) -> Callable[[], Any]:
    """Return a factory for the given model variant name.

    The backtester needs a way to construct a *fresh* model
    instance on every iteration, because each iteration retrains
    from scratch (or warm-starts from the previous iteration's
    output). Passing a live instance would reuse stale state.

    This helper centralizes the variant → class mapping so the
    backtest job never has to know about ProphetModel vs
    XGBoostModel vs LightGBMModel directly.

    Args:
        variant_name: One of the names appearing in BACKTEST_VARIANTS.

    Returns:
        A zero-arg callable returning a fresh ForecastModel instance.

    Raises:
        ValueError: If variant_name is unknown.
    """
    if variant_name == "prophet_fresh":
        return lambda: ProphetModel(strategy="fresh")
    if variant_name == "prophet_warm":
        return lambda: ProphetModel(strategy="warm")
    if variant_name == "xgboost_fresh":
        return lambda: XGBoostModel(strategy="fresh")
    if variant_name == "xgboost_incremental":
        return lambda: XGBoostModel(strategy="incremental")
    if variant_name == "lightgbm_fresh":
        return lambda: LightGBMModel(strategy="fresh")
    if variant_name == "lightgbm_incremental":
        return lambda: LightGBMModel(strategy="incremental")

    raise ValueError(f"Unknown variant: {variant_name}")


def _load_variant_model(variant_name: str) -> Any:
    """Load a trained model variant from disk.

    The daily retrain job saves every variant to
    `{settings.model_save_dir}/{variant_name}.pkl` (see
    RetrainingOrchestrator._retrain_single). This helper mirrors
    that path exactly, so the two jobs always agree on where a
    given variant lives.

    Args:
        variant_name: One of the names appearing in MULTI_MODEL_VARIANTS.

    Returns:
        A loaded ForecastModel instance, marked as trained.

    Raises:
        ValueError: If variant_name is unknown.
        FileNotFoundError: If the saved artifact does not exist.
        RuntimeError: If the loaded model does not report as trained.
    """
    if variant_name == "prophet_warm":
        model = ProphetModel(strategy="warm")
    elif variant_name == "xgboost_fresh":
        model = XGBoostModel(strategy="fresh")
    elif variant_name == "xgboost_incremental":
        model = XGBoostModel(strategy="incremental")
    elif variant_name == "lightgbm_fresh":
        model = LightGBMModel(strategy="fresh")
    elif variant_name == "lightgbm_incremental":
        model = LightGBMModel(strategy="incremental")
    else:
        raise ValueError(f"Unknown variant: {variant_name}")

    save_path = f"{settings.model_save_dir}/{variant_name}.pkl"
    logger.debug(f"Loading model '{variant_name}' from '{save_path}'")
    model.load(save_path)

    if not model.is_model_trained():
        raise RuntimeError(
            f"Loaded model '{variant_name}' from '{save_path}' is not "
            f"marked as trained"
        )

    return model


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
    works with a clean set of untrained instances. Reusing a
    registry across runs would let previously trained models
    leak state into the next retraining cycle.

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

    # ---- 1. Fetch 90 days of training data ----
    # 2160 hours = 90 days. Chosen to comfortably fit weekly
    # seasonality (7 × 90 / 7 = 90 full weeks) plus lag features.
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

    # 60 rows is the service-wide floor across all model adapters.
    if len(training_frame) < 60:
        raise RuntimeError(
            f"Cannot retrain: insufficient training data "
            f"({len(training_frame)} rows, need at least 60)"
        )

    logger.info(
        f"Fetched {len(training_frame)} rows of training data "
        f"({history_hours}h)"
    )

    # ---- 2. Build a fresh registry + orchestrator ----
    models = _build_model_registry()
    model_save_dir = settings.model_save_dir

    orchestrator = RetrainingOrchestrator(
        models=models,
        model_save_dir=model_save_dir,
    )

    # ---- 3. Retrain all models ----
    # The orchestrator isolates per-model failures, so one bad
    # model does not prevent the others from being saved.
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
        # Surface partial failures so the manager can retry and
        # the run history reflects a non-clean state.
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
# DAILY BACKTEST JOB
# ============================================================
async def daily_backtest_job() -> Dict[str, Any]:
    """Run walk-forward backtests for all 6 models × 2 horizons.

    Runs daily at 6:45 AM UTC, after the 6:00 retrain and the
    6:30 7d prediction. Steps:
        1. Open a DB session and fetch 120 days of training data.
        2. For each of the 12 (variant, horizon) pairs:
            a. Run WalkForwardBacktester
            b. Convert the BacktestResult + raw predictions to
               PerformanceRow instances
            c. Persist them via PerformanceRepository
        3. Aggregate and return a summary.

    Idempotency note: the job is NOT deduplicating on run. If it
    runs twice in the same day, it will write two sets of rows. The
    scheduler's daily cron plus the max_instances=1 setting makes
    double-runs unlikely; if this becomes a concern, add a check
    against fetch_latest_forecast_date() at the start.

    Returns:
        Dict with keys: variants_attempted, variants_succeeded,
        variants_failed, total_rows_written, results (per-variant),
        elapsed_seconds.

    Raises:
        RuntimeError: If training data cannot be fetched, or if
            every variant fails.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_backtest_job")

    # ---- 1. Fetch training + actuals data ----
    # 2880 hours = 120 days. The 30-day walk-forward window
    # requires 30 × 168 = 5040 hours of contiguous data in the
    # worst case (7d horizon), plus 60 rows of warmup for lags.
    # 120 days gives us plenty of buffer.
    history_hours = settings.backtest_history_hours

    async with session_scope() as session:
        pred_repo = PredictionRepository(session)
        training_frame = await pred_repo.fetch_training_frame(
            hours=history_hours
        )

    if training_frame is None or training_frame.empty:
        raise RuntimeError(
            "Cannot backtest: training data is empty or unavailable"
        )

    # Worst case requirement: 30 iterations × 168 hours + 60 warmup
    required_rows = (
        settings.backtest_iterations * 168 + 60
    )
    if len(training_frame) < required_rows:
        raise RuntimeError(
            f"Cannot backtest: insufficient training data "
            f"({len(training_frame)} rows, need at least {required_rows})"
        )

    logger.info(
        f"Fetched {len(training_frame)} rows of training data "
        f"({history_hours}h) for backtesting"
    )

    # ---- 2. Run all 12 backtests ----
    # Each variant is independent: one failing variant does not
    # abort the others. Failures are captured in `results[key]`.
    results: Dict[str, Dict[str, Any]] = {}
    variants_succeeded = 0
    variants_failed = 0
    total_rows_written = 0

    async with session_scope() as session:
        perf_repo = PerformanceRepository(session)

        for variant_name, horizon, horizon_hours in BACKTEST_VARIANTS:
            key = f"{variant_name}_{horizon}"
            logger.info(f"Backtesting {key}")

            try:
                # The backtester walks forward one horizon step at
                # a time, retraining a fresh model on each slice.
                bt = WalkForwardBacktester(
                    horizon=horizon,
                    horizon_hours=horizon_hours,
                )

                factory = _variant_factory(variant_name)
                backtest_result = await bt.run(
                    model_name=variant_name,
                    build_model=factory,
                    training_data=training_frame,
                    actuals=training_frame,
                )

                if not backtest_result.succeeded:
                    raise RuntimeError(
                        f"Backtest failed: {backtest_result.error}"
                    )

                # Convert per-iteration matched points into rows
                # and persist them.
                rows = _result_to_rows(backtest_result)
                written = await perf_repo.save_performance_rows(rows)

                results[key] = {
                    "status": "success",
                    "horizon": horizon,
                    "iterations_succeeded": backtest_result.iterations_succeeded,
                    "iterations_failed": backtest_result.iterations_failed,
                    "total_matched_points": backtest_result.total_matched_points,
                    "mae": backtest_result.mae,
                    "rmse": backtest_result.rmse,
                    "mape": backtest_result.mape,
                    "directional_accuracy": (
                        backtest_result.directional_accuracy
                    ),
                    "rows_written": written,
                    "elapsed_seconds": backtest_result.elapsed_seconds,
                    "error": None,
                }
                variants_succeeded += 1
                total_rows_written += written

            except Exception as e:
                logger.error(
                    f"Backtest {key} failed: {e}",
                    exc_info=True,
                )
                results[key] = {
                    "status": "failed",
                    "error": str(e),
                }
                variants_failed += 1

    elapsed = time.monotonic() - start

    summary = {
        "variants_attempted": len(BACKTEST_VARIANTS),
        "variants_succeeded": variants_succeeded,
        "variants_failed": variants_failed,
        "total_rows_written": total_rows_written,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_backtest_job complete: "
        f"{variants_succeeded}/{len(BACKTEST_VARIANTS)} variants "
        f"succeeded, {total_rows_written} rows written, "
        f"in {elapsed:.3f}s"
    )

    # Only fail the whole job if EVERY variant failed. Partial
    # success is acceptable — the successes produced useful rows.
    if variants_succeeded == 0:
        raise RuntimeError(
            f"All {len(BACKTEST_VARIANTS)} backtest variants failed"
        )

    return summary


def _result_to_rows(result: BacktestResult) -> List[PerformanceRow]:
    """Convert a BacktestResult to PerformanceRow instances.

    Each iteration's matched (prediction, actual) pairs become one
    row per point. The iteration's aggregate metrics (mae/rmse/mape)
    are repeated on every row of that iteration.

    Market condition classification (T5.3):
        Each iteration's actuals are classified into one of
        'bull', 'bear', 'volatile', or 'neutral' based on the
        price trajectory during that iteration's forecast window.
        The label is repeated on every row of the iteration.

    Design note — why we repeat the aggregate metrics:
        The prediction_performance table is read by T5.5's endpoint
        with queries like "give me the latest 7d Prophet MAE". If
        the metrics only lived in a separate batch table, every
        read would need a join or a subquery. Repeating the
        metrics on each row makes the common query a trivial
        SELECT ... ORDER BY forecast_date DESC LIMIT 1.

        The storage cost is negligible: ~35k rows/day × 3 floats.
        If it ever becomes a concern, partition by created_at and
        archive old partitions.

    Design note — why prediction_id is None:
        Backtest rows are hypothetical: the predictions were
        produced and immediately compared, never stored in
        btc_predictions. There is no real prediction to reference,
        so the FK is NULL. Migration 005 relaxed the NOT NULL
        constraint precisely for this case.

    Args:
        result: The BacktestResult to convert.

    Returns:
        List of PerformanceRow instances, one per matched point.
    """
    rows: List[PerformanceRow] = []

    for it in result.iteration_results:
        # Skip iterations that failed during training or matching —
        # they have no matched_data and should not contribute rows.
        if it.error is not None:
            continue

        # Classify this iteration's market condition based on the
        # actuals observed during the forecast window. The label is
        # applied to every row of this iteration.
        #
        # We extract actuals in time order (they're already ordered
        # in matched_data) and pass them to the classifier.
        actuals = [actual for _, _, actual in it.matched_data]
        market_condition = classify_market_condition_safe(actuals)

        # Each entry in matched_data is
        # (forecast_timestamp, predicted_price, actual_price).
        for forecast_ts, predicted, actual in it.matched_data:
            rows.append(
                PerformanceRow(
                    horizon=result.horizon,
                    model_name=result.model_name,
                    # Version is hardcoded for now; M7 will pull it
                    # from the MLflow run metadata.
                    model_version="1.0.0",
                    forecast_date=forecast_ts,
                    predicted_price=predicted,
                    actual_price=actual,
                    # Aggregate metrics for the iteration this
                    # point belongs to. Repeated on every row of
                    # the iteration — see design note above.
                    mae=it.mae,
                    rmse=it.rmse,
                    mape=it.mape,
                    # Market condition for the iteration (may be
                    # None if the classifier couldn't decide).
                    market_condition=market_condition,
                    # Backtest rows have no corresponding
                    # btc_predictions entry — see design note above.
                    prediction_id=None,
                )
            )

    return rows


# ============================================================
# DAILY ACCURACY JOB
# ============================================================
async def daily_accuracy_job() -> Dict[str, Any]:
    """Check model metrics against thresholds and record breaches.

    Runs daily at 7:00 AM UTC, after the backtest (6:45) has
    written fresh metrics. Steps:
        1. Open a DB session.
        2. For each of the 12 (model, horizon) pairs:
            a. Read the latest aggregated metrics
            b. Check against thresholds
            c. Record any breaches in threshold_breaches
        3. Return a summary with breach counts per model.

    No email/pager notifications yet — that comes in T5.6 along
    with the 3-day streak escalation rule.

    Returns:
        Dict with keys: models_checked, breaches_detected,
        breach_summary (dict keyed by "model_horizon"),
        results (per-model dict), elapsed_seconds.

    Raises:
        RuntimeError: If no metrics could be checked.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_accuracy_job")

    results: Dict[str, Dict[str, Any]] = {}
    total_breaches = 0
    models_checked = 0
    models_failed = 0
    breach_summary: Dict[str, Dict[str, bool]] = {}

    async with session_scope() as session:
        perf_repo = PerformanceRepository(session)
        threshold_repo = ThresholdRepository(session)

        for model_name, horizon in ACCURACY_CHECK_MATRIX:
            key = f"{model_name}_{horizon}"
            logger.debug(f"Checking thresholds for {key}")

            try:
                # ---- 1. Read the latest aggregated metrics ----
                metrics = await perf_repo.fetch_latest_metrics(
                    horizon=horizon,
                    model_name=model_name,
                )

                if metrics is None:
                    logger.debug(
                        f"No metrics found for {key} — skipping"
                    )
                    results[key] = {
                        "status": "no_metrics",
                    }
                    continue

                # ---- 2. Compute mean actual price for normalization ----
                # We need it to convert MAE/RMSE from USD to %.
                # Use the (predictions, actuals) we already stored.
                mean_actual_price = await _get_mean_actual_price(
                    perf_repo,
                    horizon=horizon,
                    model_name=model_name,
                    lookback_days=settings.accuracy_lookback_days,
                )

                # ---- 3. Check thresholds ----
                checks = check_thresholds(
                    mae=metrics.get("mae"),
                    rmse=metrics.get("rmse"),
                    mape=metrics.get("mape"),
                    directional_accuracy=None,
                    mean_actual_price=mean_actual_price,
                )

                breached = filter_breaches(checks)

                # ---- 4. Record breaches ----
                if breached:
                    breach_rows = await _build_breach_rows(
                        threshold_repo,
                        horizon=horizon,
                        model_name=model_name,
                        checks=breached,
                        model_version=metrics.get("model_version"),
                    )
                    written = await threshold_repo.save_breaches(
                        breach_rows
                    )
                    total_breaches += written
                else:
                    written = 0

                # ---- 5. Track per-model status ----
                breach_summary[key] = {
                    c.metric: c.breached for c in checks
                }

                results[key] = {
                    "status": "success",
                    "metrics": {
                        "mae": metrics.get("mae"),
                        "rmse": metrics.get("rmse"),
                        "mape": metrics.get("mape"),
                    },
                    "mean_actual_price": mean_actual_price,
                    "checks": [c.to_dict() for c in checks],
                    "breaches_written": written,
                }
                models_checked += 1

            except Exception as e:
                logger.error(
                    f"Accuracy check for {key} failed: {e}",
                    exc_info=True,
                )
                results[key] = {
                    "status": "failed",
                    "error": str(e),
                }
                models_failed += 1

    elapsed = time.monotonic() - start

    summary = {
        "models_checked": models_checked,
        "models_failed": models_failed,
        "breaches_detected": total_breaches,
        "breach_summary": breach_summary,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_accuracy_job complete: "
        f"{models_checked} models checked, "
        f"{total_breaches} breaches recorded, "
        f"in {elapsed:.3f}s"
    )

    if models_checked == 0 and models_failed > 0:
        raise RuntimeError(
            f"All {models_failed} accuracy checks failed"
        )

    return summary


async def _get_mean_actual_price(
    perf_repo: PerformanceRepository,
    horizon: str,
    model_name: str,
    lookback_days: int,
) -> Optional[float]:
    """Return the mean actual price over the recent evaluation window.

    Used to normalize MAE/RMSE from USD to % of mean price.

    Args:
        perf_repo: The performance repository.
        horizon: Horizon label.
        model_name: Model identifier.
        lookback_days: How far back to average.

    Returns:
        Mean actual price, or None if no rows exist.
    """
    # Query the underlying table directly for a simple AVG.
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import func, select

    from app.database.tables import prediction_performance

    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    stmt = select(
        func.avg(prediction_performance.c.actual_price)
    ).where(
        prediction_performance.c.horizon == horizon,
        prediction_performance.c.model_name == model_name,
        prediction_performance.c.forecast_date >= since,
    )

    result = await perf_repo.session.execute(stmt)
    value = result.scalar_one_or_none()

    if value is None:
        return None

    return float(value)


async def _build_breach_rows(
    threshold_repo: ThresholdRepository,
    horizon: str,
    model_name: str,
    checks: List[Any],
    model_version: Optional[str] = None,
) -> List[ThresholdBreachRow]:
    """Build ThresholdBreachRow instances with consecutive-day counters.

    For each breach, look up the previous breach of the same metric
    and increment `consecutive_days` if the last breach was on the
    previous day. Otherwise start a new streak.

    Args:
        threshold_repo: The threshold repository.
        horizon: Horizon label.
        model_name: Model identifier.
        checks: The filtered (breached) ThresholdCheckResult list.
        model_version: Optional model version string.

    Returns:
        List of ThresholdBreachRow instances.
    """
    from datetime import datetime, timezone

    rows: List[ThresholdBreachRow] = []
    now = datetime.now(timezone.utc)

    for check in checks:
        consecutive = 1

        try:
            previous = await threshold_repo.fetch_latest_breach(
                horizon=horizon,
                model_name=model_name,
                metric=check.metric,
            )

            if previous is not None:
                prev_detected = previous["detected_at"]
                # `detected_at` is a datetime; make it tz-aware
                if prev_detected.tzinfo is None:
                    prev_detected = prev_detected.replace(
                        tzinfo=timezone.utc
                    )
                # If the last breach was on the previous calendar day,
                # extend the streak
                days_between = (now.date() - prev_detected.date()).days
                if days_between == 1:
                    consecutive = int(previous["consecutive_days"]) + 1
                elif days_between == 0:
                    # Same day — keep the previous streak (idempotency)
                    consecutive = int(previous["consecutive_days"])
        except Exception as e:
            logger.warning(
                f"Failed to look up prior breach for "
                f"{horizon}/{model_name}/{check.metric}: {e}"
            )

        rows.append(
            ThresholdBreachRow(
                horizon=horizon,
                model_name=model_name,
                metric=check.metric,
                metric_unit=check.metric_unit,
                value=check.value,
                threshold=check.threshold,
                breach_direction=check.breach_direction,
                consecutive_days=consecutive,
                model_version=model_version,
            )
        )

    return rows


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

    model_path = settings.prophet_24h_model_path
    logger.debug(f"Loading Prophet model from '{model_path}'")

    model = ProphetModel(strategy="fresh")
    model.load(model_path)

    if not model.is_model_trained():
        raise RuntimeError(
            f"Loaded model from '{model_path}' is not marked as trained"
        )

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

    model_path = settings.prophet_7d_model_path
    logger.debug(f"Loading Prophet model from '{model_path}'")

    model = ProphetModel(strategy="fresh")
    model.load(model_path)

    if not model.is_model_trained():
        raise RuntimeError(
            f"Loaded model from '{model_path}' is not marked as trained"
        )

    async with session_scope() as session:
        repository = PredictionRepository(session)

        generator = PredictionGenerator(
            model=model,
            repository=repository,
            horizon="7d",
            horizon_hours=168,
            confidence=0.85,
            # 90 days of history to observe multiple weekly cycles
            history_hours=2160,
        )

        result = await generator.generate()

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


# ============================================================
# DAILY MULTI-MODEL PREDICTION JOB (M6b)
# ============================================================
async def daily_multi_model_predictions_job() -> Dict[str, Any]:
    """Generate and store predictions for the 5 non-prophet variants.

    Runs daily at 6:15 AM UTC, after the 6:00 retrain has saved all
    six model artifacts to disk and before the 6:30 7d Prophet
    prediction. The purpose is to populate `btc_predictions` with
    rows from every model variant, so the M6a comparison endpoint
    has real multi-model data to compare.

    prophet_fresh is deliberately excluded: its 24h batch is
    produced by hourly_prediction_job and its 7d batch by
    daily_7d_prediction_job. Duplicating those here would create
    competing batches for the same (horizon, model_name) key with
    different `prediction_time` values, and the comparison
    endpoint's "latest batch" lookup would become non-deterministic.

    Steps:
        1. For each (variant, horizon) in MULTI_MODEL_VARIANTS:
            a. Load the trained model from
               `{settings.model_save_dir}/{variant}.pkl`
            b. Open a DB session
            c. Build a PredictionGenerator for the horizon
            d. Run generate() and let the generator write rows
        2. Aggregate results and return a summary.

    Failure isolation: each (variant, horizon) pair is wrapped in
    its own try/except, so a missing or corrupt artifact for one
    variant does not prevent the others from being written. The
    job raises only if every pair failed.

    Idempotency note: the generator writes a fresh batch each run
    with a new `prediction_time`, and the comparison endpoint
    always reads the latest batch. Re-running this job is therefore
    safe — it just produces a newer batch that supersedes the
    previous one.

    Returns:
        Dict with keys: variants_attempted (int),
        variants_succeeded (int), variants_failed (int),
        total_rows_saved (int), results (per-key dict),
        elapsed_seconds.

    Raises:
        RuntimeError: If every (variant, horizon) pair failed.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_multi_model_predictions_job")

    results: Dict[str, Dict[str, Any]] = {}
    succeeded = 0
    failed = 0
    total_rows_saved = 0

    for variant_name, horizon, horizon_hours in MULTI_MODEL_VARIANTS:
        key = f"{variant_name}_{horizon}"
        logger.info(f"Generating predictions for {key}")

        try:
            # ---- 1. Load the trained model ----
            model = _load_variant_model(variant_name)

            # ---- 2. Generate predictions in a fresh session ----
            async with session_scope() as session:
                repository = PredictionRepository(session)
                generator = PredictionGenerator(
                    model=model,
                    repository=repository,
                    horizon=horizon,
                    horizon_hours=horizon_hours,
                    confidence=0.85,
                )
                gen_result = await generator.generate()

            if not gen_result.succeeded:
                raise RuntimeError(
                    f"Prediction generation failed: {gen_result.error}"
                )

            results[key] = {
                "status": "success",
                "variant": variant_name,
                "horizon": horizon,
                "model_name": gen_result.model_name,
                "prediction_time": gen_result.prediction_time.isoformat(),
                "rows_generated": gen_result.rows_generated,
                "rows_saved": gen_result.rows_saved,
                "elapsed_seconds": gen_result.elapsed_seconds,
                "error": None,
            }
            succeeded += 1
            total_rows_saved += gen_result.rows_saved

        except Exception as e:
            logger.error(
                f"Multi-model prediction for {key} failed: {e}",
                exc_info=True,
            )
            results[key] = {
                "status": "failed",
                "variant": variant_name,
                "horizon": horizon,
                "error": str(e),
            }
            failed += 1

    elapsed = time.monotonic() - start

    summary = {
        "variants_attempted": len(MULTI_MODEL_VARIANTS),
        "variants_succeeded": succeeded,
        "variants_failed": failed,
        "total_rows_saved": total_rows_saved,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_multi_model_predictions_job complete: "
        f"{succeeded}/{len(MULTI_MODEL_VARIANTS)} pairs succeeded, "
        f"{total_rows_saved} rows saved, in {elapsed:.3f}s"
    )

    # Only fail the whole job if EVERY pair failed. Partial success
    # is acceptable — the successes produced real rows that the
    # comparison endpoint can use.
    if succeeded == 0:
        raise RuntimeError(
            f"All {len(MULTI_MODEL_VARIANTS)} multi-model prediction "
            f"pairs failed"
        )

    return summary


# ============================================================
# DAILY MODEL PERFORMANCE AGGREGATION JOB (M7b)
# ============================================================
async def daily_model_performance_aggregation_job() -> Dict[str, Any]:
    """Copy the latest aggregate metrics into model_performance.

    Runs daily at 7:15 AM UTC, after the 6:45 backtest has written
    fresh rows to prediction_performance and after the 7:00
    accuracy check has read the same source. This job reads the
    latest aggregate metrics for each (model, horizon) pair and
    writes one row per pair to model_performance, so the M8
    multi-model performance API has a compact, indexed history to
    read from instead of re-aggregating prediction_performance on
    every request.

    Steps:
        1. Open a DB session.
        2. For each (model_name, horizon) in ACCURACY_CHECK_MATRIX:
            a. Read the latest aggregate metrics via
               PerformanceRepository.fetch_latest_metrics()
            b. Build a ModelPerformanceRow
            c. Write it via ModelPerformanceRepository.save_rows()
        3. Aggregate results and return a summary.

    Sample-size semantics:
        Each row written here represents one aggregate contribution.
        We set sample_size=1 because we are recording one aggregate
        row, not the underlying per-point count. The metrics
        themselves (mae, rmse, mape, directional_accuracy) are
        copied verbatim from the source aggregate row. If a true
        sample count becomes important later, add a method to
        PerformanceRepository that returns the row count for the
        same window.

    Failure isolation:
        Each (model, horizon) pair is wrapped in its own try/except.
        A pair with no source metrics (fetch_latest_metrics returns
        None) is counted as "skipped", not "failed" — this is a
        normal situation on the first run of a brand-new model. The
        job raises only if every pair failed for a non-skip reason.

    Idempotency:
        Each run writes a fresh row per (model, horizon) with a new
        calculated_at. Re-running the same day produces a second
        row, which is intentional — model_performance is a time
        series, and the M8 API reads the latest row per pair. If
        double-runs become a concern, add a deduplication check
        against a "calculated_at on the same calendar day" test.

    Returns:
        Dict with keys: pairs_attempted (int),
        pairs_written (int), pairs_skipped (int),
        pairs_failed (int), total_rows_written (int),
        results (per-key dict), elapsed_seconds.

    Raises:
        RuntimeError: If every pair failed (or was skipped) for a
            non-empty ACCURACY_CHECK_MATRIX.
    """
    import time
    from datetime import datetime, timezone

    start = time.monotonic()
    logger.info("Running daily_model_performance_aggregation_job")

    results: Dict[str, Dict[str, Any]] = {}
    written = 0
    skipped = 0
    failed = 0
    total_rows = 0

    # Single timestamp for the whole run so all rows share one
    # calculated_at. This makes it easy to identify "what the
    # table looked like after the 7:15 run on a given day".
    calculated_at = datetime.now(timezone.utc)

    async with session_scope() as session:
        perf_repo = PerformanceRepository(session)
        model_perf_repo = ModelPerformanceRepository(session)

        for model_name, horizon in ACCURACY_CHECK_MATRIX:
            key = f"{model_name}_{horizon}"
            logger.debug(f"Aggregating model performance for {key}")

            try:
                # ---- 1. Read the latest aggregate metrics ----
                metrics = await perf_repo.fetch_latest_metrics(
                    horizon=horizon,
                    model_name=model_name,
                )

                if metrics is None:
                    # Normal on first runs — no source data yet for
                    # this (model, horizon). Count as skipped, not failed.
                    logger.debug(
                        f"No source metrics for {key} — skipping"
                    )
                    results[key] = {"status": "skipped"}
                    skipped += 1
                    continue

                # ---- 2. Build the ModelPerformanceRow ----
                row = ModelPerformanceRow(
                    model_name=model_name,
                    horizon=horizon,
                    sample_size=1,
                    calculated_at=calculated_at,
                    mae=metrics.get("mae"),
                    rmse=metrics.get("rmse"),
                    mape=metrics.get("mape"),
                    directional_accuracy=metrics.get(
                        "directional_accuracy"
                    ),
                )

                # ---- 3. Persist ----
                n = await model_perf_repo.save_rows([row])

                results[key] = {
                    "status": "written",
                    "rows_written": n,
                    "mae": row.mae,
                    "rmse": row.rmse,
                    "mape": row.mape,
                    "directional_accuracy": row.directional_accuracy,
                }
                written += 1
                total_rows += n

            except Exception as e:
                logger.error(
                    f"Model performance aggregation for {key} "
                    f"failed: {e}",
                    exc_info=True,
                )
                results[key] = {
                    "status": "failed",
                    "error": str(e),
                }
                failed += 1

    elapsed = time.monotonic() - start

    summary = {
        "pairs_attempted": len(ACCURACY_CHECK_MATRIX),
        "pairs_written": written,
        "pairs_skipped": skipped,
        "pairs_failed": failed,
        "total_rows_written": total_rows,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_model_performance_aggregation_job complete: "
        f"{written} written, {skipped} skipped, {failed} failed, "
        f"{total_rows} rows, in {elapsed:.3f}s"
    )

    # Only fail if every pair failed for a non-skip reason. Skips
    # are expected (a brand-new model has no source metrics yet).
    if written == 0 and failed > 0:
        raise RuntimeError(
            f"All {failed} model performance aggregation pairs failed"
        )

    return summary


# ============================================================
# DAILY CORRELATION JOB (A1.5)
# ============================================================
async def daily_correlation_job() -> Dict[str, Any]:
    """Compute BTC-vs-macro correlations for all indicators × windows.

    Runs daily at 2:00 AM UTC, well before the 6:00 retrain. Fetches
    the previous day's BTC price and macro indicator data, resamples
    BTC to daily close, computes Pearson correlations for every
    (indicator, window) pair, and writes one row per pair to the
    btc_macro_correlation table. The read API (A1.6) will surface
    those rows.

    Steps:
        1. Open a DB session.
        2. Build a CorrelationCalculator with the two repositories
           it needs (CorrelationRepository + PredictionRepository).
        3. Call calc.run().
        4. Return a summary dict derived from the calculation result.

    Failure semantics:
        The calculator already isolates failures per (indicator,
        window) pair and captures skips and errors in its result.
        The job only raises when the calculator produced zero rows
        AND recorded zero skips AND zero errors — which means the
        calculator could not fetch either source table at all
        (BTC or macro data entirely unavailable). That's the one
        condition a retry might resolve; everything else is data
        the operator sees in the run summary and logs.

    Notification semantics:
        Matches the existing jobs: success and failure are recorded
        in SchedulerState (visible via the run history) and logged
        at INFO (success) or ERROR (failure). The scheduler's
        retry policy applies if the job raises. No external
        notification system is used.

    Returns:
        Dict with keys: rows_built (int), rows_written (int),
        skipped_count (int), error_count (int),
        elapsed_seconds (float), calculated_at (ISO string).

    Raises:
        RuntimeError: If the calculator produced no rows, no
            skips, and no errors — meaning both source fetches
            failed or both returned empty.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_correlation_job")

    async with session_scope() as session:
        correlation_repo = CorrelationRepository(session)
        prediction_repo = PredictionRepository(session)

        calculator = CorrelationCalculator(
            correlation_repo=correlation_repo,
            prediction_repo=prediction_repo,
        )

        result = await calculator.run()

    elapsed = time.monotonic() - start

    summary = {
        "rows_built": result.rows_built,
        "rows_written": result.rows_written,
        "skipped_count": len(result.skipped),
        "error_count": len(result.errors),
        "elapsed_seconds": result.elapsed_seconds,
        "calculated_at": result.calculated_at.isoformat(),
    }

    logger.info(
        f"daily_correlation_job complete: "
        f"{result.rows_built} built, {result.rows_written} written, "
        f"{len(result.skipped)} skipped, {len(result.errors)} errors, "
        f"in {elapsed:.3f}s"
    )

    # The calculator returns a result even when both source fetches
    # fail (it catches those errors internally and returns early).
    # If NOTHING was attempted and nothing was skipped and nothing
    # errored, that means the calculator could not even reach the
    # per-pair loop — the two empty source fetches took that path.
    # This is the one condition a retry might resolve, so we raise.
    if (
        result.rows_built == 0
        and len(result.skipped) == 0
        and len(result.errors) == 0
    ):
        raise RuntimeError(
            "daily_correlation_job produced no rows, no skips, and no "
            "errors — both source tables appear to be empty or "
            "unavailable. See the previous log lines for details."
        )

    return summary


# ============================================================
# DAILY EXPORT CLEANUP JOB (A2.6)
# ============================================================
async def daily_export_cleanup_job() -> Dict[str, Any]:
    """Delete export files older than the configured TTL.

    Runs daily at 3:00 AM UTC. Iterates the keys currently in
    storage, checks each one's modification time against
    ``settings.export_file_ttl_seconds``, and deletes the expired
    ones. Returns a summary of what was removed.

    Backend scope:
        Age-based cleanup requires the backend to expose an
        ``mtime`` method. ``LocalDiskStorage`` does; the in-memory
        test fake does; a future S3 backend will not (it will
        expire files via bucket lifecycle policies instead). The
        job inspects the backend via ``hasattr(storage, "mtime")``
        and no-ops on any backend that lacks it, logging the
        reason. That check is where the "which backends support
        age-based cleanup" decision is enforced.

    Relationship to the download link TTL:
        ``export_link_ttl_seconds`` and ``export_file_ttl_seconds``
        both default to 7 days. A download link is considered
        expired when its file has been deleted, so the download
        endpoint's "no file found" 404 is what enforces link
        expiry on this branch. The cleanup job is what produces
        that state.

    Failure semantics:
        Per-key deletion errors are caught and counted, not
        raised. A single locked or permission-denied file should
        not abort the whole run. The job only raises if the
        storage backend itself is unreachable — which on this
        branch means a disk-level error during ``list()``.

    Idempotency:
        Re-running the job is safe. Files already deleted are
        simply absent from ``list()``; a missing key is a no-op.

    Returns:
        Dict with keys: backend (str), scanned (int),
        deleted (int), skipped_not_expired (int),
        failed (int), ttl_seconds (int), results (per-key dict),
        elapsed_seconds (float).

    Raises:
        RuntimeError: If the storage backend cannot be listed.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_export_cleanup_job")

    storage = get_storage()

    # ---- 1. Backend check ----
    # Age-based cleanup requires the backend to expose an ``mtime``
    # method. ``LocalDiskStorage`` does; a future S3 backend will
    # not (it will expire files via bucket lifecycle policies
    # instead), and a minimal test fake can omit it. The check is
    # deliberately "has mtime" rather than an isinstance against a
    # concrete class, so any backend which grows the same
    # capability is picked up automatically.
    if not hasattr(storage, "mtime"):
        elapsed = time.monotonic() - start
        logger.info(
            f"daily_export_cleanup_job: backend "
            f"{type(storage).__name__} does not support age-based "
            f"cleanup on this branch — skipping"
        )
        return {
            "backend": type(storage).__name__,
            "scanned": 0,
            "deleted": 0,
            "skipped_not_expired": 0,
            "failed": 0,
            "ttl_seconds": settings.export_file_ttl_seconds,
            "results": {},
            "elapsed_seconds": elapsed,
        }

    ttl_seconds = settings.export_file_ttl_seconds
    now = time.time()
    cutoff = now - ttl_seconds

    results: Dict[str, Dict[str, Any]] = {}
    deleted = 0
    skipped = 0
    failed = 0

    # ---- 2. List keys ----
    try:
        keys = storage.list()
    except Exception as e:
        # If we cannot even list, the whole job is dead. Raise so
        # the scheduler records the failure and applies retries.
        raise RuntimeError(
            f"Cannot list export storage: {e}"
        ) from e

    logger.info(
        f"daily_export_cleanup_job: scanning {len(keys)} file(s), "
        f"TTL={ttl_seconds}s"
    )

    # ---- 3. Delete expired keys ----
    for key in keys:
        try:
            mtime = storage.mtime(key)
        except FileNotFoundError:
            # Raced with a delete — treat as already cleaned.
            logger.debug(
                f"daily_export_cleanup_job: {key!r} vanished before stat"
            )
            results[key] = {"status": "vanished"}
            continue
        except Exception as e:
            logger.warning(
                f"daily_export_cleanup_job: could not stat {key!r}: {e}"
            )
            results[key] = {"status": "stat_failed", "error": str(e)}
            failed += 1
            continue

        if mtime >= cutoff:
            results[key] = {
                "status": "kept",
                "age_seconds": now - mtime,
            }
            skipped += 1
            continue

        try:
            removed = storage.delete(key)
        except Exception as e:
            logger.warning(
                f"daily_export_cleanup_job: could not delete "
                f"{key!r}: {e}"
            )
            results[key] = {"status": "delete_failed", "error": str(e)}
            failed += 1
            continue

        if removed:
            results[key] = {
                "status": "deleted",
                "age_seconds": now - mtime,
            }
            deleted += 1
        else:
            results[key] = {
                "status": "already_gone",
                "age_seconds": now - mtime,
            }

    elapsed = time.monotonic() - start

    summary = {
        "backend": type(storage).__name__,
        "scanned": len(keys),
        "deleted": deleted,
        "skipped_not_expired": skipped,
        "failed": failed,
        "ttl_seconds": ttl_seconds,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_export_cleanup_job complete: "
        f"scanned={len(keys)} deleted={deleted} "
        f"kept={skipped} failed={failed} in {elapsed:.3f}s"
    )

    return summary


# ============================================================
# DAILY EVENT IMPACT UPDATE JOB (A5.5)
# ============================================================
async def daily_event_impact_update_job() -> Dict[str, Any]:
    """Recompute BTC reactions for every stored event and update on change.

    Runs daily at 4:00 AM UTC. The AI Service has no external
    source of "new events" — the A5.1 docstring is explicit that
    a row in ``historical_event_impacts`` implicitly defines the
    event. What this job can do, idempotently, is:

        1. Read every row currently in ``historical_event_impacts``.
        2. Recompute the reaction for each ``(event_name, event_date)``
           using A5.2's ``ReactionCalculator``.
        3. If the recomputed reaction differs from the stored one,
           delete the stored row and re-insert the new one. The
           A5.1 table has a UNIQUE (event_name, event_date)
           constraint, so an in-place UPDATE would need a bespoke
           SQL statement; delete-then-insert is the pattern
           ``EventImpactRepository.delete_by_event`` exists for.
        4. If the recomputed reaction is identical, skip — no write,
           no churn.

    Why "recompute-and-update" rather than "discover new events":
        There is no external event feed. The job cannot invent
        events. What it *can* do is keep the stored rows honest
        against the current BTC price history, which is the
        failure mode A5.2's design anticipates: if the Data
        Ingestion Service backfills or corrects BTC prices, the
        stored reactions become stale, and this job corrects them
        on the next daily run.

    Idempotency:
        Re-running the same day produces zero writes on the second
        run. Comparison is exact (float equality on the five
        comparable fields), so a row only changes if a price
        actually moved.

    Failure semantics:
        Each event is wrapped in its own try/except. A per-event
        failure is counted and logged; it does not abort the run.
        The job raises only when the initial read failed entirely
        (i.e., the source table is unreachable), which is the one
        condition a retry might resolve.

    Notification semantics:
        Matches the eight prior jobs: success and failure are
        recorded in SchedulerState via the manager's ``_wrap_job``
        and logged at INFO (success) or ERROR (failure). No
        external notification system exists in the AI Service;
        see the A5.5 PR description for the deferred status.

    Returns:
        Dict with keys: events_seen (int), events_updated (int),
        events_unchanged (int), events_skipped (int),
        events_failed (int), results (per-event dict),
        elapsed_seconds (float).

    Raises:
        RuntimeError: If the read of ``historical_event_impacts``
            fails entirely — the only condition worth a retry.
    """
    import time

    start = time.monotonic()
    logger.info("Running daily_event_impact_update_job")

    # ---- 1. Read every stored event ----
    async with session_scope() as session:
        event_repo = EventImpactRepository(session)

        try:
            stored_rows = await event_repo.fetch_all(limit=10_000)
        except Exception as e:
            # The one condition worth a retry: we cannot even read
            # the source table. Anything else is per-event and
            # handled below.
            raise RuntimeError(
                f"Cannot read historical_event_impacts: {e}"
            ) from e

    logger.info(
        f"daily_event_impact_update_job: {len(stored_rows)} stored "
        f"event(s) to evaluate"
    )

    results: Dict[str, Dict[str, Any]] = {}
    seen = 0
    updated = 0
    unchanged = 0
    skipped = 0
    failed = 0

    for row in stored_rows:
        key = f"{row['event_name']}_{row['event_date'].isoformat()}"
        seen += 1

        try:
            event_name = row["event_name"]
            event_date = row["event_date"]
            impact_level = row["impact_level"]

            # ---- 2. Recompute the reaction ----
            async with session_scope() as session:
                prediction_repo = PredictionRepository(session)
                calc = ReactionCalculator(
                    prediction_repo=prediction_repo,
                )
                calc_result = await calc.run(
                    [
                        {
                            "event_name": event_name,
                            "event_date": event_date,
                            "impact_level": impact_level,
                        }
                    ]
                )

            # If the recompute skipped (missing price data now),
            # leave the stored row alone. A previously-computed
            # reaction is better than deleting it on a transient
            # data gap. The skip is reported in `results`.
            if calc_result.rows_built == 0:
                reason = (
                    calc_result.skipped[0].reason
                    if calc_result.skipped
                    else "unknown"
                )
                results[key] = {
                    "status": "skipped",
                    "reason": reason,
                }
                skipped += 1
                continue

            new_row = calc_result.rows[0]

            # ---- 3. Compare to stored ----
            if _event_row_matches(row, new_row):
                results[key] = {"status": "unchanged"}
                unchanged += 1
                continue

            # ---- 4. Delete + re-insert ----
            async with session_scope() as session:
                event_repo = EventImpactRepository(session)

                deleted = await event_repo.delete_by_event(
                    event_name=event_name,
                    event_date=event_date,
                )
                if not deleted:
                    # Someone else removed the row between our read
                    # and now. Treat as skipped — not our row to
                    # update.
                    results[key] = {
                        "status": "skipped",
                        "reason": "vanished_before_update",
                    }
                    skipped += 1
                    continue

                written = await event_repo.save_rows([new_row])

            results[key] = {
                "status": "updated",
                "rows_written": written,
                "old": {
                    "price_change_percent": row["price_change_percent"],
                    "volatility": row["volatility"],
                    "direction": row["direction"],
                },
                "new": {
                    "price_change_percent": new_row.price_change_percent,
                    "volatility": new_row.volatility,
                    "direction": new_row.direction,
                },
            }
            updated += 1

        except Exception as e:
            logger.error(
                f"Event impact update for {key} failed: {e}",
                exc_info=True,
            )
            results[key] = {
                "status": "failed",
                "error": str(e),
            }
            failed += 1

    elapsed = time.monotonic() - start

    summary = {
        "events_seen": seen,
        "events_updated": updated,
        "events_unchanged": unchanged,
        "events_skipped": skipped,
        "events_failed": failed,
        "results": results,
        "elapsed_seconds": elapsed,
    }

    logger.info(
        f"daily_event_impact_update_job complete: "
        f"{updated} updated, {unchanged} unchanged, "
        f"{skipped} skipped, {failed} failed, "
        f"in {elapsed:.3f}s"
    )

    return summary


def _event_row_matches(
    stored: Dict[str, Any],
    computed: Any,
) -> bool:
    """Return True if the recomputed reaction equals the stored one.

    Comparison is on the five fields the recompute can change:
    ``btc_price_before``, ``btc_price_after``,
    ``price_change_percent``, ``volatility``, and ``direction``.
    The two price columns are included because a genuine price
    revision moves them even if the aggregate metrics coincidentally
    agree.

    Exact float equality is used. A tolerance-based comparison
    would treat a small drift as "unchanged" and quietly leave a
    stale row in place. Exact equality means the job writes only
    when a value truly differs, which is the intent.

    Args:
        stored: A dict row from ``EventImpactRepository.fetch_all``.
        computed: An ``EventImpactRow`` from the reaction calculator.

    Returns:
        True when all five comparable fields are equal.
    """
    return (
        stored["btc_price_before"] == computed.btc_price_before
        and stored["btc_price_after"] == computed.btc_price_after
        and stored["price_change_percent"] == computed.price_change_percent
        and stored["volatility"] == computed.volatility
        and stored["direction"] == computed.direction
    )