"""
FeaturesDBWriter — persists FeatureBuilderService output to the
features_db table.

This is a thin writer. All feature computation lives in
FeatureBuilderService; this module's only jobs are:

    - Call build_features() for the right range.
    - Convert the DataFrame into repository-shaped record dicts.
    - Persist via FeaturesDBRepository (ON CONFLICT DO NOTHING).
    - Report what happened.

Design notes
------------

1. Two entry points.

   write_current_hour():
       The scheduler's path. Computes the just-completed hour's
       feature row, enforcing the D9 writer lag so `y` is
       populated. Called hourly at :05.

   write_range(start, end):
       The CLI/backfill path. Writes every hour in [start, end)
       whose `y` is known. Idempotent — re-running skips rows
       already present.

2. Writer lag (D9).

   y at ds = btc_prices_hourly.close at ds + 1h.

   The writer must not persist the current hour's row, because
   its successor close does not exist yet. Convention:

       target_hour = floor_to_hour(now) - 1h

   At 14:05, target_hour = 13:00. Building for [13:00, 14:00)
   produces a row whose `y` is close at 14:00. That row is
   written. The 14:00 row is not (its y is 15:00's close,
   unknown).

3. build_features(include_target=True) drops the trailing row
   where `y` is NaN.

   Consequence: for a single-hour write, build_features(13:00,
   14:00, include_target=True) returns 1 row (y = close at
   14:00). For a single-hour write where the successor hour's
   close has not yet landed, build_features returns 0 rows.

   The writer treats 0 rows as "skip silently" and logs at debug
   level. This happens on the frontier during the writer lag,
   and is expected, not an error.

4. Row count for write_range is (end - start - 1) at most.

   The trailing row in [start, end) has a NaN `y` and is dropped
   by build_features. So a 24-hour range writes at most 23 rows.
   The writer documents this so callers aren't surprised.

5. No SplitProcessor.

   The DB writer does NOT go through SplitProcessor. It keeps
   warmup_complete == 0 rows and NaN active_addresses rows,
   because the AI Service's DB path reads the raw 53-column
   contract and filters however it wants. The parquet writer
   applies SplitProcessor separately. See migration 009's
   governance note.

6. Idempotency.

   FeaturesDBRepository.create_many uses
   ON CONFLICT (ds) DO NOTHING. Re-running is a no-op for hours
   already written.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.database.features_db_repository import (
    FeaturesDBRepository,
)
from app.services.feature_builder_service import (
    FeatureBuilderService,
)


logger = logging.getLogger(__name__)


def _floor_to_hour(dt: datetime) -> datetime:
    """Return dt truncated to the start of its UTC hour."""
    return dt.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


class FeaturesDBWriter:
    """
    Persist feature rows to features_db.

    Usage:

        db = SessionLocal()
        writer = FeaturesDBWriter(db)
        writer.write_current_hour()
        # or
        writer.write_range(start, end)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = FeaturesDBRepository(db)
        self.builder = FeatureBuilderService(db)

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def write_current_hour(self) -> bool:
        """
        Compute and persist the just-completed hour's feature row.

        Returns True if a row was written (or attempted — the
        repository's ON CONFLICT may skip it), False if the
        build produced no rows (successor close not yet
        available).

        Called by the scheduler at :05.
        """
        now = datetime.now(timezone.utc)
        current_hour = _floor_to_hour(now)
        target_hour = current_hour - timedelta(hours=1)

        logger.info(
            "FeaturesDBWriter: writing hour %s",
            target_hour.isoformat(),
        )

        return self._write_one(target_hour)

    def write_range(
        self,
        start: datetime,
        end: datetime,
    ) -> dict[str, Any]:
        """
        Compute and persist every hour in [start, end) whose `y`
        is known.

        Args:
            start: inclusive UTC, hour-aligned.
            end:   exclusive UTC, hour-aligned.

        Returns a summary dict:

            {
              "expected_hours":  int,   # (end - start) in hours
              "written":         int,   # rows attempted
              "skipped":         int,   # hours dropped for NaN y
              "already_present": int,   # hours already in DB
            }

        Note: "expected_hours" counts the raw span. The trailing
        hour has a NaN y and is always dropped by
        build_features(include_target=True), so "written +
        skipped" is at most (expected_hours - 1). See module
        docstring for detail.
        """
        start = _floor_to_hour(start)
        end = _floor_to_hour(end)

        if end <= start:
            raise ValueError(
                f"Invalid range: start={start.isoformat()} "
                f"end={end.isoformat()}"
            )

        expected = int((end - start).total_seconds() // 3600)

        # Skip hours already present, to keep the build small
        # on re-runs.
        existing = self.repository.existing_ds(start, end)
        logger.info(
            "FeaturesDBWriter: [%s, %s): %d expected, "
            "%d already present",
            start.isoformat(),
            end.isoformat(),
            expected,
            len(existing),
        )

        df = self.builder.build_features(start, end)

        if df.empty:
            logger.warning(
                "FeaturesDBWriter: build produced no rows for "
                "[%s, %s)",
                start.isoformat(),
                end.isoformat(),
            )
            return {
                "expected_hours": expected,
                "written": 0,
                "skipped": expected,
                "already_present": len(existing),
            }

        # Drop rows already present.
        if existing:
            df = df[~df.index.isin(existing)]

        if df.empty:
            logger.info(
                "FeaturesDBWriter: nothing new to write in "
                "[%s, %s)",
                start.isoformat(),
                end.isoformat(),
            )
            return {
                "expected_hours": expected,
                "written": 0,
                "skipped": 0,
                "already_present": len(existing),
            }

        records = self._frame_to_records(df)
        attempted = self.repository.create_many(records)

        # "skipped" is the count of hours in [start, end) that
        # were not written and not already present — i.e., the
        # trailing frontier hour(s).
        written_or_present = attempted + len(existing)
        skipped = expected - written_or_present
        if skipped < 0:
            # Should not happen; guard against off-by-one
            # surprises.
            skipped = 0

        summary = {
            "expected_hours": expected,
            "written": attempted,
            "skipped": skipped,
            "already_present": len(existing),
        }

        logger.info(
            "FeaturesDBWriter: [%s, %s) done: "
            "expected=%d written=%d skipped=%d already=%d",
            start.isoformat(),
            end.isoformat(),
            summary["expected_hours"],
            summary["written"],
            summary["skipped"],
            summary["already_present"],
        )

        return summary

    # ----------------------------------------------------------
    # Internals
    # ----------------------------------------------------------

    def _write_one(self, target_hour: datetime) -> bool:
        """
        Compute and persist exactly one hour's row.

        Returns True if the row existed after the call (either
        because it was freshly written or because it was already
        there), False if the build produced no row.
        """
        target_hour = _floor_to_hour(target_hour)
        end = target_hour + timedelta(hours=1)

        df = self.builder.build_features(target_hour, end)

        if df.empty:
            logger.debug(
                "FeaturesDBWriter: no row for %s "
                "(successor close not yet available)",
                target_hour.isoformat(),
            )
            return False

        records = self._frame_to_records(df)
        self.repository.create_many(records)

        logger.info(
            "FeaturesDBWriter: wrote %d row(s) for %s",
            len(records),
            target_hour.isoformat(),
        )
        return True

    @staticmethod
    def _frame_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Convert a build_features() DataFrame into a list of dicts
        matching FeaturesDBRepository.create_many's expected keys.

        The repository validates that every row has exactly the
        53 expected keys, so this method does no shape checking
        of its own — it just serializes.
        """
        records: list[dict[str, Any]] = []

        for ds, row in df.iterrows():
            record: dict[str, Any] = {"ds": ds}
            for col, value in row.items():
                # NaN -> None so the repository's integer casts
                # don't choke. Floats keep NaN? No: the schema
                # allows NULL for feature columns, so NaN becomes
                # None.
                if pd.isna(value):
                    record[col] = None
                else:
                    record[col] = value
            records.append(record)

        return records