"""
Service for computing the high_yield_credit_stress_proxy feature.

The proxy is a daily derived market signal:

    (HYG / SHY).pct_change()

HYG is the iShares iBoxx $ High Yield Corporate Bond ETF.
SHY is the iShares 1-3 Year Treasury Bond ETF.

The ratio HYG/SHY rises when high-yield credit is outperforming
short-term treasuries (credit conditions healthy) and falls when
it is underperforming (credit conditions stressed). The
day-over-day percent change of that ratio is the proxy: negative
values indicate credit stress increasing, positive values
indicate it easing.

This value is consumed by features_db as the
high_yield_credit_stress_proxy column (see
docs/data-service-schemas.md §5, row 14). The features writer
treats it as a market feature and ffills it without a limit.

Design notes
------------

1. Timestamp convention: midnight UTC.

   Each observation is written with time = 00:00:00 UTC on the
   observation day, NOT datetime.now().

   This is required for two reasons:

     a. Idempotency. The raw macro_indicators table has a unique
        constraint on (time, indicator_name). Midnight UTC means
        "the value for day D" always lands on the same timestamp,
        so re-running the service on the same day is a no-op.
        datetime.now() would produce a different timestamp on
        every run and the ON CONFLICT clause would never fire.

     b. PIT correctness. The features writer picks the latest
        observation with time <= the feature hour. Midnight UTC
        means the value for day D is available to every hour of
        day D, which is what a daily series means. datetime.now()
        would leave a gap between midnight and the job's run time.

   This differs from gold_spot, which uses datetime.now() because
   it is a point-in-time snapshot rather than a daily series.
   The divergence is deliberate.

2. Idempotency is delegated entirely to the repository.

   MacroIndicatorRepository.create_many uses
   ON CONFLICT (time, indicator_name) DO NOTHING. The service
   does not pre-check for existing rows; it just asks Yahoo for
   the last HY_PROXY_LOOKBACK_DAYS of history and lets the
   database deduplicate. This keeps the service stateless and
   makes a wide lookback window effectively free on a healthy
   system.

3. Source and indicator name.

   Written with:
       indicator_name = "high_yield_credit_stress_proxy"
       source         = "derived"

   "derived" because this is not a provider-published series;
   it is computed by us from two ETF price series.

4. Failure mode.

   If Yahoo returns no data for either symbol, the service
   returns [] and the scheduler logs a warning. Nothing is
   written. This matches GoldSpotService.collect()'s behavior
   on missing data.

   If Yahoo raises (network error, non-2xx), the exception
   propagates to the scheduler, which wraps the call in a
   try/except and logs a traceback. The scheduler's loop
   continues.

5. Error handling inside collect().

   Rows where (HYG/SHY).pct_change() is NaN are skipped:

     - The very first row is always NaN (pct_change has no
       prior value to compare against).

     - Any row whose prior ratio is zero or NaN is NaN.

   These are dropped before building records. We never write
   NaN into macro_indicators.value, which is NOT NULL.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from app.collectors.yahoo_finance import YahooFinanceCollector
from app.config import settings
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)

logger = logging.getLogger(__name__)


HY_PROXY_INDICATOR = "high_yield_credit_stress_proxy"
HY_PROXY_SOURCE = "derived"

HYG_SYMBOL = "HYG"
SHY_SYMBOL = "SHY"


class HighYieldCreditStressService:
    """
    Compute and persist the high_yield_credit_stress_proxy feature.

    Writes one row per trading day into the raw macro_indicators
    table. Idempotent: re-running on the same day writes nothing
    new, thanks to the (time, indicator_name) unique constraint
    in the repository.
    """

    def __init__(
        self,
        db,
        collector: YahooFinanceCollector | None = None,
    ):
        self.repository = MacroIndicatorRepository(db)
        self.collector = collector or YahooFinanceCollector()
        self._owns_collector = collector is None

    async def close(self) -> None:
        """
        Close the Yahoo Finance collector when owned by this
        service.

        If the caller passed their own collector, we do not close
        it — the caller owns its lifecycle. Mirrors
        GoldSpotService.close().
        """
        if self._owns_collector:
            await self.collector.close()

    async def collect(self) -> list[dict[str, Any]]:
        """
        Fetch HYG and SHY, compute the proxy, and return records
        ready for MacroIndicatorRepository.create_many.

        Returns:
            A list of dicts, one per trading day whose proxy value
            is not NaN:

                {
                    "indicator_name": "high_yield_credit_stress_proxy",
                    "time":           datetime at midnight UTC,
                    "value":          float,
                    "previous_value": None,
                    "change_percent": None,
                    "source":         "derived",
                }

            Empty list if either symbol has no data, if the ratio
            has fewer than two rows (so no pct_change can be
            computed), or if all rows are NaN after pct_change.
        """

        range_ = f"{settings.HY_PROXY_LOOKBACK_DAYS}d"

        hyg_records = await self.collector.get_daily_history(
            HYG_SYMBOL,
            range_=range_,
            interval="1d",
        )

        shy_records = await self.collector.get_daily_history(
            SHY_SYMBOL,
            range_=range_,
            interval="1d",
        )

        if not hyg_records or not shy_records:
            logger.warning(
                "HY proxy: missing input data "
                "(HYG rows=%d, SHY rows=%d)",
                len(hyg_records),
                len(shy_records),
            )
            return []

        # ------------------------------------------------------
        # Build a 1D Series of close prices per symbol, indexed
        # by the observation date (UTC).
        # ------------------------------------------------------

        hyg = _records_to_series(hyg_records)
        shy = _records_to_series(shy_records)

        # ------------------------------------------------------
        # Align by date. Inner join: only days where BOTH ETFs
        # traded. This is the same implicit alignment the
        # original scripts got from DataFrame construction.
        # ------------------------------------------------------

        combined = pd.concat(
            [hyg.rename("HYG"), shy.rename("SHY")],
            axis=1,
            join="inner",
        ).dropna()

        if len(combined) < 2:
            logger.warning(
                "HY proxy: fewer than 2 aligned trading days "
                "(rows=%d); cannot compute pct_change",
                len(combined),
            )
            return []

        # ------------------------------------------------------
        # Compute the proxy: (HYG / SHY).pct_change()
        # ------------------------------------------------------

        ratio = combined["HYG"] / combined["SHY"]
        proxy = ratio.pct_change()

        # ------------------------------------------------------
        # Drop NaN rows. The first row is always NaN; interior
        # NaN can appear if a ratio was 0 or NaN.
        # ------------------------------------------------------

        proxy = proxy.dropna()

        if proxy.empty:
            logger.warning(
                "HY proxy: no non-NaN values after pct_change"
            )
            return []

        # ------------------------------------------------------
        # Build records with midnight-UTC timestamps.
        # ------------------------------------------------------

        records: list[dict[str, Any]] = []

        for date, value in proxy.items():
            # `date` is a pandas Timestamp (tz-naive), the
            # observation day in UTC from the Yahoo timestamps.
            observation_time = datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
                tzinfo=timezone.utc,
            )

            records.append(
                {
                    "indicator_name": HY_PROXY_INDICATOR,
                    "time": observation_time,
                    "value": float(value),
                    "previous_value": None,
                    "change_percent": None,
                    "source": HY_PROXY_SOURCE,
                }
            )

        logger.info(
            "HY proxy: computed %d observation(s) "
            "(range: %s -> %s)",
            len(records),
            records[0]["time"].date() if records else "-",
            records[-1]["time"].date() if records else "-",
        )

        return records


# ==========================================================
# Internal helpers
# ==========================================================


def _records_to_series(
    records: list[dict[str, Any]],
) -> pd.Series:
    """
    Convert a list of YahooFinanceCollector history records into
    a pandas Series of close prices, indexed by observation date
    (tz-naive, UTC).

    Yahoo returns one record per trading day with a Unix-second
    timestamp. Duplicate dates (rare but possible if Yahoo emits
    two candles for the same calendar day) are collapsed by
    keeping the last, matching the scripts' implicit dedup.
    """

    dates = pd.to_datetime(
        [record["timestamp"] for record in records],
        unit="s",
        utc=True,
    )

    # Normalize to midnight UTC so both symbols align on the
    # same calendar day regardless of the exact exchange open
    # time Yahoo recorded.
    dates = dates.normalize()

    # Drop tz before building the Series so indexing against
    # `proxy.items()` yields tz-naive Timestamps, which is what
    # the record builder above expects.
    dates = dates.tz_localize(None)

    series = pd.Series(
        [record["price"] for record in records],
        index=dates,
        dtype="float64",
    )

    # Keep the last value per day if Yahoo emitted duplicates.
    series = series[~series.index.duplicated(keep="last")]

    series = series.sort_index()

    return series