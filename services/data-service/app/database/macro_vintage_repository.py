"""
Repository for macro_indicator_vintages.

All writes use ON CONFLICT (series_id, observation_date,
release_date) DO NOTHING so that:
  - re-running the vintage fetch is a no-op for already-stored
    (series_id, observation_date, release_date) triples
  - concurrent writers (scheduler + CLI backfill) do not race
  - historical vintages are immutable by default

Idempotency is critical for this table: the CLI backfill and the
daily scheduler task can overlap on the same window without
producing duplicates. The unique constraint
uq_macro_vintage_series_obs_release is what makes this work.

Pattern matches app/database/macro_indicator_repository.py and
the Chat 3 hourly repositories: batched insert, named-constraint
ON CONFLICT, single commit per create_many call.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Iterable

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.macro_indicator_vintage import (
    MacroIndicatorVintage,
)

logger = logging.getLogger(__name__)


# Insert in batches to avoid building one enormous statement for
# a full 20-year multi-series backfill. The value matches
# macro_indicator_repository.MAX_INSERT_BATCH_SIZE for
# consistency across repositories.
MAX_INSERT_BATCH_SIZE = 5_000


class MacroVintageRepository:
    """Database operations for macro_indicator_vintages."""

    def __init__(self, db: Session):
        self.db = db

    def create_many(
        self,
        vintages: list[dict[str, Any]],
    ) -> int:
        """
        Insert vintage rows, ignoring any whose
        (series_id, observation_date, release_date) triple
        already exists.

        Returns the number of rows attempted (not the number
        actually inserted — Postgres does not report that
        cheaply for a batch DO NOTHING).

        The input dicts must have exactly these keys:
            series_id, indicator_name, observation_date,
            release_date, value

        `created_at` is intentionally not required — the table
        default (now()) supplies it.
        """
        if not vintages:
            return 0

        for start in range(
            0,
            len(vintages),
            MAX_INSERT_BATCH_SIZE,
        ):
            batch = vintages[
                start:start + MAX_INSERT_BATCH_SIZE
            ]

            stmt = insert(
                MacroIndicatorVintage
            ).values(
                batch
            )

            stmt = stmt.on_conflict_do_nothing(
                constraint="uq_macro_vintage_series_obs_release"
            )

            self.db.execute(stmt)

        self.db.commit()

        logger.info(
            "Processed %d macro vintage records",
            len(vintages),
        )

        return len(vintages)

    def get_series(
        self,
        series_id: str,
        since: date | None = None,
    ) -> list[MacroIndicatorVintage]:
        """
        Return all vintage rows for one series, ordered by
        observation_date then release_date (both ascending).

        `since`, when provided, filters on observation_date >=
        since. Useful for reporting and for tests.

        Not on the hot path — the features writer (B4) does its
        own PIT query directly. This method is for operators and
        tests.
        """
        query = self.db.query(MacroIndicatorVintage).filter(
            MacroIndicatorVintage.series_id == series_id,
        )

        if since is not None:
            query = query.filter(
                MacroIndicatorVintage.observation_date >= since,
            )

        return (
            query.order_by(
                MacroIndicatorVintage.observation_date.asc(),
                MacroIndicatorVintage.release_date.asc(),
            )
            .all()
        )

    def latest_release_date(
        self,
        series_id: str,
    ) -> date | None:
        """
        Return the maximum release_date stored for one series,
        or None if the series has no rows.

        Used by the CLI to report how current each series is,
        and by future incremental backfills to determine where
        to resume.

        Implementation note: MAX() ignores NULLs, and
        release_date is NOT NULL by schema, so the only way
        this returns None is when the series has no rows at
        all.
        """
        result = (
            self.db.query(
                func.max(MacroIndicatorVintage.release_date)
            )
            .filter(
                MacroIndicatorVintage.series_id == series_id,
            )
            .scalar()
        )

        return result

    def count_by_series(self) -> dict[str, int]:
        """
        Return a {series_id: row_count} mapping across the whole
        table.

        Diagnostic only. Used by the CLI to print a per-series
        summary at the end of a backfill run, and by tests to
        assert row counts without knowing the full row set.

        One GROUP BY query; no N+1.
        """
        rows = (
            self.db.query(
                MacroIndicatorVintage.series_id,
                func.count(MacroIndicatorVintage.id),
            )
            .group_by(MacroIndicatorVintage.series_id)
            .all()
        )

        return {series_id: count for series_id, count in rows}