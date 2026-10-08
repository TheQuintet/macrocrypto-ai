"""
Materialize btc_prices_hourly from raw tables.

Reads:
    - raw btc_prices (ticks)
    - raw btc_dominance
    - raw macro_indicators (for indicator_name='active_addresses')

Writes:
    - btc_prices_hourly

Missingness policy (locked in Chat 3, do not change without
sign-off):

    close, volume:
        Skip the entire hour if no btc_prices tick exists in
        [hour, hour+1). Do not write a NULL-close row.
        Do not carry forward.

    volatility:
        NULL if fewer than 2 ticks.
        Otherwise std(ddof=1) of log returns of consecutive
        ticks within the hour. NOT annualized.

    dominance:
        Latest btc_dominance row with time <= hour.
        NULL if none exists. No age limit.

    active_addresses:
        Latest raw macro_indicators row with
        indicator_name='active_addresses' and time <= hour.
        NULL if none exists. No age limit.

    price_lag_7d:
        close from the btc_prices_hourly row at exactly
        hour - 7 days. NULL if that row does not exist.

    created_at:
        now().
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.btc_prices_hourly_repository import (
    BTCPriceHourlyRepository,
)

logger = logging.getLogger(__name__)


ONE_HOUR = timedelta(hours=1)
SEVEN_DAYS = timedelta(days=7)

ACTIVE_ADDRESSES_INDICATOR = "active_addresses"


def _floor_to_hour(dt: datetime) -> datetime:
    """Return dt truncated to the start of its UTC hour."""
    return dt.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )


def _last_completed_hour(now: datetime | None = None) -> datetime:
    """
    Return the timestamp of the last hour whose row is complete.

    Example: if now is 14:35, the current hour is [14:00, 15:00),
    which is still in progress. The last completed hour is
    13:00-14:00, whose row has time = 14:00.

    So this function returns the *hour boundary* of the last
    completed hour, which is the timestamp used as the row's
    primary key.
    """
    now = now or datetime.now(timezone.utc)
    return _floor_to_hour(now)


class HourlyBTCPricesService:
    """Materialize btc_prices_hourly."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = BTCPriceHourlyRepository(db)

    # ------------------------------------------------------------------
    # FETCH
    # ------------------------------------------------------------------

    def fetch_hour_bucket(
        self,
        hour: datetime,
    ) -> dict[str, Any] | None:
        """
        Read the raw data for [hour, hour+1).

        Returns None if the hour has no btc_prices ticks; the
        caller interprets that as "skip this hour".

        Returns a dict with:
            close, volume, volatility
        """
        hour = _floor_to_hour(hour)
        next_hour = hour + ONE_HOUR

        rows = self.db.execute(
            text(
                """
                SELECT time, price, volume
                FROM btc_prices
                WHERE time >= :start AND time < :end
                ORDER BY time ASC
                """
            ),
            {"start": hour, "end": next_hour},
        ).all()

        if not rows:
            return None

        prices = [float(r[1]) for r in rows]
        volumes = [float(r[2]) for r in rows if r[2] is not None]

        close = prices[-1]
        volume = sum(volumes) if volumes else None

        volatility = self._compute_volatility(prices)

        return {
            "close": close,
            "volume": volume,
            "volatility": volatility,
        }

    @staticmethod
    def _compute_volatility(prices: list[float]) -> float | None:
        """
        std(ddof=1) of log returns of consecutive prices.

        Returns None if fewer than 2 prices.
        """
        if len(prices) < 2:
            return None

        log_returns: list[float] = []
        for prev, curr in zip(prices, prices[1:]):
            if prev <= 0 or curr <= 0:
                continue
            log_returns.append(math.log(curr / prev))

        if len(log_returns) < 2:
            return None

        n = len(log_returns)
        mean = sum(log_returns) / n
        variance = sum((r - mean) ** 2 for r in log_returns) / (n - 1)
        return math.sqrt(variance)

    def _fetch_dominance(self, hour: datetime) -> float | None:
        row = self.db.execute(
            text(
                """
                SELECT dominance
                FROM btc_dominance
                WHERE time <= :hour
                ORDER BY time DESC
                LIMIT 1
                """
            ),
            {"hour": hour},
        ).first()
        return float(row[0]) if row and row[0] is not None else None

    def _fetch_active_addresses(self, hour: datetime) -> float | None:
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
            {"name": ACTIVE_ADDRESSES_INDICATOR, "hour": hour},
        ).first()
        return float(row[0]) if row and row[0] is not None else None

    def _fetch_price_lag_7d(self, hour: datetime) -> float | None:
        target = hour - SEVEN_DAYS
        row = self.repository.get_by_time(target)
        return float(row.close) if row and row.close is not None else None

    # ------------------------------------------------------------------
    # BUILD
    # ------------------------------------------------------------------

    def build_hour_row(
        self,
        hour: datetime,
    ) -> dict[str, Any] | None:
        """
        Build the row for a given hour.

        Returns None if there are no raw ticks for this hour —
        the caller should skip the hour entirely.
        """
        hour = _floor_to_hour(hour)

        bucket = self.fetch_hour_bucket(hour)
        if bucket is None:
            return None

        return {
            "time": hour,
            "close": bucket["close"],
            "volume": bucket["volume"],
            "volatility": bucket["volatility"],
            "dominance": self._fetch_dominance(hour),
            "active_addresses": self._fetch_active_addresses(hour),
            "price_lag_7d": self._fetch_price_lag_7d(hour),
        }

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

        Returns True if a row was built (and, unless dry_run,
        attempted to be written). Returns False if the hour had
        no raw ticks and was skipped.
        """
        hour = _floor_to_hour(hour)
        row = self.build_hour_row(hour)

        if row is None:
            logger.debug(
                "[BTC-HOURLY] skip %s (no raw ticks)", hour.isoformat()
            )
            return False

        if dry_run:
            logger.info(
                "[BTC-HOURLY] dry-run would write %s: close=%s vol=%s",
                hour.isoformat(),
                row["close"],
                row["volatility"],
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
        Materialize btc_prices_hourly for every hour in
        [start, end).

        start: inclusive, snapped down to the hour.
        end:   exclusive, snapped down to the hour, and clamped
               to the last completed hour.

        Returns a summary dict:
            {
              "expected_hours":  int,
              "written":         int,   # hours with rows built
              "skipped_no_data": int,   # hours with no raw ticks
              "already_present": int,   # hours already in DB
              "missing":         list[datetime]  # only if verify_only
            }

        verify_only: if True, no writes. Reports which hours would
        have been built vs. skipped, and lists any hours that are
        missing from the table currently.
        """
        start = _floor_to_hour(start)
        end = _floor_to_hour(end)

        last_completed = _last_completed_hour()
        if end > last_completed:
            logger.warning(
                "[BTC-HOURLY] clamping end %s to last completed hour %s",
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
        skipped = 0
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
                bucket = self.fetch_hour_bucket(hour)
                if bucket is None:
                    skipped += 1
                else:
                    missing.append(hour)
            else:
                did_write = self.write_hour(hour, dry_run=dry_run)
                if did_write:
                    written += 1
                else:
                    skipped += 1

            if idx % 1000 == 0:
                logger.info(
                    "[BTC-HOURLY] progress %d/%d hours (%d%%)",
                    idx,
                    expected,
                    int(100 * idx / expected),
                )

            hour += ONE_HOUR

        summary = {
            "expected_hours": expected,
            "written": written,
            "skipped_no_data": skipped,
            "already_present": already,
        }
        if verify_only:
            summary["missing"] = missing

        logger.info(
            "[BTC-HOURLY] backfill done: expected=%d written=%d "
            "skipped=%d already=%d",
            expected,
            written,
            skipped,
            already,
        )
        return summary