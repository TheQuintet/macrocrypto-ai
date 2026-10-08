"""
Hourly gap detection (Chat 4, C4-2).

For a range [start, end), find hours that are missing from an
hourly table, and classify each as either:

  MATERIALIZATION_GAP
      Raw data for that hour exists (or exists at-or-before the
      hour, for macro), so re-running Chat 3's hourly writer
      would produce a row.

  RAW_DATA_GAP
      Raw data does not exist. Re-materializing won't help;
      the operator must first run the appropriate raw backfill
      (C4-1's run_hourly_backfills.py --btc for BTC, or Phase A's
      run_backfills.py for macro/FRED), then re-materialize.

Asymmetric raw-check rule (Chat 4 Decision, confirmed):

  btc_prices_hourly:
      raw_has_data(H) = EXISTS btc_prices tick in [H, H+1h)
      Rationale: HourlyBTCPricesService.build_hour_row reads
      ticks in [H, H+1h). Zero ticks -> returns None -> writer
      skips. So no ticks => re-materializing cannot produce a
      row; the gap is raw-side.

  macro_indicators_hourly:
      raw_has_data(H) = EXISTS macro_indicators observation
                        with time <= H
      Rationale: HourlyMacroIndicatorsService.build_hour_row
      reads the latest observation with time <= H (ffill). Any
      prior observation -> non-NULL row. No prior observation
      -> all-NULL row (writer still writes it, but useless).
      So no prior observation => re-materializing cannot
      produce a useful row; the gap is raw-side.

The addendum's "macro always has data" claim is too strong —
it ignored the pre-first-observation case. This module uses
the general rule above.

No writes are performed by scan(). repair() is opt-in and
uses the hour-by-hour write_hour primitive (Chat 4 Decision).

Returns persisted counts, matching Chat 3's convention.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlalchemy import text

from app.database.session import SessionLocal
from app.services.hourly_btc_prices_service import (
    HourlyBTCPricesService,
    _floor_to_hour,
    _last_completed_hour,
)
from app.services.hourly_macro_indicators_service import (
    HourlyMacroIndicatorsService,
)

logger = logging.getLogger(__name__)


ONE_HOUR = timedelta(hours=1)


# ============================================================
# TABLE CONSTANTS
# ============================================================

TABLE_BTC = "btc_prices_hourly"
TABLE_MACRO = "macro_indicators_hourly"

SUPPORTED_TABLES = (TABLE_BTC, TABLE_MACRO)


# ============================================================
# TYPES
# ============================================================


class GapClass(str, Enum):
    """How a missing hour can be repaired."""

    MATERIALIZATION_GAP = "MATERIALIZATION_GAP"
    RAW_DATA_GAP = "RAW_DATA_GAP"


@dataclass(frozen=True)
class MissingHour:
    hour: datetime
    classification: GapClass


@dataclass
class GapReport:
    """
    Result of scanning one hourly table over a range.

    All counts are in hours. `missing_hours` is the full set;
    `first_missing` is capped for display.
    """

    table: str
    start: datetime
    end: datetime
    expected_hours: int
    actual_hours: int
    missing_count: int
    materialization_count: int
    raw_data_count: int
    missing_hours: list[MissingHour] = field(default_factory=list)

    @property
    def has_gaps(self) -> bool:
        return self.missing_count > 0

    def first_missing(self, n: int = 20) -> list[MissingHour]:
        return self.missing_hours[:n]

    def suggested_commands(self) -> list[str]:
        """
        Human-readable repair commands, tailored to the classes
        present in this report.

        BTC RAW_DATA_GAP:
            Point at C4-1's hourly backfill (run_hourly_backfills
            --btc). Binance is the source for raw BTC ticks.

        Macro RAW_DATA_GAP:
            Point at Phase A's daily FRED backfill
            (run_backfills.py). NOTE: macro_indicators_hourly
            holds cpi, interest_rate, m2_growth, dxy,
            treasury_yield from FRED — NOT gold. Gold is a raw
            indicator (gold_spot) that feeds features_db, not
            the macro hourly table. If the gap precedes all
            available FRED history, there is nothing to backfill.

        In both cases, MATERIALIZATION_GAP hours are repaired
        via --repair on this same CLI.
        """
        cmds: list[str] = []

        if self.raw_data_count > 0:
            if self.table == TABLE_BTC:
                cmds.append(
                    "# BTC raw ticks are missing for some hours. "
                    "Fetch hourly candles first:"
                )
                cmds.append(
                    "python -m app.scripts.run_hourly_backfills --btc "
                    f"--start {self.start.date()} "
                    f"--end {self.end.date()}"
                )
            elif self.table == TABLE_MACRO:
                cmds.append(
                    "# Macro raw observations are missing for some "
                    "hours. Fetch FRED data first:"
                )
                cmds.append("python -m app.scripts.run_backfills")
                cmds.append(
                    "# If the gap precedes all available FRED "
                    "history, there is nothing to backfill."
                )

        if self.materialization_count > 0 or self.raw_data_count > 0:
            flag = "--table btc" if self.table == TABLE_BTC else "--table macro"
            cmds.append(
                "# Then re-materialize (--repair covers "
                "MATERIALIZATION_GAP hours only):"
            )
            cmds.append(
                "python -m app.scripts.verify_hourly_tables "
                f"{flag} --start {self.start.date()} "
                f"--end {self.end.date()} --repair"
            )

        return cmds


# ============================================================
# EXPECTED / ACTUAL HOURS
# ============================================================


def _expected_hours(start: datetime, end: datetime) -> list[datetime]:
    """All hour boundaries in [start, end)."""
    hours: list[datetime] = []
    cursor = start
    while cursor < end:
        hours.append(cursor)
        cursor += ONE_HOUR
    return hours


def _actual_hours(
    table: str,
    start: datetime,
    end: datetime,
) -> set[datetime]:
    """Hours already present in the hourly table over [start, end)."""
    if table not in SUPPORTED_TABLES:
        raise ValueError(f"unsupported table: {table}")

    # `table` is interpolated; it is validated against
    # SUPPORTED_TABLES above and never comes from user input
    # without that validation.
    sql = text(
        f"""
        SELECT time FROM {table}
        WHERE time >= :start AND time < :end
        """
    )
    session = SessionLocal()
    try:
        rows = session.execute(
            sql, {"start": start, "end": end}
        ).all()
        return {_floor_to_hour(r[0]) for r in rows}
    finally:
        session.close()


# ============================================================
# RAW DATA PRESENCE — ASYMMETRIC
# ============================================================


def _raw_has_data_btc(hour: datetime) -> bool:
    """
    BTC: raw_has_data(H) = EXISTS tick in [H, H+1h).

    Matches HourlyBTCPricesService.build_hour_row's read.
    """
    sql = text(
        """
        SELECT 1 FROM btc_prices
        WHERE time >= :start AND time < :end
        LIMIT 1
        """
    )
    session = SessionLocal()
    try:
        row = session.execute(
            sql, {"start": hour, "end": hour + ONE_HOUR}
        ).first()
        return row is not None
    finally:
        session.close()


def _raw_has_data_macro(hour: datetime) -> bool:
    """
    Macro: raw_has_data(H) = EXISTS observation with time <= H.

    Matches HourlyMacroIndicatorsService.build_hour_row's read
    (latest observation with time <= H, per-indicator ffill).
    """
    sql = text(
        """
        SELECT 1 FROM macro_indicators
        WHERE time <= :hour
        LIMIT 1
        """
    )
    session = SessionLocal()
    try:
        row = session.execute(sql, {"hour": hour}).first()
        return row is not None
    finally:
        session.close()


def _raw_has_data(table: str, hour: datetime) -> bool:
    """
    Dispatch to the table's raw-presence check.

    The two rules are deliberately asymmetric — see module
    docstring. Do not collapse them.
    """
    if table == TABLE_BTC:
        return _raw_has_data_btc(hour)
    if table == TABLE_MACRO:
        return _raw_has_data_macro(hour)
    raise ValueError(f"unsupported table: {table}")


# ============================================================
# SCAN
# ============================================================


def scan(
    table: str,
    start: datetime,
    end: datetime,
) -> GapReport:
    """
    Read-only gap scan. Does not write anything.

    start: inclusive, floored to the hour.
    end:   exclusive, floored to the hour, clamped to the last
           completed hour.
    """
    if table not in SUPPORTED_TABLES:
        raise ValueError(f"unsupported table: {table}")

    start = _floor_to_hour(start)
    end = _floor_to_hour(end)

    last_completed = _last_completed_hour()
    if end > last_completed:
        logger.warning(
            "[GAP-DETECT] %s clamping end %s to last completed hour %s",
            table, end.isoformat(), last_completed.isoformat(),
        )
        end = last_completed

    if end <= start:
        raise ValueError(
            f"invalid range: start={start.isoformat()} "
            f"end={end.isoformat()}"
        )

    expected = _expected_hours(start, end)
    actual = _actual_hours(table, start, end)

    missing_hours: list[MissingHour] = []
    mat_count = 0
    raw_count = 0

    for hour in expected:
        if hour in actual:
            continue
        if _raw_has_data(table, hour):
            classification = GapClass.MATERIALIZATION_GAP
            mat_count += 1
        else:
            classification = GapClass.RAW_DATA_GAP
            raw_count += 1
        missing_hours.append(
            MissingHour(hour=hour, classification=classification)
        )

    report = GapReport(
        table=table,
        start=start,
        end=end,
        expected_hours=len(expected),
        actual_hours=len(actual),
        missing_count=len(missing_hours),
        materialization_count=mat_count,
        raw_data_count=raw_count,
        missing_hours=missing_hours,
    )

    logger.info(
        "[GAP-DETECT] %s %s -> %s: expected=%d actual=%d "
        "missing=%d (mat=%d raw=%d)",
        table,
        start.isoformat(), end.isoformat(),
        report.expected_hours, report.actual_hours,
        report.missing_count,
        report.materialization_count, report.raw_data_count,
    )

    return report


# ============================================================
# REPAIR — OPT-IN
# ============================================================


def _make_writer(table: str):
    """
    Return a callable (hour -> bool) that materializes one hour
    using Chat 3's writer primitive (write_hour).

    Both Chat 3 services accept a Session as their first
    positional argument:

        HourlyBTCPricesService(db: Session)
        HourlyMacroIndicatorsService(db: Session)

    If either signature changes to manage its own session, this
    helper must be updated — otherwise it leaks a session per
    repaired hour.
    """
    if table == TABLE_BTC:

        def _write(hour: datetime) -> bool:
            session = SessionLocal()
            try:
                service = HourlyBTCPricesService(session)
                return service.write_hour(hour)
            finally:
                session.close()

        return _write

    if table == TABLE_MACRO:

        def _write(hour: datetime) -> bool:
            session = SessionLocal()
            try:
                service = HourlyMacroIndicatorsService(session)
                return service.write_hour(hour)
            finally:
                session.close()

        return _write

    raise ValueError(f"unsupported table: {table}")


def repair(report: GapReport) -> dict[str, int]:
    """
    Attempt to repair the MATERIALIZATION_GAP hours in `report`.

    For each MATERIALIZATION_GAP hour, calls Chat 3's write_hour
    primitive on that single hour.

    For each RAW_DATA_GAP hour, does nothing except log a
    pointer to the appropriate raw backfill. We never auto-pull
    from external providers from here: those calls have rate
    limits and cost, and should be explicit human decisions
    (Chat 4 Decision 2).

    Returns a summary dict:
        {
          "attempted":   int,  # MATERIALIZATION_GAP hours written
          "succeeded":   int,  # write_hour returned True
          "skipped":     int,  # write_hour returned False
          "raw_gaps":    int,  # RAW_DATA_GAP hours left untouched
          "errors":      int,  # write_hour raised
        }
    """
    write = _make_writer(report.table)

    attempted = 0
    succeeded = 0
    skipped = 0
    errors = 0

    for item in report.missing_hours:
        if item.classification == GapClass.RAW_DATA_GAP:
            continue

        attempted += 1
        try:
            wrote = write(item.hour)
            if wrote:
                succeeded += 1
            else:
                skipped += 1
        except Exception:
            logger.exception(
                "[GAP-REPAIR] %s write_hour(%s) failed",
                report.table, item.hour.isoformat(),
            )
            errors += 1

    raw_gaps = report.raw_data_count
    if raw_gaps > 0:
        if report.table == TABLE_BTC:
            pointer = (
                "python -m app.scripts.run_hourly_backfills --btc"
            )
        else:
            pointer = "python -m app.scripts.run_backfills"
        logger.warning(
            "[GAP-REPAIR] %s: %d RAW_DATA_GAP hour(s) not repaired. "
            "Run the raw backfill first (%s), then re-run this "
            "command with --repair.",
            report.table, raw_gaps, pointer,
        )

    summary = {
        "attempted": attempted,
        "succeeded": succeeded,
        "skipped": skipped,
        "raw_gaps": raw_gaps,
        "errors": errors,
    }
    logger.info(
        "[GAP-REPAIR] %s done: attempted=%d succeeded=%d "
        "skipped=%d raw_gaps=%d errors=%d",
        report.table, attempted, succeeded, skipped, raw_gaps, errors,
    )
    return summary