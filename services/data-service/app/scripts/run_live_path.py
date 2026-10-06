"""
CLI entry point for the data-service live path.

Usage
-----
    python -m app.scripts.run_live_path --backfill
    python -m app.scripts.run_live_path --btc-hourly
    python -m app.scripts.run_live_path --macro-hourly
    python -m app.scripts.run_live_path --features-db
    python -m app.scripts.run_live_path --all

Scope (Phase A, Chat 2)
-----------------------
Only --backfill is implemented. It calls
app.services.backfill_service.check_and_backfill(force=True).

The other subcommands are Phase B (hourly pipeline). They print
a "not yet implemented" message and exit 0 so that --all is
usable end-to-end without pretending unimplemented work succeeded.

Design notes
------------
- CLI calls the same service methods the scheduler will call, when
  a scheduler is added. No business logic lives here (D2).
- run_backfills.py remains the top-level manual script; this CLI
  is an additive trigger, not a replacement.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Callable, Awaitable

from app.services.backfill_service import (
    check_and_backfill,
    get_backfill_status,
)


logger = logging.getLogger(__name__)


# ============================================================
# SUBCOMMAND IMPLEMENTATIONS
# ============================================================


async def _run_backfill() -> int:
    """
    Full re-pull of every registered source (idempotent).

    Uses force=True because a human invoking --backfill wants the
    freshest data, not a staleness-checked subset.
    """
    await check_and_backfill(force=True)

    status = get_backfill_status()
    if status.state == "failed":
        logger.error(
            "[CLI] backfill failed on source=%s: %s",
            status.current_source,
            status.error,
        )
        return 1

    logger.info(
        "[CLI] backfill %s (ran=%d, skipped=%d)",
        status.state,
        status.sources_run,
        status.sources_skipped,
    )
    return 0


async def _run_btc_hourly() -> int:
    _not_implemented("--btc-hourly", "hourly BTC backfill (Phase B)")
    return 0


async def _run_macro_hourly() -> int:
    _not_implemented("--macro-hourly", "hourly macro backfill (Phase B)")
    return 0


async def _run_features_db() -> int:
    _not_implemented("--features-db", "features_db writer (Phase B)")
    return 0


async def _run_all() -> int:
    """
    Run everything in order. Phase A: backfill is real, the other
    three steps are stubs.
    """
    rc = await _run_backfill()
    if rc != 0:
        return rc

    await _run_btc_hourly()
    await _run_macro_hourly()
    await _run_features_db()
    return 0


def _not_implemented(flag: str, description: str) -> None:
    print(
        f"{flag}: {description} is not yet implemented. "
        f"This is Phase B work (see data-service-live-path-design.md)."
    )


# ============================================================
# ARGPARSE
# ============================================================


SUBCOMMANDS: dict[str, tuple[str, Callable[[], Awaitable[int]]]] = {
    "--backfill":     ("Run the daily-resolution backfill for all sources", _run_backfill),
    "--btc-hourly":   ("Backfill hourly BTC klines (Phase B)",              _run_btc_hourly),
    "--macro-hourly": ("Backfill hourly macro series (Phase B)",            _run_macro_hourly),
    "--features-db":  ("Write the features_db hourly table (Phase B)",      _run_features_db),
    "--all":          ("Run every step in order",                            _run_all),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_live_path",
        description=(
            "Manually trigger data-service live-path steps. "
            "Phase A implements --backfill; other flags are Phase B stubs."
        ),
    )

    group = parser.add_mutually_exclusive_group(required=True)
    for flag, (help_text, _) in SUBCOMMANDS.items():
        group.add_argument(flag, action="store_true", help=help_text)

    return parser


# ============================================================
# ENTRY POINT
# ============================================================


async def _dispatch(args: argparse.Namespace) -> int:
    for flag, (_, handler) in SUBCOMMANDS.items():
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            return await handler()
    return 2  # unreachable: argparse enforces required=True


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return asyncio.run(_dispatch(args))
    except KeyboardInterrupt:
        logger.warning("[CLI] interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())