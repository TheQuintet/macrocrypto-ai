"""
Materialize macro_indicators_hourly from raw macro_indicators.

Reads:
    raw macro_indicators (long format: one row per
    time + indicator_name)

Writes:
    macro_indicators_hourly (wide format: one row per hour,
    one column per indicator)

Missingness policy (locked in Chat 3):

    Each column is the latest raw macro_indicators observation
    with the matching indicator_name and time <= hour. NULL if
    no such observation exists. No age limit.

Rename map (raw indicator_name -> hourly column):

    cpi                -> cpi
    federal_funds_rate -> interest_rate
    m2_money_supply    -> m2_growth
    dxy                -> dxy
    ten_year_treasury  -> treasury_yield

Forward-fill is not implemented as a stateful loop; for each
hour we query "latest observation with time <= hour". That is
equivalent to forward-fill with no limit, and it is stateless
so the backfill can run in any order and be interrupted freely.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.macro_indicators_hourly_repository import (
    MacroIndicatorHourlyRepository,
)

logger = logging.getLogger(__name__)


ONE_HOUR = timedelta(hours=1)


# Raw indicator_name -> hourly column
RENAME_MAP: dict[str, str] = {
    "cpi": "cpi",
    "federal_funds_rate": "interest_rate",
    "m2_money_supply": "m2_growth",
    "dxy": "dxy",
    "ten_year_treasury": "treasury_yield",
}


def _floor_to_hour(dt: datetime) -> datetime:
    """Return dt truncated to the start of its UTC hour."""
    return dt.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


def _last_completed_hour(now: datetime | None = None) -> datetime:
    """
    Return the row timestamp of the last completed hour.

    At 14:35, the current hour is [14:00, 15:00) and is not
    complete. The last completed hour is [13:00, 14:00), whose
    row has time = 14:00.
    """
    now = now or datetime.now(timezone.utc)
    return _floor_to_hour(now)


class HourlyMacroIndicatorsService:
    """Materialize macro_indicators_hourly."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = MacroIndicatorHourlyRepository(db)

    async def close(self) -> None:
        """No-op close, kept for symmetry with other services."""
        return None

    # ------------------------------------------------------------------
    # FETCH
    # ------------------------------------------------------------------

    def _latest_value(
        self,
        raw_indicator_name: str,
        hour: datetime,
    ) -> float | None:
        """
        Latest value for a raw indicator with time <= hour.

        Returns None if no observation exists.
        """
        row = self.db.execute(
            text(
                """
                SELECT value
                FROM macro_indicators
                WHERE indicator_name = :name AND time <= :hour
                ORDER BY time DESC
                LIMIT 1
                """
            ),
            {"name": raw_indicator_name, "hour": hour},
        ).first()
        return float(row[0]) if row and row[0] is not None else None

    # ------------------------------------------------------------------
    # BUILD
    # ------------------------------------------------------------------

    def build_hour_row(
        self,
        hour: datetime,
    ) -> dict[str, Any]:
        """
        Build the wide-format row for a given hour.

        Always returns a row. All columns may be NULL if raw
        data has never been observed.
        """
        hour = _floor_to_hour(hour)

        row: dict[str, Any] = {"time": hour}
        for raw_name, hourly_col in RENAME_MAP.items():
            row[hourly_col] = self._latest_value(raw_name, hour)

        return row

    # ------------------------------------------------------------------
    # WRITE
    # ------------------------------------------------------------------

    def write_hour(
        self,
        hour: datetime,
        dry_run: bool = False,
    ) -> bool:
        """
        Build and write one hour's row.

        Always returns True: unlike btc_prices_hourly, this table
        does not skip hours — every hour gets a row, with NULLs
        where data is missing.

        Row is written only if it does not already exist
        (ON CONFLICT DO NOTHING).
        """
        hour = _floor_to_hour(hour)
        row = self.build_hour_row(hour)

        if dry_run:
            logger.info(
                "[MACRO-HOURLY] dry-run would write %s: %s",
                hour.isoformat(),
                {k: v for k, v in row.items() if k != "time"},
            )
            return True

        self.repository.upsert_many([row])
        return True

    # ------------------------------------------------------------------
    # BACKFILL
    # ------------------------------------------------------------------

    def backfill(
        self,
        start: datetime,
        end: datetime,
        dry_run: bool = False,
        verify_only: bool = False,
    ) -> dict[str, Any]:
        """
        Materialize macro_indicators_hourly for every hour in
        [start, end).

        start: inclusive, snapped down to the hour.
        end:   exclusive, snapped down to the hour, clamped to
               the last completed hour.

        Unlike BTC, macro hours are never "skipped" for lack of
        raw data — an all-NULL row is still written. So the
        summary reports "written" as the count of hours that
        were not already present, regardless of whether the
        values are populated.

        verify_only: if True, no writes. Reports which hours are
        missing from the table in the range.
        """
        start = _floor_to_hour(start)
        end = _floor_to_hour(end)

        last_completed = _last_completed_hour()
        if end > last_completed:
            logger.warning(
                "[MACRO-HOURLY] clamping end %s to last completed "
                "hour %s",
                end.isoformat(),
                last_completed.isoformat(),
            )
            end = last_completed

        if end <= start:
            raise ValueError(
                f"Invalid range: start={start.isoformat()} "
                f"end={end.isoformat()}"
            )

        expected = int((end - start).total_seconds() // 3600)

        existing = self.repository.existing_hours(start, end)

        written = 0
        already = 0
        missing: list[datetime] = []

        hour = start
        idx = 0
        while hour < end:
            idx += 1

            if hour in existing:
                already += 1
                hour += ONE_HOUR
                continue

            if verify_only:
                missing.append(hour)
            else:
                self.write_hour(hour, dry_run=dry_run)
                written += 1

            if idx % 1000 == 0:
                logger.info(
                    "[MACRO-HOURLY] progress %d/%d hours (%d%%)",
                    idx,
                    expected,
                    int(100 * idx / expected),
                )

            hour += ONE_HOUR

        summary = {
            "expected_hours": expected,
            "written": written,
            "already_present": already,
        }
        if verify_only:
            summary["missing"] = missing

        logger.info(
            "[MACRO-HOURLY] backfill done: expected=%d written=%d "
            "already=%d",
            expected,
            written,
            already,
        )
        return summary