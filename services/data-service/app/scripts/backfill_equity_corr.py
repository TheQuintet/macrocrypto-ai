"""
One-time backfill for the equity_corr macro indicator.

Calculates historical 30-observation rolling correlation between
daily BTC returns and daily NASDAQ Composite returns.

The calculation matches EquityCorrService:
- actual overlapping dates only
- no forward-filling of NASDAQ
- daily returns
- shift(1) information barrier
- 30-observation rolling correlation
- source="derived"

Run from the data-service root:

    python -m app.scripts.backfill_equity_corr
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import pandas as pd

from app.collectors.binance import BinanceCollector
from app.config import settings
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)
from app.database.session import SessionLocal


logger = logging.getLogger(__name__)

EQUITY_CORR_INDICATOR = "equity_corr"
NASDAQ_INDICATOR = "nasdaq_composite"

ROLLING_WINDOW = 30
MIN_PERIODS = 30

# BTC price history currently begins around this date.
# This is the requested start of the historical equity_corr backfill.
BACKFILL_START = datetime(2017, 8, 17, tzinfo=timezone.utc)


async def backfill_equity_corr() -> None:
    """Calculate and persist historical equity_corr records."""

    end_time = datetime.now(timezone.utc)

    calculation_start = BACKFILL_START.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    logger.info(
        "Starting equity_corr backfill: %s -> %s",
        calculation_start.date(),
        end_time.date(),
    )

    db = SessionLocal()
    collector = BinanceCollector()

    try:
        repository = MacroIndicatorRepository(db)

        # --------------------------------------------------
        # 1. Load NASDAQ history from the database
        # --------------------------------------------------

        lookback_days = (
            end_time - calculation_start
        ).days

        nasdaq_rows = repository.get_historical_data(
            indicator_name=NASDAQ_INDICATOR,
            days=lookback_days + 60,
        )

        if not nasdaq_rows:
            logger.error(
                "No NASDAQ Composite observations found."
            )
            return

        logger.info(
            "Loaded %d NASDAQ observations",
            len(nasdaq_rows),
        )

        # --------------------------------------------------
        # 2. Load historical BTC daily candles
        # --------------------------------------------------

        btc_candles = await collector.get_klines(
            symbol=settings.BINANCE_DEFAULT_SYMBOL,
            interval="1d",
            limit=1000,
            start_time=int(
                calculation_start.timestamp() * 1000
            ),
            end_time=int(
                end_time.timestamp() * 1000
            ),
        )

        if not btc_candles:
            logger.error(
                "No BTC daily candles returned from Binance."
            )
            return

        logger.info(
            "Loaded %d BTC daily candles",
            len(btc_candles),
        )

        # --------------------------------------------------
        # 3. Build normalized daily BTC dataset
        # --------------------------------------------------

        btc_df = pd.DataFrame(
            {
                "date": [
                    datetime.fromtimestamp(
                        candle["open_time"] / 1000,
                        tz=timezone.utc,
                    ).date()
                    for candle in btc_candles
                ],
                "btc_close": [
                    float(candle["close"])
                    for candle in btc_candles
                ],
            }
        )

        # --------------------------------------------------
        # 4. Build normalized daily NASDAQ dataset
        # --------------------------------------------------

        nasdaq_df = pd.DataFrame(
            {
                "date": [
                    row.time.astimezone(
                        timezone.utc
                    ).date()
                    for row in nasdaq_rows
                ],
                "nasdaq_close": [
                    float(row.value)
                    for row in nasdaq_rows
                ],
            }
        )

        # Remove duplicate dates defensively.
        btc_df = (
            btc_df
            .drop_duplicates(subset=["date"])
            .sort_values("date")
            .reset_index(drop=True)
        )

        nasdaq_df = (
            nasdaq_df
            .drop_duplicates(subset=["date"])
            .sort_values("date")
            .reset_index(drop=True)
        )

        logger.info(
            "Normalized datasets: BTC=%d, NASDAQ=%d",
            len(btc_df),
            len(nasdaq_df),
        )

        # --------------------------------------------------
        # 5. Align by actual overlapping dates
        #
        # Do NOT forward-fill NASDAQ.
        #
        # This ensures returns are calculated from actual
        # market observations only.
        # --------------------------------------------------

        df = (
            pd.merge(
                btc_df,
                nasdaq_df,
                on="date",
                how="inner",
            )
            .sort_values("date")
            .reset_index(drop=True)
        )

        if df.empty:
            logger.error(
                "No overlapping BTC/NASDAQ dates found."
            )
            return

        logger.info(
            "Aligned BTC/NASDAQ observations: %d",
            len(df),
        )

        logger.info(
            "Aligned date range: %s -> %s",
            df["date"].min(),
            df["date"].max(),
        )

        # --------------------------------------------------
        # 6. Calculate daily returns
        # --------------------------------------------------

        df["btc_return"] = (
            df["btc_close"].pct_change()
        )

        df["nasdaq_return"] = (
            df["nasdaq_close"].pct_change()
        )

        # --------------------------------------------------
        # 7. Apply information barrier
        #
        # equity_corr(T) must not use prices/returns from T.
        #
        # Therefore the correlation assigned to T only uses
        # returns available through T-1.
        # --------------------------------------------------

        df["historical_btc_return"] = (
            df["btc_return"].shift(1)
        )

        df["historical_nasdaq_return"] = (
            df["nasdaq_return"].shift(1)
        )

        logger.info(
            "Valid shifted BTC returns: %d",
            df["historical_btc_return"].notna().sum(),
        )

        logger.info(
            "Valid shifted NASDAQ returns: %d",
            df["historical_nasdaq_return"].notna().sum(),
        )

        # --------------------------------------------------
        # 8. Calculate 30-observation rolling correlation
        # --------------------------------------------------

        df[EQUITY_CORR_INDICATOR] = (
            df["historical_btc_return"]
            .rolling(
                window=ROLLING_WINDOW,
                min_periods=MIN_PERIODS,
            )
            .corr(
                df["historical_nasdaq_return"]
            )
        )

        valid_correlations = df[
            EQUITY_CORR_INDICATOR
        ].notna().sum()

        logger.info(
            "Valid equity_corr correlations: %d",
            valid_correlations,
        )

        # --------------------------------------------------
        # 9. Restrict output to requested backfill range
        # --------------------------------------------------

        df = df[
            df["date"] >= calculation_start.date()
        ].copy()

        valid_df = df[
            df[EQUITY_CORR_INDICATOR].notna()
        ].copy()

        if valid_df.empty:
            logger.warning(
                "No valid equity_corr records generated."
            )
            return

        # --------------------------------------------------
        # 10. Build database records
        # --------------------------------------------------

        records = []

        for _, row in valid_df.iterrows():
            correlation = row[EQUITY_CORR_INDICATOR]

            records.append(
                {
                    "indicator_name": EQUITY_CORR_INDICATOR,
                    "time": datetime.combine(
                        row["date"],
                        datetime.min.time(),
                        tzinfo=timezone.utc,
                    ),
                    "value": round(
                        float(correlation),
                        4,
                    ),
                    "previous_value": None,
                    "change_percent": None,
                    "source": "derived",
                }
            )

        logger.info(
            "Prepared %d equity_corr records for persistence",
            len(records),
        )

        # --------------------------------------------------
        # 11. Persist using existing repository
        #
        # create_many() uses the existing unique constraint:
        #
        # (time, indicator_name)
        #
        # Therefore rerunning this script is safe.
        # --------------------------------------------------

        repository.create_many(records)

        logger.info(
            "Equity_corr backfill completed successfully."
        )

        logger.info(
            "Processed %d records.",
            len(records),
        )

        logger.info(
            "Backfill range: %s -> %s",
            valid_df["date"].min(),
            valid_df["date"].max(),
        )

    except Exception:
        logger.exception(
            "Equity_corr backfill failed."
        )
        raise

    finally:
        await collector.close()
        db.close()


if __name__ == "__main__":
    asyncio.run(
        backfill_equity_corr()
    )

