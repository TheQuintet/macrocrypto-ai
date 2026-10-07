"""
CLI for raw hourly backfill (Chat 4, C4-1).

Pulls hourly candles for BTC (Binance) and/or gold (Yahoo) into
raw tables. Idempotent: re-running over the same range inserts
nothing new on the second run.

Usage
-----
    python -m app.scripts.run_hourly_backfills --btc
    python -m app.scripts.run_hourly_backfills --gold
    python -m app.scripts.run_hourly_backfills --all
    python -m app.scripts.run_hourly_backfills --btc --days 30
    python -m app.scripts.run_hourly_backfills --btc \\
        --start 2024-01-01 --end 2024-12-31
    python -m app.scripts.run_hourly_backfills --gold --days 7

Default range
-------------
If neither --days nor --start is given, --days 30 is used,
matching the Chat 4 addendum and Chat 3's --days default.

Exit codes
----------
    0   success
    2   invalid args (bad datetime, bad range, unknown source)
    3   database or network error during backfill

Scope
-----
This CLI is CLI-only by design (Chat 4 Decision 1). It is not
wired into the FastAPI lifespan. See
docs/data-service-hourly-runbook.md for the recommended
operational cadence.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.hourly_backfill_service import (
    HOURLY_BACKFILL_SOURCES,
    run_hourly_backfill,
)


logger = logging.getLogger(__name__)


DEFAULT_DAYS = 30


# ============================================================
# PARSING HELPERS
# ============================================================


def _parse_utc_datetime(raw: str) -> datetime:
    """
    Parse an ISO-8601 string into a timezone-aware UTC datetime.

    Accepts 'YYYY-MM-DD' and 'YYYY-MM-DDTHH:MM:SS'. If the input
    carries no timezone, UTC is assumed.
    """
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid datetime '{raw}': {exc}"
        ) from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _floor_to_hour(dt: datetime) -> datetime:
    """Truncate to the start of the UTC hour."""
    return dt.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


def _resolve_range(
    args: argparse.Namespace,
) -> tuple[Optional[datetime], Optional[datetime], Optional[int]]:
    """
    Return (start, end, days) for run_hourly_backfill.

    Exactly one of {days, start} is set. If neither, days defaults
    to DEFAULT_DAYS. The service itself clamps end to the last
    completed hour and floors both bounds.
    """
    if args.days is not None:
        if args.days <= 0:
            raise ValueError("--days must be a positive integer")
        return None, None, args.days

    if args.start is None:
        # Neither given: default to --days 30.
        return None, None, DEFAULT_DAYS

    start = _parse_utc_datetime(args.start)

    if args.end is not None:
        end = _parse_utc_datetime(args.end)
    else:
        end = datetime.now(timezone.utc)

    if _floor_to_hour(end) <= _floor_to_hour(start):
        raise ValueError(
            f"--end ({end.isoformat()}) must be after "
            f"--start ({start.isoformat()})"
        )

    return start, end, None


def _selected_keys(args: argparse.Namespace) -> list[str]:
    """Return the source keys selected by the CLI flags."""
    if args.all:
        return list(HOURLY_BACKFILL_SOURCES.keys())
    keys: list[str] = []
    if args.btc:
        keys.append("btc_hourly")
    if args.gold:
        keys.append("gold_hourly")
    return keys


# ============================================================
# ARGPARSE
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_hourly_backfills",
        description=(
            "Backfill raw hourly data from external providers "
            "(Binance for BTC, Yahoo for gold)."
        ),
    )

    # Exactly one source selector.
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--btc",
        action="store_true",
        help="Backfill raw btc_prices with hourly Binance klines.",
    )
    source_group.add_argument(
        "--gold",
        action="store_true",
        help=(
            "Backfill raw macro_indicators (indicator_name="
            "'gold_spot') with hourly Yahoo data."
        ),
    )
    source_group.add_argument(
        "--all",
        action="store_true",
        help="Run every registered hourly backfill source.",
    )

    # Range: --days and --start are mutually exclusive.
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument(
        "--days",
        type=int,
        default=None,
        help=(
            f"Backfill the last N days. Defaults to {DEFAULT_DAYS} "
            "if --start is not given. Mutually exclusive with "
            "--start/--end."
        ),
    )
    range_group.add_argument(
        "--start",
        type=str,
        default=None,
        help="Inclusive start, ISO-8601 (e.g. 2024-01-01).",
    )

    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help=(
            "Exclusive end, ISO-8601. Defaults to the current hour "
            "if omitted. Only meaningful with --start."
        ),
    )

    return parser


# ============================================================
# ENTRY POINT
# ============================================================


async def _run(args: argparse.Namespace) -> int:
    keys = _selected_keys(args)
    if not keys:
        # argparse should prevent this, but stay defensive.
        logger.error("[CLI] no source selected")
        return 2

    start, end, days = _resolve_range(args)

    range_desc = (
        f"days={days}" if days is not None
        else f"{start.isoformat()} -> {end.isoformat()}"
    )

    logger.info(
        "[CLI] hourly backfill: sources=%s range=%s",
        ",".join(keys), range_desc,
    )

    try:
        results = await run_hourly_backfill(
            keys, start=start, end=end, days=days,
        )
    except ValueError as exc:
        logger.error("[CLI] %s", exc)
        return 2
    except Exception:
        logger.exception("[CLI] hourly backfill failed")
        return 3

    total = 0
    for key, written in results.items():
        logger.info(
            "[CLI] %s: %d row(s) persisted", key, written,
        )
        total += written

    logger.info("[CLI] hourly backfill complete: %d row(s) total", total)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return asyncio.run(_run(args))
    except KeyboardInterrupt:
        logger.warning("[CLI] interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())