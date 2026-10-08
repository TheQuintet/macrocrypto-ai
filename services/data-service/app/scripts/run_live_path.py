"""
CLI entry point for the data-service live path.

Usage
-----
    python -m app.scripts.run_live_path --backfill
    python -m app.scripts.run_live_path --btc-hourly
    python -m app.scripts.run_live_path --btc-hourly-backfill --days 30
    python -m app.scripts.run_live_path --btc-hourly-backfill \
        --start 2024-01-01 --end 2024-12-31
    python -m app.scripts.run_live_path --btc-hourly-backfill --verify --days 30
    python -m app.scripts.run_live_path --btc-hourly-backfill --dry-run --days 30
    python -m app.scripts.run_live_path --macro-hourly
    python -m app.scripts.run_live_path --features-db
    python -m app.scripts.run_live_path --all

Scope
-----
Phase A (Chat 2):
    --backfill is the daily-resolution backfill.

Phase B (Chat 3):
    --btc-hourly writes btc_prices_hourly for the just-completed hour.
    --btc-hourly-backfill materializes a range of hours from raw data.

Phase B (Chat 4, still stubbed here):
    --macro-hourly, --features-db.

Design notes
------------
- CLI calls the same service methods the scheduler calls. No
  business logic lives here (D2).
- run_backfills.py remains the top-level manual script; this CLI
  is an additive trigger, not a replacement.
- All backfill commands are idempotent (ON CONFLICT DO NOTHING),
  so re-running is safe.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from app.services.backfill_service import (
    check_and_backfill,
    get_backfill_status,
)


logger = logging.getLogger(__name__)


# ============================================================
# BACKFILL RANGE HELPERS
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


def _resolve_backfill_range(
    args: argparse.Namespace,
) -> tuple[datetime, datetime]:
    """
    Resolve --days or --start/--end into a (start, end) tuple.

    Both are snapped to hour boundaries.

    --days N        -> [now - N days, now], both floored to the hour
    --start / --end -> [start, end), both floored to the hour
    Neither         -> defaults to --days 30 (enforced by parser)

    The end is not clamped here; the service clamps to the last
    completed hour and warns.
    """
    now = _floor_to_hour(datetime.now(timezone.utc))

    if args.days is not None:
        if args.days <= 0:
            raise ValueError("--days must be a positive integer")
        end = now
        start = end - timedelta(days=args.days)
        return start, end

    if args.start is None:
        raise ValueError(
            "Either --days or --start must be provided"
        )

    start = _floor_to_hour(_parse_utc_datetime(args.start))

    if args.end is not None:
        end = _floor_to_hour(_parse_utc_datetime(args.end))
    else:
        end = now

    if end <= start:
        raise ValueError(
            f"--end ({end.isoformat()}) must be after "
            f"--start ({start.isoformat()})"
        )

    return start, end


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
    """
    Materialize btc_prices_hourly for the previous completed hour.
    """
    from app.database.session import SessionLocal
    from app.services.hourly_btc_prices_service import (
        HourlyBTCPricesService,
    )

    now = datetime.now(timezone.utc)
    target_hour = now.replace(
        minute=0, second=0, microsecond=0
    ) - timedelta(hours=1)

    db = SessionLocal()
    try:
        service = HourlyBTCPricesService(db)
        wrote = service.write_hour(target_hour)
        if wrote:
            logger.info(
                "[CLI] wrote btc_prices_hourly row for %s",
                target_hour.isoformat(),
            )
        else:
            logger.info(
                "[CLI] skipped btc_prices_hourly %s (no raw ticks)",
                target_hour.isoformat(),
            )
        return 0
    finally:
        db.close()


async def _run_btc_hourly_backfill(
    args: argparse.Namespace,
) -> int:
    """
    Materialize btc_prices_hourly for a range of hours.
    """
    from app.database.session import SessionLocal
    from app.services.hourly_btc_prices_service import (
        HourlyBTCPricesService,
    )

    start, end = _resolve_backfill_range(args)

    logger.info(
        "[CLI] btc-hourly-backfill range: %s -> %s%s%s",
        start.isoformat(),
        end.isoformat(),
        " (dry-run)" if args.dry_run else "",
        " (verify)" if args.verify else "",
    )

    db = SessionLocal()
    try:
        service = HourlyBTCPricesService(db)
        summary = service.backfill(
            start=start,
            end=end,
            dry_run=args.dry_run,
            verify_only=args.verify,
        )
    finally:
        db.close()

    if args.verify:
        missing = summary.get("missing", [])
        if not missing:
            logger.info("[CLI] verify: no gaps in range")
            return 0
        logger.warning(
            "[CLI] verify: %d missing hour(s) in range",
            len(missing),
        )
        for h in missing[:20]:
            print(f"  missing: {h.isoformat()}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
        return 1

    logger.info(
        "[CLI] btc-hourly-backfill %s: expected=%d written=%d "
        "skipped=%d already=%d",
        "DRY-RUN" if args.dry_run else "done",
        summary["expected_hours"],
        summary["written"],
        summary["skipped_no_data"],
        summary["already_present"],
    )
    return 0


async def _run_macro_hourly() -> int:
    _not_implemented("--macro-hourly", "hourly macro backfill (Phase B)")
    return 0


async def _run_features_db() -> int:
    _not_implemented("--features-db", "features_db writer (Phase B)")
    return 0


async def _run_all() -> int:
    """
    Run everything in order. --backfill is real; --btc-hourly is
    now real (Phase B2). The rest are still stubs.
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


SUBCOMMANDS: dict[
    str,
    tuple[str, Callable[..., Awaitable[int]]],
] = {
    "--backfill": (
        "Run the daily-resolution backfill for all sources",
        _run_backfill,
    ),
    "--btc-hourly": (
        "Write btc_prices_hourly for the last completed hour",
        _run_btc_hourly,
    ),
    "--btc-hourly-backfill": (
        "Materialize btc_prices_hourly over a range of hours",
        _run_btc_hourly_backfill,
    ),
    "--macro-hourly": (
        "Backfill hourly macro series (Phase B)",
        _run_macro_hourly,
    ),
    "--features-db": (
        "Write the features_db hourly table (Phase B)",
        _run_features_db,
    ),
    "--all": (
        "Run every step in order",
        _run_all,
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_live_path",
        description=(
            "Manually trigger data-service live-path steps. "
            "Supports the daily backfill and the hourly BTC "
            "materialization."
        ),
    )

    # Exactly one subcommand.
    group = parser.add_mutually_exclusive_group(required=True)
    for flag, (help_text, _) in SUBCOMMANDS.items():
        group.add_argument(flag, action="store_true", help=help_text)

    # Range shape for *-backfill commands.
    # --days and --start are mutually exclusive; --end pairs with
    # --start. If neither --days nor --start is given, the service
    # defaults to --days 30.
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument(
        "--days",
        type=int,
        default=None,
        help=(
            "Backfill the last N days (mutually exclusive with "
            "--start/--end). Defaults to 30 if --start is not given."
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

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Log what would be written; write nothing.",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help=(
            "Report missing hours in the range; write nothing. "
            "Exit code 1 if any hours are missing."
        ),
    )

    return parser


# ============================================================
# ENTRY POINT
# ============================================================


async def _dispatch(args: argparse.Namespace) -> int:
    for flag, (_, handler) in SUBCOMMANDS.items():
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            # --btc-hourly-backfill takes args; others don't.
            if flag == "--btc-hourly-backfill":
                return await handler(args)
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
    except ValueError as exc:
        logger.error("[CLI] %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())