"""CLI entry point for 7-day prediction generation.

This script orchestrates one full prediction cycle for the 7d
horizon:
    1. Load a trained Prophet model from disk
    2. Open a database session
    3. Run PredictionGenerator
    4. Log the result and exit with a status code

Usage:
    # Default: load from models/prophet_7d.json and save to DB
    python -m app.prediction.generate_7d

    # Custom model path
    python -m app.prediction.generate_7d --model-path /path/to/model.json

    # Dry run (predict but do not write to DB)
    python -m app.prediction.generate_7d --dry-run

    # Custom confidence level
    python -m app.prediction.generate_7d --confidence 0.95

Exit codes:
    0 — success
    1 — failure (missing model, insufficient data, DB error, etc.)
    2 — CLI argument error (argparse default)

Designed to be called from:
    - A shell (`python -m app.prediction.generate_7d`)
    - A cron job (T2.5)
    - An APScheduler job (registered in Branch 18)
    - A container entrypoint
"""

import argparse
import asyncio
import logging
import sys
from typing import Optional

from app.ai.models.prophet_model import ProphetModel
from app.config import settings
from app.database.engine import dispose_engine, session_scope
from app.database.repositories.prediction_repository import (
    PredictionRepository,
)
from app.prediction.generator import PredictionGenerator

logger = logging.getLogger(__name__)


# ============================================================
# CLI ARGUMENTS
# ============================================================
def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="generate_7d",
        description=(
            "Generate 7-day BTC price predictions and save them "
            "to TimescaleDB."
        ),
    )

    parser.add_argument(
        "--model-path",
        type=str,
        default=settings.prophet_7d_model_path,
        help=(
            f"Path to the trained Prophet model file. "
            f"Default: {settings.prophet_7d_model_path}"
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Generate predictions but do not save them to the "
            "database. Useful for local testing."
        ),
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        choices=[0.70, 0.85, 0.95],
        help="Confidence level for stored bounds. Default: 0.85",
    )

    parser.add_argument(
        "--history-hours",
        type=int,
        default=2160,  # 90 days
        help=(
            "Number of hours of history to fetch from TimescaleDB. "
            "Default: 2160 (90 days)"
        ),
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help=(
            "Override the configured log level for this run. "
            "Default: use settings.log_level"
        ),
    )

    return parser


# ============================================================
# LOGGING SETUP
# ============================================================
def configure_logging(level: Optional[str] = None) -> None:
    """Configure logging for the CLI run.

    Args:
        level: Optional log level override. If None, uses
            settings.log_level.
    """
    effective_level = (level or settings.log_level).upper()

    logging.basicConfig(
        level=effective_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        force=True,
    )


# ============================================================
# MAIN
# ============================================================
async def run_generation(
    model_path: str,
    dry_run: bool,
    confidence: float,
    history_hours: int,
) -> bool:
    """Run one 7d prediction generation cycle.

    Args:
        model_path: Path to the trained Prophet model file.
        dry_run: If True, skip saving to the database.
        confidence: Confidence level for stored bounds.
        history_hours: Number of hours of history to fetch.

    Returns:
        True if generation succeeded, False otherwise.
    """
    # ---- 1. Load model ----
    logger.info(f"Loading Prophet model from '{model_path}'")
    model = ProphetModel(strategy="fresh")

    try:
        model.load(model_path)
    except FileNotFoundError:
        logger.error(
            f"Model file not found: '{model_path}'. "
            f"Train the model first (see RetrainingOrchestrator)."
        )
        return False
    except Exception as e:
        logger.error(
            f"Failed to load model from '{model_path}': {e}",
            exc_info=True,
        )
        return False

    logger.info(
        f"Model loaded: name='{model.get_name()}', "
        f"version='{model.get_version()}', "
        f"trained={model.is_model_trained()}"
    )

    # ---- 2. Open session and run generator ----
    async with session_scope() as session:
        repository = PredictionRepository(session)

        if dry_run:
            # Wrap the repo so save_predictions is a no-op
            repository = _DryRunRepositoryWrapper(repository)
            logger.info("Dry-run mode: predictions will NOT be saved")

        generator = PredictionGenerator(
            model=model,
            repository=repository,
            horizon="7d",
            horizon_hours=168,  # 7 * 24
            confidence=confidence,
            history_hours=history_hours,
        )

        logger.info(f"Starting generation: {generator!r}")
        result = await generator.generate()

    # ---- 3. Report ----
    if result.succeeded:
        logger.info(
            f"SUCCESS: {result.rows_generated} predictions generated, "
            f"{result.rows_saved} saved in {result.elapsed_seconds:.3f}s"
        )
        return True

    logger.error(
        f"FAILURE: {result.error} "
        f"(after {result.elapsed_seconds:.3f}s)"
    )
    return False


# ============================================================
# DRY-RUN WRAPPER
# ============================================================
class _DryRunRepositoryWrapper:
    """Repository wrapper that swallows writes during --dry-run.

    Delegates all read methods to the wrapped repository, but
    replaces save_predictions() with a no-op that returns 0.
    """

    def __init__(self, inner: PredictionRepository) -> None:
        """Initialize the wrapper.

        Args:
            inner: The real repository to wrap.
        """
        self._inner = inner

    async def fetch_training_frame(self, hours: int):
        """Delegate to the wrapped repository."""
        return await self._inner.fetch_training_frame(hours=hours)

    async def fetch_recent_btc_data(self, hours: int):
        """Delegate to the wrapped repository."""
        return await self._inner.fetch_recent_btc_data(hours=hours)

    async def fetch_recent_macro_data(self, hours: int):
        """Delegate to the wrapped repository."""
        return await self._inner.fetch_recent_macro_data(hours=hours)

    async def save_predictions(self, rows):
        """No-op: return 0 without touching the database."""
        logger.info(
            f"Dry-run: would have saved {len(rows)} prediction rows"
        )
        return 0


# ============================================================
# ENTRY POINT
# ============================================================
async def async_main(args: argparse.Namespace) -> int:
    """Async main — runs the generation and disposes the engine.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        success = await run_generation(
            model_path=args.model_path,
            dry_run=args.dry_run,
            confidence=args.confidence,
            history_hours=args.history_hours,
        )
        return 0 if success else 1
    finally:
        await dispose_engine()


def main(argv: Optional[list] = None) -> int:
    """CLI entry point.

    Args:
        argv: Optional argument list (for testing). If None, uses
            sys.argv.

    Returns:
        Exit code.
    """
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    logger.info(
        f"generate_7d starting "
        f"(model_path='{args.model_path}', "
        f"dry_run={args.dry_run}, "
        f"confidence={args.confidence})"
    )

    try:
        return asyncio.run(async_main(args))
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())