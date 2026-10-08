"""
Repository for features_db.

All writes use ON CONFLICT (ds) DO NOTHING so that:
    - re-running the feature writer is a no-op for hours already
      stored
    - concurrent writers (scheduler + CLI backfill) do not race
    - historical rows are immutable by default

Pattern matches app/database/macro_vintage_repository.py and
the Chat 3 hourly repositories: batched insert, single commit
per create_many call, no pre-check (the ON CONFLICT clause is
the deduplication mechanism).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.features_db import FeaturesDB


logger = logging.getLogger(__name__)


# Insert in batches to avoid building one enormous statement
# for a multi-year backfill. The value matches
# MacroIndicatorRepository.MAX_INSERT_BATCH_SIZE and
# MacroVintageRepository.MAX_INSERT_BATCH_SIZE for consistency
# across repositories. Note: at hourly resolution, 5000 rows is
# about 7 months of data per batch.
MAX_INSERT_BATCH_SIZE = 5_000


# The 53 columns of features_db, in schema order. Used to
# validate incoming record dicts so a caller that forgets a
# column fails loudly here rather than at insert time with a
# cryptic psycopg error.
_COLUMNS = (
    # 2 — timestamp and target
    "ds",
    "y",
    # 4 — raw market & on-chain
    "btc_price",
    "btc_volume",
    "btc_dominance",
    "active_addresses",
    # 13 — macro & external assets
    "gold_spot",
    "dxy",
    "ten_year_treasury",
    "vix",
    "high_yield_spread",
    "nasdaq_composite",
    "equity_corr",
    "high_yield_credit_stress_proxy",
    "cpi",
    "federal_funds_rate",
    "gdp",
    "m2_money_supply",
    "unemployment",
    # 10 — technical indicators & ratios
    "btc_log_return_1d",
    "btc_log_return_7d",
    "btc_log_return_30d",
    "btc_sma_7",
    "btc_sma_30",
    "btc_sma_90",
    "btc_volatility_7d",
    "btc_volatility_30d",
    "btc_gold_ratio",
    "btc_nasdaq_ratio",
    # 4 — data-quality flags
    "high_yield_spread_is_missing",
    "active_addresses_is_imputed",
    "unemployment_is_imputed",
    "warmup_complete",
    # 14 — observation recency trackers
    "btc_dominance_days_since_last_observation",
    "gold_spot_days_since_last_observation",
    "dxy_days_since_last_observation",
    "ten_year_treasury_days_since_last_observation",
    "vix_days_since_last_observation",
    "nasdaq_composite_days_since_last_observation",
    "equity_corr_days_since_last_observation",
    "high_yield_credit_stress_proxy_days_since_last_observation",
    "active_addresses_days_since_last_observation",
    "cpi_days_since_release",
    "federal_funds_rate_days_since_release",
    "gdp_days_since_release",
    "m2_money_supply_days_since_release",
    "unemployment_days_since_release",
    # 6 — engineered features
    "eng_price_lag_1d",
    "eng_price_lag_7d",
    "eng_price_lag_30d",
    "eng_returns_1d",
    "eng_returns_7d",
    "eng_returns_30d",
)


class FeaturesDBRepository:
    """Database operations for features_db."""

    def __init__(self, db: Session):
        self.db = db

    def create_many(
        self,
        rows: list[dict[str, Any]],
    ) -> int:
        """
        Insert feature rows, ignoring any whose ds already exists.

        Returns the number of rows attempted (not the number
        actually inserted — Postgres does not report that
        cheaply for a batch DO NOTHING).

        Each dict must have exactly the 53 column keys listed in
        _COLUMNS. Missing or extra keys raise ValueError before
        the database sees the batch. This catches bugs in
        build_features() early.
        """
        if not rows:
            return 0

        expected = set(_COLUMNS)
        for i, row in enumerate(rows):
            actual = set(row.keys())
            if actual != expected:
                missing = sorted(expected - actual)
                extra = sorted(actual - expected)
                raise ValueError(
                    f"features_db row {i} has wrong keys: "
                    f"missing={missing}, extra={extra}"
                )

        for start in range(
            0,
            len(rows),
            MAX_INSERT_BATCH_SIZE,
        ):
            batch = rows[
                start:start + MAX_INSERT_BATCH_SIZE
            ]

            stmt = insert(FeaturesDB).values(batch)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["ds"]
            )

            self.db.execute(stmt)

        self.db.commit()

        logger.info(
            "Processed %d features_db record(s)",
            len(rows),
        )

        return len(rows)

    def get_by_ds(
        self,
        ds: datetime,
    ) -> FeaturesDB | None:
        """Return the feature row for a specific hour, or None."""
        return (
            self.db.query(FeaturesDB)
            .filter(FeaturesDB.ds == ds)
            .first()
        )

    def existing_ds(
        self,
        start: datetime,
        end: datetime,
    ) -> set[datetime]:
        """
        Return the set of ds values already present in
        [start, end). Used by backfill to skip work.

        Matches the shape of BTCPriceHourlyRepository.existing_hours
        and MacroIndicatorHourlyRepository.existing_hours.
        """
        rows = (
            self.db.query(FeaturesDB.ds)
            .filter(
                FeaturesDB.ds >= start,
                FeaturesDB.ds < end,
            )
            .all()
        )
        return {row[0] for row in rows}

    def latest_ds(self) -> datetime | None:
        """
        Return the maximum ds stored, or None if the table is
        empty. Used by the CLI to report freshness and by future
        incremental writers.
        """
        return (
            self.db.query(FeaturesDB.ds)
            .order_by(FeaturesDB.ds.desc())
            .limit(1)
            .scalar()
        )

    def count_in_range(
        self,
        start: datetime,
        end: datetime,
    ) -> int:
        """
        Count rows in [start, end). Diagnostic only; used by the
        CLI to report what a backfill actually landed.
        """
        return (
            self.db.query(FeaturesDB)
            .filter(
                FeaturesDB.ds >= start,
                FeaturesDB.ds < end,
            )
            .count()
        )