"""Manual pipeline CLI for the AI Service.

Provides four subcommands that share the same ML flow as the live
scheduler, but run manually against the file-based feature source
(parquet) instead of the DB:

    train      — Train the 6 candidate models on the train partition.
    backtest   — Run walk-forward backtests across all (variant,
                 horizon) pairs and persist the per-point metrics.
    predict    — Generate and store predictions from trained models.
    run        — Run train → backtest → predict in sequence.

Usage:
    python -m app.ai.pipeline train
    python -m app.ai.pipeline backtest --horizon 24h
    python -m app.ai.pipeline predict --confidence 0.85
    python -m app.ai.pipeline run
    python -m app.ai.pipeline run --models prophet_fresh,xgboost_fresh

The CLI is the manual entry point for the file-path feature source.
It shares the same repository methods, model classes, and
orchestrator as the scheduled jobs — no code is duplicated.

Exit codes:
    0 — success
    1 — one or more steps failed
    2 — CLI argument error (argparse default)

Design notes:
    - Every subcommand reads features via
      PredictionRepository.fetch_training_frame_for_source with a
      FeatureContext. This keeps the CLI source-agnostic.
    - The train subcommand saves all 6 models to
      {settings.model_save_dir}/{variant}.pkl, matching the layout
      the scheduler expects.
    - The backtest subcommand writes per-point rows to
      prediction_performance, matching the scheduler's format.
    - The predict subcommand writes rows to btc_predictions.
    - The champion selection is INTENTIONALLY not implemented here.
      That is a separate phase (see known_issues.md #17). This CLI
      trains, backtests, and predicts with all 6 variants so that
      champion selection has data to work with.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from app.ai.backtest import BacktestResult, WalkForwardBacktester
from app.ai.models import (
    LightGBMModel,
    ProphetModel,
    XGBoostModel,
)
from app.ai.orchestrator import RetrainingOrchestrator
from app.config import settings
from app.database.engine import dispose_engine, session_scope
from app.database.enums import FeatureContext, FeaturePartition
from app.database.repositories.performance_repository import (
    PerformanceRepository,
    PerformanceRow,
)
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.prediction.generator import PredictionGenerator
from app.prediction.market import classify_market_condition_safe


logger = logging.getLogger("app.ai.pipeline")


# ============================================================
# CONSTANTS
# ============================================================
ALL_VARIANTS: Tuple[str, ...] = (
    "prophet_fresh",
    "prophet_warm",
    "xgboost_fresh",
    "xgboost_incremental",
    "lightgbm_fresh",
    "lightgbm_incremental",
)

# (variant, horizon, horizon_hours) — the full 12-pair matrix.
VARIANT_HORIZONS: Tuple[Tuple[str, str, int], ...] = tuple(
    (variant, horizon, hours)
    for variant in ALL_VARIANTS
    for horizon, hours in (("24h", 24), ("7d", 168))
)

# Per-command default history lengths (in hours).
DEFAULT_TRAIN_HOURS = 2160        # 90 days
DEFAULT_BACKTEST_HOURS = 2880     # 120 days
DEFAULT_PREDICT_HOURS = 720       # 30 days

# Minimum rows required by the models.
MIN_TRAIN_ROWS = 60

# Log format shared by all subcommands.
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


# ============================================================
# HELPERS
# ============================================================
def _configure_logging(level: Optional[str] = None) -> None:
    """Configure root logging for the CLI run."""
    effective_level = (level or settings.log_level).upper()
    logging.basicConfig(
        level=effective_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        force=True,
    )


def _parse_models(models_arg: Optional[str]) -> List[str]:
    """Parse --models value into a list of variant names.

    Args:
        models_arg: Comma-separated variant names, or None.

    Returns:
        List of variant names. When None, returns all 6 variants.

    Raises:
        ValueError: If any variant name is unknown.
    """
    if not models_arg:
        return list(ALL_VARIANTS)

    names = [name.strip() for name in models_arg.split(",") if name.strip()]
    if not names:
        return list(ALL_VARIANTS)

    unknown = [name for name in names if name not in ALL_VARIANTS]
    if unknown:
        raise ValueError(
            f"Unknown variant(s): {unknown}. "
            f"Valid: {list(ALL_VARIANTS)}"
        )

    return names


def _parse_horizons(horizon_arg: str) -> List[Tuple[str, int]]:
    """Parse --horizon value into a list of (label, hours) tuples.

    Args:
        horizon_arg: One of "24h", "7d", or "both".

    Returns:
        List of (label, hours) tuples.
    """
    if horizon_arg == "both":
        return [("24h", 24), ("7d", 168)]
    if horizon_arg == "24h":
        return [("24h", 24)]
    if horizon_arg == "7d":
        return [("7d", 168)]
    raise ValueError(f"Unknown horizon: {horizon_arg}")


def _build_model(variant: str) -> Any:
    """Instantiate a fresh model for the given variant name.

    Args:
        variant: One of ALL_VARIANTS.

    Returns:
        A fresh, untrained ForecastModel instance.

    Raises:
        ValueError: If the variant is unknown.
    """
    if variant == "prophet_fresh":
        return ProphetModel(strategy="fresh")
    if variant == "prophet_warm":
        return ProphetModel(strategy="warm")
    if variant == "xgboost_fresh":
        return XGBoostModel(strategy="fresh")
    if variant == "xgboost_incremental":
        return XGBoostModel(strategy="incremental")
    if variant == "lightgbm_fresh":
        return LightGBMModel(strategy="fresh")
    if variant == "lightgbm_incremental":
        return LightGBMModel(strategy="incremental")
    raise ValueError(f"Unknown variant: {variant}")


def _variant_factory(variant: str) -> Callable[[], Any]:
    """Return a zero-arg factory for the given variant.

    Used by the backtester, which needs a fresh instance per
    iteration. Wraps _build_model in a lambda.

    Args:
        variant: One of ALL_VARIANTS.

    Returns:
        A callable returning a fresh ForecastModel.
    """
    return lambda: _build_model(variant)


# ============================================================
# TRAIN SUBCOMMAND
# ============================================================
async def _cmd_train(args: argparse.Namespace) -> int:
    """Train the requested model variants on the train partition.

    Loads features via fetch_training_frame_for_source with
    FeatureContext.TRAINING, builds an orchestrator, and retrains
    all requested variants. Saves each to
    {settings.model_save_dir}/{variant}.pkl.

    Returns:
        0 on success, 1 on failure.
    """
    start = time.monotonic()
    logger.info("=== train ===")

    variants = _parse_models(args.models)
    partition = FeaturePartition(args.partition)

    logger.info(
        f"Training {len(variants)} variant(s) from partition "
        f"'{partition.value}' for {args.hours}h"
    )

    # ---- 1. Fetch training data ----
    async with session_scope() as session:
        repo = PredictionRepository(session)
        training_frame = await repo.fetch_training_frame_for_source(
            hours=args.hours,
            context=FeatureContext.TRAINING,
            partition=partition,
        )

    if training_frame is None or training_frame.empty:
        logger.error("Training data is empty — aborting")
        return 1

    if len(training_frame) < MIN_TRAIN_ROWS:
        logger.error(
            f"Insufficient training data: {len(training_frame)} rows, "
            f"need at least {MIN_TRAIN_ROWS}"
        )
        return 1

    logger.info(
        f"Fetched {len(training_frame)} rows, "
        f"{len(training_frame.columns)} columns"
    )

    # ---- 2. Build registry (only requested variants) ----
    registry: Dict[str, Any] = {v: _build_model(v) for v in variants}

    # ---- 3. Retrain ----
    orchestrator = RetrainingOrchestrator(
        models=registry,
        model_save_dir=settings.model_save_dir,
    )
    results = orchestrator.retrain_all(data=training_frame)

    # ---- 4. Summarize ----
    succeeded = sum(1 for r in results.values() if r["status"] == "success")
    failed = len(results) - succeeded
    elapsed = time.monotonic() - start

    logger.info(
        f"train complete: {succeeded}/{len(results)} succeeded "
        f"in {elapsed:.2f}s"
    )

    if failed > 0:
        failed_names = [
            name for name, r in results.items() if r["status"] != "success"
        ]
        logger.error(f"Failed variants: {failed_names}")
        return 1

    return 0


# ============================================================
# BACKTEST SUBCOMMAND
# ============================================================
async def _cmd_backtest(args: argparse.Namespace) -> int:
    """Run walk-forward backtests and persist per-point metrics.

    Loads features via FeatureContext.TRAINING (walk-forward uses
    a training window), runs 12 (variant, horizon) backtests, and
    writes rows to prediction_performance.

    Returns:
        0 on success, 1 on failure.
    """
    start = time.monotonic()
    logger.info("=== backtest ===")

    variants = _parse_models(args.models)
    horizons = _parse_horizons(args.horizon)
    partition = FeaturePartition(args.partition)

    logger.info(
        f"Backtesting {len(variants)} variant(s) × "
        f"{len(horizons)} horizon(s) = "
        f"{len(variants) * len(horizons)} pairs "
        f"from partition '{partition.value}' for {args.hours}h"
    )

    # ---- 1. Fetch training data ----
    async with session_scope() as session:
        repo = PredictionRepository(session)
        training_frame = await repo.fetch_training_frame_for_source(
            hours=args.hours,
            context=FeatureContext.TRAINING,
            partition=partition,
        )

    if training_frame is None or training_frame.empty:
        logger.error("Training data is empty — aborting")
        return 1

    logger.info(
        f"Fetched {len(training_frame)} rows, "
        f"{len(training_frame.columns)} columns"
    )

    # ---- 2. Iterate over (variant, horizon) pairs ----
    succeeded = 0
    failed = 0
    total_rows_written = 0

    async with session_scope() as session:
        perf_repo = PerformanceRepository(session)

        for variant in variants:
            for horizon_label, horizon_hours in horizons:
                key = f"{variant}_{horizon_label}"
                logger.info(f"Backtesting {key}")

                try:
                    bt = WalkForwardBacktester(
                        horizon=horizon_label,
                        horizon_hours=horizon_hours,
                        iterations=args.iterations,
                        full_trajectory=args.full_trajectory,
                    )

                    factory = _variant_factory(variant)
                    bt_result = await bt.run(
                        model_name=variant,
                        build_model=factory,
                        training_data=training_frame,
                        actuals=training_frame,
                    )

                    if not bt_result.succeeded:
                        raise RuntimeError(
                            f"Backtest failed: {bt_result.error}"
                        )

                    rows = _result_to_rows(bt_result)

                    if args.dry_run:
                        written = len(rows)
                        logger.info(
                            f"[dry-run] would write {written} rows for {key}"
                        )
                    else:
                        written = await perf_repo.save_performance_rows(rows)

                    logger.info(
                        f"Backtest {key} ok: "
                        f"MAE={bt_result.mae:.2f}, "
                        f"RMSE={bt_result.rmse:.2f}, "
                        f"MAPE={bt_result.mape:.2f}%, "
                        f"DA={bt_result.directional_accuracy:.1f}%, "
                        f"{written} rows written"
                    )
                    succeeded += 1
                    total_rows_written += written

                except Exception as e:
                    logger.error(f"Backtest {key} failed: {e}", exc_info=True)
                    failed += 1

    elapsed = time.monotonic() - start
    logger.info(
        f"backtest complete: {succeeded}/{succeeded + failed} pairs "
        f"succeeded, {total_rows_written} rows written "
        f"in {elapsed:.2f}s"
    )

    if succeeded == 0:
        return 1
    return 0


def _result_to_rows(result: BacktestResult) -> List[PerformanceRow]:
    """Convert a BacktestResult to PerformanceRow instances.

    Mirrors the same conversion the scheduled backtest job uses,
    so the CLI and the scheduler write identical rows.

    Args:
        result: The BacktestResult to convert.

    Returns:
        List of PerformanceRow instances.
    """
    rows: List[PerformanceRow] = []

    for it in result.iteration_results:
        if it.error is not None:
            continue

        actuals = [actual for _, _, actual in it.matched_data]
        market_condition = classify_market_condition_safe(actuals)

        for forecast_ts, predicted, actual in it.matched_data:
            rows.append(
                PerformanceRow(
                    horizon=result.horizon,
                    model_name=result.model_name,
                    model_version="1.0.0",
                    forecast_date=forecast_ts,
                    predicted_price=predicted,
                    actual_price=actual,
                    mae=it.mae,
                    rmse=it.rmse,
                    mape=it.mape,
                    market_condition=market_condition,
                    prediction_id=None,
                )
            )

    return rows


# ============================================================
# PREDICT SUBCOMMAND
# ============================================================
async def _cmd_predict(args: argparse.Namespace) -> int:
    """Generate predictions for trained models and store them.

    For each (variant, horizon), loads the trained model from
    disk, builds a PredictionGenerator with
    FeatureContext.PREDICTION, and calls generate(). Writes rows
    to btc_predictions.

    Returns:
        0 on success, 1 on failure.
    """
    start = time.monotonic()
    logger.info("=== predict ===")

    variants = _parse_models(args.models)
    horizons = _parse_horizons(args.horizon)
    partition = FeaturePartition(args.partition)

    logger.info(
        f"Predicting with {len(variants)} variant(s) × "
        f"{len(horizons)} horizon(s) = "
        f"{len(variants) * len(horizons)} runs "
        f"from partition '{partition.value}' for {args.hours}h "
        f"at confidence {args.confidence}"
    )

    succeeded = 0
    failed = 0
    total_rows_saved = 0

    for variant in variants:
        for horizon_label, horizon_hours in horizons:
            key = f"{variant}_{horizon_label}"
            logger.info(f"Predicting {key}")

            try:
                # ---- 1. Load trained model from disk ----
                model = _build_model(variant)
                model_path = f"{settings.model_save_dir}/{variant}.pkl"
                model.load(model_path)

                if not model.is_model_trained():
                    raise RuntimeError(
                        f"Model '{variant}' loaded but not marked as trained"
                    )

                # ---- 2. Generate predictions ----
                async with session_scope() as session:
                    repo = PredictionRepository(session)
                    generator = PredictionGenerator(
                        model=model,
                        repository=repo,
                        horizon=horizon_label,
                        horizon_hours=horizon_hours,
                        confidence=args.confidence,
                        history_hours=args.hours,
                        history_source=FeatureContext.PREDICTION,
                    )

                    if args.dry_run:
                        # We can't easily intercept save_predictions here,
                        # so we skip the generator and log the intent.
                        logger.info(
                            f"[dry-run] would generate {horizon_hours} "
                            f"predictions for {key}"
                        )
                        succeeded += 1
                        continue

                    result = await generator.generate()

                if not result.succeeded:
                    raise RuntimeError(
                        f"Prediction failed: {result.error}"
                    )

                logger.info(
                    f"Predict {key} ok: "
                    f"{result.rows_saved} rows saved"
                )
                succeeded += 1
                total_rows_saved += result.rows_saved

            except FileNotFoundError:
                logger.warning(
                    f"Model file missing for {variant} — "
                    f"run 'train' first"
                )
                failed += 1
            except Exception as e:
                logger.error(f"Predict {key} failed: {e}", exc_info=True)
                failed += 1

    elapsed = time.monotonic() - start
    logger.info(
        f"predict complete: {succeeded}/{succeeded + failed} "
        f"runs succeeded, {total_rows_saved} rows saved "
        f"in {elapsed:.2f}s"
    )

    if succeeded == 0:
        return 1
    return 0


# ============================================================
# RUN SUBCOMMAND
# ============================================================
async def _cmd_run(args: argparse.Namespace) -> int:
    """Run train → backtest → predict in sequence.

    Each step inherits the same flags from the parent command.
    Fails fast: if train fails, backtest and predict are skipped.

    Returns:
        0 on success, 1 on failure.
    """
    logger.info("=== run: train → backtest → predict ===")

    # ---- 1. Train ----
    rc = await _cmd_train(args)
    if rc != 0:
        logger.error("train failed — aborting run")
        return rc

    # ---- 2. Backtest ----
    rc = await _cmd_backtest(args)
    if rc != 0:
        logger.error("backtest failed — aborting run")
        return rc

    # ---- 3. Predict ----
    rc = await _cmd_predict(args)
    if rc != 0:
        logger.error("predict failed")
        return rc

    logger.info("run complete: all steps succeeded")
    return 0


# ============================================================
# ARGUMENT PARSER
# ============================================================
def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add flags common to all subcommands."""
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help=(
            "Comma-separated variant names. "
            f"Default: all 6 ({','.join(ALL_VARIANTS)})."
        ),
    )
    parser.add_argument(
        "--horizon",
        type=str,
        default="both",
        choices=["24h", "7d", "both"],
        help="Which horizon(s) to process. Default: both.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform reads but skip database writes.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override the configured log level for this run.",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="python -m app.ai.pipeline",
        description=(
            "Manual ML pipeline CLI for the AI Service. "
            "Shares the same ML flow as the live scheduler, "
            "but runs on demand against the file-based feature source."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- train ----
    p_train = subparsers.add_parser(
        "train",
        help="Train the requested model variants.",
    )
    _add_common_args(p_train)
    p_train.add_argument(
        "--partition",
        type=str,
        default="train",
        choices=["train", "val", "test"],
        help="Feature partition to train on. Default: train.",
    )
    p_train.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_TRAIN_HOURS,
        help=f"History length in hours. Default: {DEFAULT_TRAIN_HOURS}.",
    )

    # ---- backtest ----
    p_bt = subparsers.add_parser(
        "backtest",
        help="Run walk-forward backtests and persist metrics.",
    )
    _add_common_args(p_bt)
    p_bt.add_argument(
        "--partition",
        type=str,
        default="train",
        choices=["train", "val"],
        help="Feature partition to backtest over. Default: train.",
    )
    p_bt.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_BACKTEST_HOURS,
        help=f"History length in hours. Default: {DEFAULT_BACKTEST_HOURS}.",
    )
    p_bt.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Walk-forward iterations. Default: settings.backtest_iterations.",
    )
    p_bt.add_argument(
        "--full-trajectory",
        dest="full_trajectory",
        action="store_true",
        default=None,
        help=(
            "Evaluate the full forecast trajectory per iteration. "
            "Default: settings.backtest_full_trajectory."
        ),
    )

    # ---- predict ----
    p_pr = subparsers.add_parser(
        "predict",
        help="Generate predictions from trained models.",
    )
    _add_common_args(p_pr)
    p_pr.add_argument(
        "--partition",
        type=str,
        default="live_frontier",
        choices=["live_frontier", "test"],
        help="Feature partition for history. Default: live_frontier.",
    )
    p_pr.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_PREDICT_HOURS,
        help=f"History length in hours. Default: {DEFAULT_PREDICT_HOURS}.",
    )
    p_pr.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        choices=[0.70, 0.85, 0.95],
        help="Confidence level for stored bounds. Default: 0.85.",
    )

    # ---- run ----
    p_run = subparsers.add_parser(
        "run",
        help="Run train → backtest → predict in sequence.",
    )
    _add_common_args(p_run)
    p_run.add_argument(
        "--partition",
        type=str,
        default="train",
        choices=["train", "val"],
        help="Feature partition for train and backtest. Default: train.",
    )
    p_run.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_TRAIN_HOURS,
        help=(
            f"History length in hours for training. "
            f"Default: {DEFAULT_TRAIN_HOURS}."
        ),
    )
    p_run.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Walk-forward iterations. Default: settings.backtest_iterations.",
    )
    p_run.add_argument(
        "--full-trajectory",
        dest="full_trajectory",
        action="store_true",
        default=None,
        help="Evaluate the full forecast trajectory per iteration.",
    )
    p_run.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        choices=[0.70, 0.85, 0.95],
        help="Confidence level for stored bounds. Default: 0.85.",
    )

    return parser


# ============================================================
# ENTRY POINT
# ============================================================
async def _async_main(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate subcommand and dispose the engine."""
    try:
        if args.command == "train":
            return await _cmd_train(args)
        if args.command == "backtest":
            return await _cmd_backtest(args)
        if args.command == "predict":
            return await _cmd_predict(args)
        if args.command == "run":
            return await _cmd_run(args)
        logger.error(f"Unknown command: {args.command}")
        return 2
    finally:
        await dispose_engine()


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (for tests). If None, uses
            sys.argv.

    Returns:
        Exit code.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    _configure_logging(args.log_level)

    logger.info(
        f"pipeline starting (command='{args.command}', "
        f"models='{args.models or 'all'}', "
        f"horizon='{args.horizon}', "
        f"dry_run={args.dry_run})"
    )

    try:
        return asyncio.run(_async_main(args))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())