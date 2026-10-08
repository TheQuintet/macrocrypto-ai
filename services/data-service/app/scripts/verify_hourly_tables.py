"""
CLI for hourly table gap verification and optional repair
(Chat 4, C4-2).

Usage
-----
    python -m app.scripts.verify_hourly_tables --table btc --days 30
    python -m app.scripts.verify_hourly_tables --table macro --days 30
    python -m app.scripts.verify_hourly_tables --table all --days 7
    python -m app.scripts.verify_hourly_tables --table btc \\
        --start 2024-01-01 --end 2024-12-31
    python -m app.scripts.verify_hourly_tables --table btc --days 7 --repair

Default range
-------------
If neither --days nor --start is given, --days 30 is used,
matching Chat 3 and C4-1's defaults.

Repair policy
-------------
--repair defaults OFF (Chat 4 Decision 2). When enabled:
  - MATERIALIZATION_GAP hours are repaired hour-by-hour using
    Chat 3's write_hour primitive.
  - RAW_DATA_GAP hours are NOT auto-repaired. A message tells
    the operator to run the appropriate raw backfill first
    (run_hourly_backfills --btc for BTC,
     run_backfills            for macro/FRED).
    We never pull from external providers implicitly.

Exit codes
----------
    0   no gaps found
    1   gaps found (regardless of whether --repair fixed them)
    2   invalid args
    3   database or other runtime error

Scope
-----
This is a thin wrapper around app.services.gap_detection_service.
All business logic lives in the service, per Chat 4 Decision
(the CLI calls the same service the future scheduler will call).
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.services.gap_detection_service import (
    SUPPORTED_TABLES,
    TABLE_BTC,
    TABLE_MACRO,
    GapReport,
    repair as repair_gaps,
    scan as scan_gaps,
)


logger = logging.getLogger(__name__)


DEFAULT_DAYS = 30

# CLI-level table selector -> service-level table name.
TABLE_ALIASES: dict[str, list[str]] = {
    "btc": [TABLE_BTC],
    "macro": [TABLE_MACRO],
    "all": list(SUPPORTED_TABLES),
}


# ============================================================
# PARSING HELPERS
# ============================================================


def _parse_utc_datetime(raw: str) -> datetime:
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
    return dt.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


def _resolve_range(
    args: argparse.Namespace,
) -> tuple[datetime, datetime]:
    """
    Resolve --days or --start/--end into a floored (start, end).

    Defaults to --days 30 when neither --days nor --start given.
    """
    if args.days is not None and args.end is not None:
        logger.warning(
            "[CLI] --end is ignored when --days is used; "
            "using now() as the end."
        )

    now = _floor_to_hour(datetime.now(timezone.utc))

    if args.days is not None:
        if args.days <= 0:
            raise ValueError("--days must be a positive integer")
        return now - timedelta(days=args.days), now

    if args.start is None:
        return now - timedelta(days=DEFAULT_DAYS), now

    start = _floor_to_hour(_parse_utc_datetime(args.start))
    end = (
        _floor_to_hour(_parse_utc_datetime(args.end))
        if args.end is not None
        else now
    )
    if end <= start:
        raise ValueError(
            f"--end ({end.isoformat()}) must be after "
            f"--start ({start.isoformat()})"
        )
    return start, end


def _selected_tables(args: argparse.Namespace) -> list[str]:
    return TABLE_ALIASES[args.table]


# ============================================================
# REPORT RENDERING
# ============================================================


def _print_report(report: GapReport) -> None:
    print()
    print(f"=== {report.table} ===")
    print(
        f"  range:   {report.start.isoformat()} -> "
        f"{report.end.isoformat()}"
    )
    print(f"  expected hours: {report.expected_hours}")
    print(f"  actual hours:   {report.actual_hours}")

    if not report.has_gaps:
        print("  missing hours:  0")
        return

    pct = 100.0 * report.missing_count / max(report.expected_hours, 1)
    print(
        f"  missing hours:  {report.missing_count} "
        f"({pct:.2f}%)"
    )
    print(
        f"    MATERIALIZATION_GAP: "
        f"{report.materialization_count}"
    )
    print(
        f"    RAW_DATA_GAP:        "
        f"{report.raw_data_count}"
    )

    print("  first missing hours:")
    for item in report.first_missing(20):
        print(f"    {item.hour.isoformat()}  {item.classification.value}")
    if report.missing_count > 20:
        print(f"    ... and {report.missing_count - 20} more")

    cmds = report.suggested_commands()
    if cmds:
        print("  suggested commands:")
        for line in cmds:
            print(f"    {line}")


# ============================================================
# ARGPARSE
# ============================================================


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_hourly_tables",
        description=(
            "Find gaps in btc_prices_hourly and/or "
            "macro_indicators_hourly, classify each missing hour "
            "as MATERIALIZATION_GAP or RAW_DATA_GAP, and "
            "optionally repair the MATERIALIZATION_GAP hours."
        ),
    )

    parser.add_argument(
        "--table",
        choices=sorted(TABLE_ALIASES.keys()),
        required=True,
        help="Which hourly table(s) to scan.",
    )

    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument(
        "--days",
        type=int,
        default=None,
        help=(
            f"Scan the last N days. Defaults to {DEFAULT_DAYS} "
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

    parser.add_argument(
        "--repair",
        action="store_true",
        help=(
            "Attempt to repair MATERIALIZATION_GAP hours by "
            "re-running Chat 3's hourly writer on each. RAW_DATA_GAP "
            "hours are left untouched (run the raw backfill first). "
            "Defaults OFF."
        ),
    )

    return parser


# ============================================================
# ENTRY POINT
# ============================================================


def _run(args: argparse.Namespace) -> int:
    try:
        start, end = _resolve_range(args)
    except ValueError as exc:
        logger.error("[CLI] %s", exc)
        return 2

    tables = _selected_tables(args)
    logger.info(
        "[CLI] verify %s range %s -> %s (repair=%s)",
        ",".join(tables),
        start.isoformat(), end.isoformat(), args.repair,
    )

    any_gaps = False
    any_repair_errors = False

    for table in tables:
        try:
            report = scan_gaps(table, start, end)
        except ValueError as exc:
            logger.error("[CLI] %s", exc)
            return 2
        except Exception:
            logger.exception("[CLI] scan failed for %s", table)
            return 3

        _print_report(report)

        if not report.has_gaps:
            continue

        any_gaps = True

        if args.repair:
            try:
                summary = repair_gaps(report)
            except Exception:
                logger.exception("[CLI] repair failed for %s", table)
                any_repair_errors = True
                continue

            print(
                f"  repair: attempted={summary['attempted']} "
                f"succeeded={summary['succeeded']} "
                f"skipped={summary['skipped']} "
                f"raw_gaps={summary['raw_gaps']} "
                f"errors={summary['errors']}"
            )
            if summary["errors"] > 0:
                any_repair_errors = True

    if any_repair_errors:
        return 3
    if any_gaps:
        return 1
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return _run(args)
    except KeyboardInterrupt:
        logger.warning("[CLI] interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())