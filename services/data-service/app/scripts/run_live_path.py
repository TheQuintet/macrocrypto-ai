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
    python -m app.scripts.run_live_path --macro-hourly-backfill --days 30
    python -m app.scripts.run_live_path --macro-hourly-backfill \
        --start 2024-01-01 --end 2024-12-31
    python -m app.scripts.run_live_path --macro-hourly-backfill --verify --days 30
    python -m app.scripts.run_live_path --macro-hourly-backfill --dry-run --days 30
    python -m app.scripts.run_live_path --verify-hourly --table btc --days 30
    python -m app.scripts.run_live_path --verify-hourly --table macro --days 30
    python -m app.scripts.run_live_path --verify-hourly --table all --days 7
    python -m app.scripts.run_live_path --verify-hourly --table btc \
        --days 7 --repair
    python -m app.scripts.run_live_path --macro-vintages
    python -m app.scripts.run_live_path --macro-vintages --years 20
    python -m app.scripts.run_live_path --macro-vintages-backfill
    python -m app.scripts.run_live_path --macro-vintages-backfill --years 10
    python -m app.scripts.run_live_path --features-db
    python -m app.scripts.run_live_path --features-db-backfill --days 30
    python -m app.scripts.run_live_path --features-db-backfill \
        --start 2024-01-01 --end 2024-12-31
    python -m app.scripts.run_live_path --features-db-parquet --days 365
    python -m app.scripts.run_live_path --features-db-parquet \
        --start 2023-01-01 --end 2024-12-31
    python -m app.scripts.run_live_path --all

Scope
-----
Phase A (Chat 2):
    --backfill is the daily-resolution backfill.

Phase B (Chat 3):
    --btc-hourly writes btc_prices_hourly for the just-completed hour.
    --btc-hourly-backfill materializes a range of hours from raw data.
    --macro-hourly writes macro_indicators_hourly for the
        just-completed hour.
    --macro-hourly-backfill materializes a range of hours from raw data.

Phase B (Chat 4, C4-2):
    --verify-hourly scans one or more hourly tables for gaps and
        classifies each missing hour as MATERIALIZATION_GAP or
        RAW_DATA_GAP. Requires --table. Supports --repair (default
        OFF) to fix MATERIALIZATION_GAP hours. This is the
        consolidated verify path (Chat 4 Decision 8); Chat 3's
        per-command --verify flag on the *-hourly-backfill
        subcommands is left untouched.

Phase B (Chat 5, B6):
    --macro-vintages fetches FRED vintages for the 5 revision-prone
        series and writes them to macro_indicator_vintages. Uses
        VINTAGE_LOOKBACK_YEARS by default.
    --macro-vintages-backfill is an alias for the same operation,
        provided for symmetry with the *-backfill naming used by
        the hourly commands. Both accept --years to override the
        lookback for a single run.

Phase B (Chat 5, B4):
    --features-db writes the just-completed hour's row to
        features_db. Enforces the D9 writer lag.
    --features-db-backfill writes a range of hours to
        features_db, skipping already-present hours. Accepts
        --days / --start / --end.
    --features-db-parquet produces the Option B hourly parquet
        set (train/val/test/live_frontier + feature_scaler.pkl)
        in FEATURES_DB_PARQUET_DIR (default
        app/data/processed_v2_builder/). Accepts --days /
        --start / --end.

Design notes
------------
- CLI calls the same service methods the scheduler calls. No
  business logic lives here (D2).
- run_backfills.py remains the top-level manual script; this CLI
  is an additive trigger, not a replacement.
- All backfill commands are idempotent (ON CONFLICT DO NOTHING),
  so re-running is safe.
- --features-db-backfill and --features-db-parquet use the same
  range shape (--days / --start / --end) as the hourly
  backfills. See _resolve_backfill_range().
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

from app.services.gap_detection_service import (
    SUPPORTED_TABLES,
    TABLE_BTC,
    TABLE_MACRO,
    repair as repair_gaps,
    scan as scan_gaps,
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
    """
    Materialize macro_indicators_hourly for the previous
    completed hour.
    """
    from app.database.session import SessionLocal
    from app.services.hourly_macro_indicators_service import (
        HourlyMacroIndicatorsService,
    )

    now = datetime.now(timezone.utc)
    target_hour = now.replace(
        minute=0, second=0, microsecond=0
    ) - timedelta(hours=1)

    db = SessionLocal()
    try:
        service = HourlyMacroIndicatorsService(db)
        service.write_hour(target_hour)
        logger.info(
            "[CLI] wrote macro_indicators_hourly row for %s",
            target_hour.isoformat(),
        )
        return 0
    finally:
        db.close()


async def _run_macro_hourly_backfill(
    args: argparse.Namespace,
) -> int:
    """
    Materialize macro_indicators_hourly for a range of hours.
    """
    from app.database.session import SessionLocal
    from app.services.hourly_macro_indicators_service import (
        HourlyMacroIndicatorsService,
    )

    start, end = _resolve_backfill_range(args)

    logger.info(
        "[CLI] macro-hourly-backfill range: %s -> %s%s%s",
        start.isoformat(),
        end.isoformat(),
        " (dry-run)" if args.dry_run else "",
        " (verify)" if args.verify else "",
    )

    db = SessionLocal()
    try:
        service = HourlyMacroIndicatorsService(db)
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
        "[CLI] macro-hourly-backfill %s: expected=%d written=%d "
        "already=%d",
        "DRY-RUN" if args.dry_run else "done",
        summary["expected_hours"],
        summary["written"],
        summary["already_present"],
    )
    return 0


# ------------------------------------------------------------------
# --verify-hourly (C4-2, Chat 4)
# ------------------------------------------------------------------
#
# Consolidated verify path (Chat 4 Decision 8):
#   --verify-hourly --table {btc,macro,all}
#
# Reuses the same gap_detection_service the new top-level CLI
# (verify_hourly_tables.py) uses. Chat 3's --verify flag on the
# *-hourly-backfill subcommands is untouched — it still works
# and covers the per-service case.

TABLE_ALIASES: dict[str, list[str]] = {
    "btc": [TABLE_BTC],
    "macro": [TABLE_MACRO],
    "all": list(SUPPORTED_TABLES),
}


async def _run_verify_hourly(args: argparse.Namespace) -> int:
    """
    Scan one or more hourly tables for gaps; optionally repair.

    Exit codes:
        0   no gaps found
        1   gaps found (regardless of --repair outcome)
        2   invalid args
        3   database or repair error
    """
    if args.table is None:
        logger.error("[CLI] --verify-hourly requires --table")
        return 2

    if args.table not in TABLE_ALIASES:
        logger.error(
            "[CLI] --table must be one of: %s",
            ", ".join(sorted(TABLE_ALIASES.keys())),
        )
        return 2

    if args.verify and args.dry_run:
        logger.warning(
            "[CLI] --verify and --dry-run are mutually exclusive; "
            "--verify takes precedence"
        )

    try:
        start, end = _resolve_backfill_range(args)
    except ValueError as exc:
        logger.error("[CLI] %s", exc)
        return 2

    tables = TABLE_ALIASES[args.table]

    logger.info(
        "[CLI] verify-hourly: tables=%s range=%s -> %s repair=%s",
        ",".join(tables),
        start.isoformat(), end.isoformat(),
        args.repair,
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

        # Print a compact human-readable summary.
        print()
        print(f"=== {table} ===")
        print(
            f"  range:           {report.start.isoformat()} -> "
            f"{report.end.isoformat()}"
        )
        print(f"  expected hours:  {report.expected_hours}")
        print(f"  actual hours:    {report.actual_hours}")
        print(f"  missing hours:   {report.missing_count}")
        if report.has_gaps:
            print(
                f"    MATERIALIZATION_GAP: "
                f"{report.materialization_count}"
            )
            print(
                f"    RAW_DATA_GAP:        "
                f"{report.raw_data_count}"
            )
            for item in report.first_missing(20):
                print(
                    f"    {item.hour.isoformat()}  "
                    f"{item.classification.value}"
                )
            if report.missing_count > 20:
                print(
                    f"    ... and {report.missing_count - 20} more"
                )

        if not report.has_gaps:
            continue

        any_gaps = True

        if args.repair:
            try:
                summary = repair_gaps(report)
            except Exception:
                logger.exception(
                    "[CLI] repair failed for %s", table
                )
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


# ------------------------------------------------------------------
# --macro-vintages / --macro-vintages-backfill (Chat 5, B6)
# ------------------------------------------------------------------
#
# Fetches FRED vintages for the 5 revision-prone series and writes
# them to macro_indicator_vintages. Idempotent (ON CONFLICT DO
# NOTHING on the (series_id, observation_date, release_date)
# unique constraint), so re-running is a no-op for stored rows.
#
# --macro-vintages and --macro-vintages-backfill are aliases for
# the same operation. Both accept --years to override the
# VINTAGE_LOOKBACK_YEARS default for one run; if --years is not
# given, the setting is used.
#
# Requires a real FRED_API_KEY. If the key is missing or still
# the placeholder, the service constructor raises RuntimeError
# and the CLI exits 1 with a clear message.


async def _run_macro_vintages(args: argparse.Namespace) -> int:
    """
    Fetch and persist FRED macro indicator vintages.

    Exit codes:
        0   at least one series written (or already present)
        1   no series succeeded, or FRED key misconfigured
        2   bad args
    """
    from app.database.session import SessionLocal
    from app.services.macro_vintage_service import (
        MacroVintageService,
    )

    lookback_years = args.years

    logger.info(
        "[CLI] macro-vintages: lookback_years=%s",
        lookback_years
        if lookback_years is not None
        else f"default ({_vintage_default_years()})",
    )

    db = SessionLocal()
    service = None
    try:
        try:
            service = MacroVintageService(
                db,
                lookback_years=lookback_years,
            )
        except RuntimeError as exc:
            # Missing or placeholder FRED_API_KEY. Fail with a
            # clean, actionable message rather than a traceback.
            logger.error("[CLI] %s", exc)
            return 1
        except ValueError as exc:
            logger.error("[CLI] %s", exc)
            return 2

        try:
            records = await service.collect()
        except Exception:
            logger.exception(
                "[CLI] macro-vintages collection failed"
            )
            return 1

        if not records:
            logger.warning(
                "[CLI] macro-vintages: no records returned; "
                "nothing to persist"
            )
            return 1

        attempted = service.repository.create_many(records)

        logger.info(
            "[CLI] macro-vintages done: attempted=%d",
            attempted,
        )

        # Per-series summary for operator visibility.
        counts = service.repository.count_by_series()
        if counts:
            print()
            print("=== macro_indicator_vintages (per series) ===")
            for series_id in sorted(counts.keys()):
                print(f"  {series_id:<12} {counts[series_id]} rows")

        return 0

    finally:
        if service:
            await service.close()
        db.close()


def _vintage_default_years() -> int:
    """
    Read VINTAGE_LOOKBACK_YEARS without importing the whole
    settings object twice. Isolated here so the CLI's logging
    line stays truthful if the setting changes.
    """
    from app.config import settings

    return settings.VINTAGE_LOOKBACK_YEARS


# ------------------------------------------------------------------
# --features-db / --features-db-backfill / --features-db-parquet
#   (Chat 5, B4)
# ------------------------------------------------------------------
#
# Three related commands:
#
#   --features-db
#       Writes the just-completed hour to features_db. Enforces
#       the D9 writer lag. Called by the scheduler every hour at
#       :05; the CLI is the manual trigger.
#
#   --features-db-backfill
#       Writes a range of hours to features_db. Skips hours
#       already present. Idempotent (ON CONFLICT (ds) DO NOTHING).
#
#   --features-db-parquet
#       Produces the Option B hourly parquet set:
#         train_scaled.parquet
#         val_scaled.parquet
#         test_scaled.parquet
#         live_frontier_scaled.parquet
#         feature_scaler.pkl
#       in FEATURES_DB_PARQUET_DIR. Does NOT write to features_db.
#       Uses SplitProcessor + FeatureScaler with hourly configs.
#
# The DB writer and the parquet writer both call
# FeatureBuilderService.build_features(); they never compute
# features independently. See feature_builder_service.py and
# the B4 D22 guarantee.


async def _run_features_db() -> int:
    """
    Write the just-completed hour to features_db.

    Exit codes:
        0   a row was written, or already present
        1   no row could be built (successor close missing)
        2   DB or runtime error
    """
    from app.database.session import SessionLocal
    from app.services.features_db_writer import FeaturesDBWriter

    db = SessionLocal()
    try:
        writer = FeaturesDBWriter(db)
        wrote = writer.write_current_hour()

        if wrote:
            logger.info(
                "[CLI] features-db: wrote the previous hour"
            )
            return 0

        logger.warning(
            "[CLI] features-db: no row available for the "
            "previous hour (successor close missing)"
        )
        return 1

    except Exception:
        logger.exception("[CLI] features-db failed")
        return 2

    finally:
        db.close()


async def _run_features_db_backfill(
    args: argparse.Namespace,
) -> int:
    """
    Write a range of hours to features_db.

    Exit codes:
        0   completed (some rows may have been skipped as
            already present)
        2   bad args or DB error
    """
    from app.database.session import SessionLocal
    from app.services.features_db_writer import FeaturesDBWriter

    try:
        start, end = _resolve_backfill_range(args)
    except ValueError as exc:
        logger.error("[CLI] %s", exc)
        return 2

    logger.info(
        "[CLI] features-db-backfill range: %s -> %s",
        start.isoformat(),
        end.isoformat(),
    )

    db = SessionLocal()
    try:
        writer = FeaturesDBWriter(db)
        summary = writer.write_range(start, end)

        logger.info(
            "[CLI] features-db-backfill done: expected=%d "
            "written=%d skipped=%d already=%d",
            summary["expected_hours"],
            summary["written"],
            summary["skipped"],
            summary["already_present"],
        )
        return 0

    except Exception:
        logger.exception("[CLI] features-db-backfill failed")
        return 2

    finally:
        db.close()


async def _run_features_db_parquet(
    args: argparse.Namespace,
) -> int:
    """
    Produce the Option B hourly parquet set.

    Exit codes:
        0   completed
        2   bad args or runtime error
    """
    from app.database.session import SessionLocal
    from app.services.features_parquet_writer import (
        FeaturesParquetWriter,
    )

    try:
        start, end = _resolve_backfill_range(args)
    except ValueError as exc:
        logger.error("[CLI] %s", exc)
        return 2

    logger.info(
        "[CLI] features-db-parquet range: %s -> %s",
        start.isoformat(),
        end.isoformat(),
    )

    db = SessionLocal()
    try:
        writer = FeaturesParquetWriter(db)
        summary = writer.write_all(start, end)

        print()
        print("=== processed_v2_builder ===")
        print(f"  output_dir:   {summary['output_dir']}")
        print(f"  train_rows:   {summary['train_rows']}")
        print(f"  val_rows:     {summary['val_rows']}")
        print(f"  test_rows:    {summary['test_rows']}")
        print(f"  frontier_rows:{summary['frontier_rows']}")
        print(
            f"  purged+embargoed: "
            f"{summary['purged_embargo_rows']}"
        )

        return 0

    except Exception:
        logger.exception("[CLI] features-db-parquet failed")
        return 2

    finally:
        db.close()


async def _run_all() -> int:
    """
    Run everything in order. --backfill, --btc-hourly,
    --macro-hourly, and --features-db are real.
    """
    rc = await _run_backfill()
    if rc != 0:
        return rc

    await _run_btc_hourly()
    await _run_macro_hourly()
    await _run_features_db()
    return 0


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
        "Write macro_indicators_hourly for the last completed hour",
        _run_macro_hourly,
    ),
    "--macro-hourly-backfill": (
        "Materialize macro_indicators_hourly over a range of hours",
        _run_macro_hourly_backfill,
    ),
    "--verify-hourly": (
        "Scan hourly tables for gaps; --repair to fix "
        "MATERIALIZATION_GAP hours (requires --table)",
        _run_verify_hourly,
    ),
    "--macro-vintages": (
        "Fetch FRED macro indicator vintages and persist them "
        "(Phase B, B6)",
        _run_macro_vintages,
    ),
    "--macro-vintages-backfill": (
        "Alias for --macro-vintages; accepts --years to override "
        "VINTAGE_LOOKBACK_YEARS for one run",
        _run_macro_vintages,
    ),
    "--features-db": (
        "Write the just-completed hour to features_db",
        _run_features_db,
    ),
    "--features-db-backfill": (
        "Write a range of hours to features_db; skips hours "
        "already present",
        _run_features_db_backfill,
    ),
    "--features-db-parquet": (
        "Produce the Option B hourly parquet set in "
        "FEATURES_DB_PARQUET_DIR (split + scale)",
        _run_features_db_parquet,
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
            "Supports the daily backfill, the hourly BTC "
            "and macro materializations, hourly gap "
            "verification, FRED macro vintage ingestion, "
            "and features_db writes."
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

    parser.add_argument(
        "--table",
        choices=["btc", "macro", "all"],
        default=None,
        help=(
            "Which hourly table(s) --verify-hourly scans. "
            "Required when --verify-hourly is used."
        ),
    )

    parser.add_argument(
        "--repair",
        action="store_true",
        help=(
            "With --verify-hourly: attempt to repair "
            "MATERIALIZATION_GAP hours by re-running Chat 3's "
            "hourly writer on each. RAW_DATA_GAP hours are left "
            "untouched. Defaults OFF."
        ),
    )

    parser.add_argument(
        "--years",
        type=int,
        default=None,
        help=(
            "With --macro-vintages / --macro-vintages-backfill: "
            "lookback window in years. Overrides "
            "VINTAGE_LOOKBACK_YEARS for one run. Must be a "
            "positive integer."
        ),
    )

    return parser


# ============================================================
# ENTRY POINT
# ============================================================


async def _dispatch(args: argparse.Namespace) -> int:
    ARG_TAKING_FLAGS = (
        "--btc-hourly-backfill",
        "--macro-hourly-backfill",
        "--verify-hourly",
        "--macro-vintages",
        "--macro-vintages-backfill",
        "--features-db-backfill",
        "--features-db-parquet",
    )
    for flag, (_, handler) in SUBCOMMANDS.items():
        if getattr(args, flag.lstrip("-").replace("-", "_")):
            if flag in ARG_TAKING_FLAGS:
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