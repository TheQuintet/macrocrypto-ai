"""Manual pipeline CLI for the AI Service.

Runs the full scheduler flow — ML jobs plus analytics jobs —
on demand, in a sandboxed environment. Every write goes to
CLI-isolated targets:

    - btc_predictions_cli
    - prediction_performance_cli
    - threshold_breaches_cli
    - model_performance_cli
    - btc_macro_correlation_cli
    - historical_event_impacts_cli
    - cli_data/models/
    - cli_data/exports/

Production tables and paths are never touched.

Isolation is activated by setting CLI_MODE=true before importing
the rest of the application. The CLI does this automatically at
startup, so the caller doesn't need to remember to set it.

Subcommands:
    train           Train the 6 ML model variants.
    backtest        Run walk-forward backtests (12 pairs).
    predict         Generate predictions (both horizons).
    correlation     Compute BTC-vs-macro correlations.
    event-impact    Recompute event reactions.
    export-cleanup  Delete expired export files.
    run             Run all six above, in sequence.
    simulate        Replay analytics jobs for N historical days.

Usage:
    python -m app.cli.pipeline train
    python -m app.cli.pipeline backtest --horizon 24h
    python -m app.cli.pipeline predict --confidence 0.85
    python -m app.cli.pipeline correlation
    python -m app.cli.pipeline event-impact
    python -m app.cli.pipeline export-cleanup
    python -m app.cli.pipeline run
    python -m app.cli.pipeline simulate --days 30 \
        --jobs correlation,event-impact --end-date 2024-12-09

Exit codes:
    0 — success
    1 — one or more steps failed
    2 — CLI argument error

Design:
    The CLI invokes the same job functions the scheduler uses
    (daily_retrain_job, daily_backtest_job, etc.). The routing
    to CLI tables happens transparently inside the repositories,
    because they read settings.cli_mode. This means:

        - No duplicated ML or analytics logic.
        - The scheduler and the CLI always produce the same shape
          of output — they just write to different tables.
        - A single implementation is tested by both paths.
"""

# ============================================================
# ACTIVATE CLI MODE BEFORE ANY OTHER IMPORTS
# ============================================================
# The rest of the app imports `settings` at module load time.
# We must set CLI_MODE in the environment BEFORE that happens,
# so that when `settings` is instantiated, `cli_mode` is True.
#
# This is the first executable statement in the module.
import os

os.environ["CLI_MODE"] = "true"


# ============================================================
# NOW SAFE TO IMPORT THE REST
# ============================================================
import argparse
import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.config import settings
from app.database.engine import dispose_engine

# Job functions — reused from the scheduler module.
from app.scheduler.jobs import (
    daily_7d_prediction_job,
    daily_backtest_job,
    daily_correlation_job,
    daily_event_impact_update_job,
    daily_export_cleanup_job,
    daily_retrain_job,
    hourly_prediction_job,
)


logger = logging.getLogger("app.cli.pipeline")


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

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


# ============================================================
# LOGGING
# ============================================================
def _configure_logging(level: Optional[str] = None) -> None:
    """Configure root logging for the CLI run.

    Called once after argument parsing. The CLI runs in a
    dedicated process, so it's safe to use `force=True` to
    reset any prior logging configuration.
    """
    effective_level = (level or settings.log_level).upper()
    logging.basicConfig(
        level=effective_level,
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        force=True,
    )


# ============================================================
# HELPERS
# ============================================================
def _print_banner(command: str) -> None:
    """Print a banner showing CLI mode is active and where writes go."""
    logger.info("=" * 70)
    logger.info(f"CLI pipeline: {command}")
    logger.info(f"  CLI_MODE          = {settings.cli_mode}")
    logger.info(f"  feature_source    = {settings.feature_source}")
    logger.info(f"  model_save_dir    = {settings.effective_model_save_dir}")
    logger.info(
        f"  backtest_model_dir= {settings.effective_backtest_model_dir}"
    )
    logger.info(f"  exports_dir       = {settings.export_storage_dir_path}")
    logger.info("=" * 70)


def _result_ok(result: Any) -> bool:
    """Return True if a job's returned summary indicates success.

    Jobs return dicts with varying keys. We look for common failure
    markers:

        - `error` is not None
        - `succeeded` is False
        - The job raised (handled by the caller)

    Otherwise assume success.
    """
    if not isinstance(result, dict):
        # Job returned something else — assume success.
        return True

    if result.get("error") is not None:
        return False

    if result.get("succeeded") is False:
        return False

    return True


async def _run_job(
    name: str,
    coro_factory,
    *,
    dry_run: bool = False,
) -> Tuple[bool, Any, float]:
    """Run one job function and capture its outcome.

    Args:
        name: Human-readable job name for logging.
        coro_factory: A zero-arg callable that returns the job's
            coroutine. Using a factory (rather than a coroutine
            directly) lets us defer the coroutine's construction
            until we're inside the try block — if the factory
            raises, we still catch it.
        dry_run: If True, log the intent but skip execution.

    Returns:
        Tuple of (ok, result_or_error, elapsed_seconds).
    """
    start = time.monotonic()

    if dry_run:
        logger.info(f"[dry-run] would run: {name}")
        return True, {"dry_run": True, "job": name}, time.monotonic() - start

    logger.info(f"Running job: {name}")
    try:
        result = await coro_factory()
    except Exception as e:
        elapsed = time.monotonic() - start
        logger.error(
            f"Job {name!r} raised after {elapsed:.2f}s: {e}",
            exc_info=True,
        )
        return False, {"error": str(e)}, elapsed

    elapsed = time.monotonic() - start
    ok = _result_ok(result)
    logger.info(
        f"Job {name!r} {'succeeded' if ok else 'failed'} "
        f"in {elapsed:.2f}s"
    )
    return ok, result, elapsed


# ============================================================
# SUBCOMMAND: train
# ============================================================
async def _cmd_train(args: argparse.Namespace) -> int:
    """Train the 6 model variants."""
    _print_banner("train")

    ok, _, _ = await _run_job(
        "daily_retrain_job",
        daily_retrain_job,
        dry_run=args.dry_run,
    )
    return 0 if ok else 1


# ============================================================
# SUBCOMMAND: backtest
# ============================================================
async def _cmd_backtest(args: argparse.Namespace) -> int:
    """Run the daily backtest job."""
    _print_banner("backtest")

    ok, _, _ = await _run_job(
        "daily_backtest_job",
        daily_backtest_job,
        dry_run=args.dry_run,
    )
    return 0 if ok else 1


# ============================================================
# SUBCOMMAND: predict
# ============================================================
async def _cmd_predict(args: argparse.Namespace) -> int:
    """Run the prediction jobs (24h and 7d)."""
    _print_banner("predict")

    results: List[bool] = []

    # 24h prediction
    ok, _, _ = await _run_job(
        "hourly_prediction_job",
        hourly_prediction_job,
        dry_run=args.dry_run,
    )
    results.append(ok)

    # 7d prediction
    ok, _, _ = await _run_job(
        "daily_7d_prediction_job",
        daily_7d_prediction_job,
        dry_run=args.dry_run,
    )
    results.append(ok)

    return 0 if all(results) else 1


# ============================================================
# SUBCOMMAND: correlation
# ============================================================
async def _cmd_correlation(args: argparse.Namespace) -> int:
    """Run the correlation calculation."""
    _print_banner("correlation")

    ok, _, _ = await _run_job(
        "daily_correlation_job",
        daily_correlation_job,
        dry_run=args.dry_run,
    )
    return 0 if ok else 1


# ============================================================
# SUBCOMMAND: event-impact
# ============================================================
async def _cmd_event_impact(args: argparse.Namespace) -> int:
    """Run the event impact update."""
    _print_banner("event-impact")

    ok, _, _ = await _run_job(
        "daily_event_impact_update_job",
        daily_event_impact_update_job,
        dry_run=args.dry_run,
    )
    return 0 if ok else 1


# ============================================================
# SUBCOMMAND: export-cleanup
# ============================================================
async def _cmd_export_cleanup(args: argparse.Namespace) -> int:
    """Run the export cleanup."""
    _print_banner("export-cleanup")

    ok, _, _ = await _run_job(
        "daily_export_cleanup_job",
        daily_export_cleanup_job,
        dry_run=args.dry_run,
    )
    return 0 if ok else 1


# ============================================================
# SUBCOMMAND: run (full sequence)
# ============================================================
async def _cmd_run(args: argparse.Namespace) -> int:
    """Run the full daily cycle in order.

    Order: retrain → backtest → predict → correlation →
    event-impact → export-cleanup.

    Fails fast: if a step fails, subsequent steps are skipped.
    """
    _print_banner("run")

    steps = [
        ("daily_retrain_job", daily_retrain_job),
        ("daily_backtest_job", daily_backtest_job),
        ("hourly_prediction_job", hourly_prediction_job),
        ("daily_7d_prediction_job", daily_7d_prediction_job),
        ("daily_correlation_job", daily_correlation_job),
        ("daily_event_impact_update_job", daily_event_impact_update_job),
        ("daily_export_cleanup_job", daily_export_cleanup_job),
    ]

    start = time.monotonic()
    for name, job in steps:
        ok, _, _ = await _run_job(name, job, dry_run=args.dry_run)
        if not ok:
            logger.error(f"Step {name!r} failed — aborting run")
            return 1

    total = time.monotonic() - start
    logger.info(f"Full run complete in {total:.2f}s")
    return 0


# ============================================================
# SUBCOMMAND: simulate
# ============================================================
async def _cmd_simulate(args: argparse.Namespace) -> int:
    """Replay analytics jobs for N historical days.

    For each day D from (end_date - days + 1) to end_date:
        - Run each requested analytics job with as_of=D.

    The jobs accept an `as_of` parameter that overrides the
    "current time" they use internally. This lets a single CLI
    invocation produce N days of analytics output, as if the
    jobs had run once per day.

    The output lands in the CLI tables (or the production tables
    if CLI_MODE were somehow off — but the CLI always forces
    CLI_MODE=true). Query the *_cli tables afterward to see the
    time series.
    """
    _print_banner("simulate")

    # Parse the requested jobs.
    requested = [j.strip() for j in args.jobs.split(",") if j.strip()]
    if not requested:
        logger.error("No jobs specified with --jobs")
        return 1

    job_map = {
        "correlation": daily_correlation_job,
        "event-impact": daily_event_impact_update_job,
        "export-cleanup": daily_export_cleanup_job,
    }

    unknown = [j for j in requested if j not in job_map]
    if unknown:
        logger.error(
            f"Unknown job(s): {unknown}. "
            f"Valid: {list(job_map.keys())}"
        )
        return 1

    # Resolve the end date.
    if args.end_date:
        try:
            end_date = datetime.fromisoformat(args.end_date).replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            logger.error(
                f"Invalid --end-date: {args.end_date}. "
                f"Expected YYYY-MM-DD."
            )
            return 1
    else:
        end_date = datetime.now(timezone.utc)

    days = args.days
    if days <= 0:
        logger.error("--days must be positive")
        return 1

    logger.info(
        f"Simulating {days} day(s) ending {end_date.date()}, "
        f"jobs={requested}"
    )

    total_start = time.monotonic()
    day_results: List[Tuple[str, bool]] = []

    for day_offset in range(days):
        as_of = end_date - timedelta(days=days - 1 - day_offset)
        logger.info(
            f"--- Simulated day {day_offset + 1}/{days} "
            f"({as_of.date()}) ---"
        )

        for job_name in requested:
            job = job_map[job_name]
            ok, _, _ = await _run_job(
                f"{job_name} as_of={as_of.date()}",
                lambda j=job, a=as_of: j(as_of=a),
                dry_run=args.dry_run,
            )
            day_results.append((f"{job_name}/{as_of.date()}", ok))

    total_elapsed = time.monotonic() - total_start

    # Summary.
    total_runs = len(day_results)
    failures = sum(1 for _, ok in day_results if not ok)
    logger.info(
        f"Simulation complete: {total_runs - failures}/{total_runs} "
        f"runs succeeded in {total_elapsed:.2f}s"
    )

    if failures > 0:
        failed = [name for name, ok in day_results if not ok]
        logger.error(f"Failures: {failed}")
        return 1

    return 0


# ============================================================
# ARGUMENT PARSER
# ============================================================
def build_arg_parser() -> argparse.ArgumentParser:
    """Build the top-level parser with subcommands.

    Returns:
        Configured ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="python -m app.cli.pipeline",
        description=(
            "Manual pipeline CLI for the AI Service. Runs the full "
            "scheduler flow on demand, sandboxed to *_cli tables "
            "and the cli_data/ directory. Production data is never "
            "touched."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # ---- Common flag helper ----
    def _add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument(
            "--dry-run",
            action="store_true",
            help="Log the intent but do not execute.",
        )
        p.add_argument(
            "--log-level",
            type=str,
            default=None,
            choices=["DEBUG", "INFO", "WARNING", "ERROR"],
            help="Override the configured log level for this run.",
        )

    # ---- train ----
    p_train = subparsers.add_parser(
        "train", help="Train the 6 ML model variants."
    )
    _add_common(p_train)

    # ---- backtest ----
    p_bt = subparsers.add_parser(
        "backtest", help="Run walk-forward backtests."
    )
    _add_common(p_bt)

    # ---- predict ----
    p_pr = subparsers.add_parser(
        "predict", help="Generate predictions for both horizons."
    )
    _add_common(p_pr)

    # ---- correlation ----
    p_corr = subparsers.add_parser(
        "correlation", help="Compute BTC-vs-macro correlations."
    )
    _add_common(p_corr)

    # ---- event-impact ----
    p_ev = subparsers.add_parser(
        "event-impact", help="Recompute event reactions."
    )
    _add_common(p_ev)

    # ---- export-cleanup ----
    p_exp = subparsers.add_parser(
        "export-cleanup", help="Delete expired export files."
    )
    _add_common(p_exp)

    # ---- run ----
    p_run = subparsers.add_parser(
        "run", help="Run the full daily cycle in sequence."
    )
    _add_common(p_run)

    # ---- simulate ----
    p_sim = subparsers.add_parser(
        "simulate",
        help="Replay analytics jobs for N historical days.",
    )
    _add_common(p_sim)
    p_sim.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to simulate. Default: 7.",
    )
    p_sim.add_argument(
        "--jobs",
        type=str,
        default="correlation,event-impact",
        help=(
            "Comma-separated analytics jobs to run. "
            "Choices: correlation, event-impact, export-cleanup. "
            "Default: correlation,event-impact."
        ),
    )
    p_sim.add_argument(
        "--end-date",
        type=str,
        default=None,
        help=(
            "Last day of the simulation in YYYY-MM-DD format. "
            "Default: today (UTC)."
        ),
    )

    return parser


# ============================================================
# DISPATCH
# ============================================================
_SUBCOMMANDS = {
    "train": _cmd_train,
    "backtest": _cmd_backtest,
    "predict": _cmd_predict,
    "correlation": _cmd_correlation,
    "event-impact": _cmd_event_impact,
    "export-cleanup": _cmd_export_cleanup,
    "run": _cmd_run,
    "simulate": _cmd_simulate,
}


async def _async_main(args: argparse.Namespace) -> int:
    """Dispatch to the subcommand and dispose the DB engine."""
    handler = _SUBCOMMANDS.get(args.command)
    if handler is None:
        logger.error(f"Unknown command: {args.command}")
        return 2

    try:
        return await handler(args)
    finally:
        # Always dispose the engine so asyncpg connections are
        # closed cleanly before the process exits.
        await dispose_engine()


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (for tests). If None, uses
            sys.argv.

    Returns:
        Exit code.
    """
    # 1. Parse arguments FIRST so `--log-level` is available.
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # 2. Configure logging using the parsed level (or settings default).
    _configure_logging(args.log_level)

    # 3. Log the CLI activation (the actual env var was set at module
    #    import time, before `settings` was instantiated).
    logger.info(
        f"CLI mode active (CLI_MODE=true); "
        f"writes target *_cli tables and cli_data/ directory"
    )

    # 4. Run.
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