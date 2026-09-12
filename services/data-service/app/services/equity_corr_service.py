"""
Service for calculating the derived equity_corr feature.

equity_corr measures the rolling relationship between daily BTC returns
and daily NASDAQ Composite returns.

The feature is leakage-free: the value for day T only uses information
available through day T-1.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from app.collectors.binance import BinanceCollector
from app.config import settings
from app.database.macro_indicator_repository import (
    MacroIndicatorRepository,
)

logger = logging.getLogger(__name__)

EQUITY_CORR_INDICATOR = "equity_corr"
NASDAQ_INDICATOR = "nasdaq_composite"

ROLLING_WINDOW = 30
MIN_PERIODS = 30

# Extra history is required because:
# 1. daily returns require a previous price
# 2. the feature uses a 30-observation rolling window
LOOKBACK_DAYS = 60


class EquityCorrService:
    """Calculate and prepare the derived equity_corr feature."""

    def __init__(
        self,
        db,
        collector: BinanceCollector | None = None,
    ):
        self.repository = MacroIndicatorRepository(db)
        self.collector = collector or BinanceCollector()
        self._owns_collector = collector is None

    async def close(self) -> None:
        """Close the Binance collector when owned by this service."""
        if self._owns_collector:
            await self.collector.close()

    async def calculate(self) -> list[dict[str, Any]]:
        """
        Calculate the 30-day leakage-free BTC/NASDAQ correlation.

        Returns:
            Derived macro-indicator records ready for persistence.
        """

        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=LOOKBACK_DAYS)

        # --------------------------------------------------
        # 1. Get historical NASDAQ observations
        # --------------------------------------------------

        nasdaq_rows = self.repository.get_historical_data(
            indicator_name=NASDAQ_INDICATOR,
            days=LOOKBACK_DAYS,
        )

        if not nasdaq_rows:
            logger.warning(
                "No NASDAQ Composite data available for equity_corr"
            )
            return []

        # --------------------------------------------------
        # 2. Get historical daily BTC candles
        # --------------------------------------------------

        btc_candles = await self.collector.get_klines(
            symbol=settings.BINANCE_DEFAULT_SYMBOL,
            interval="1d",
            limit=1000,
            start_time=int(start_time.timestamp() * 1000),
            end_time=int(end_time.timestamp() * 1000),
        )

        if not btc_candles:
            logger.warning(
                "No BTC daily data available for equity_corr"
            )
            return []

        # --------------------------------------------------
        # 3. Build normalized daily datasets
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

        nasdaq_df = pd.DataFrame(
            {
                "date": [
                    row.time.astimezone(timezone.utc).date()
                    for row in nasdaq_rows
                ],
                "nasdaq_close": [
                    float(row.value)
                    for row in nasdaq_rows
                ],
            }
        )

        # --------------------------------------------------
        # 4. Align by actual calendar date
        # --------------------------------------------------

        df = pd.merge(
            btc_df,
            nasdaq_df,
            on="date",
            how="inner",
        ).sort_values("date")

        if df.empty:
            logger.warning(
                "No overlapping BTC/NASDAQ dates available "
                "for equity_corr"
            )
            return []

        logger.info(
            "equity_corr input counts: BTC=%d, NASDAQ=%d, aligned=%d",
            len(btc_df),
            len(nasdaq_df),
            len(df),
        )

        # --------------------------------------------------
        # 5. Calculate daily returns
        # --------------------------------------------------

        df["btc_return"] = df["btc_close"].pct_change()
        df["nasdaq_return"] = df["nasdaq_close"].pct_change()

        # --------------------------------------------------
        # 6. Information barrier
        #
        # equity_corr(T) must not use prices/returns from T.
        # --------------------------------------------------

        df["historical_btc_return"] = df["btc_return"].shift(1)
        df["historical_nasdaq_return"] = df["nasdaq_return"].shift(1)

        logger.info(
            "equity_corr valid shifted returns: BTC=%d, NASDAQ=%d",
            df["historical_btc_return"].notna().sum(),
            df["historical_nasdaq_return"].notna().sum(),
        )

        # --------------------------------------------------
        # 7. Calculate 30-observation rolling correlation
        # --------------------------------------------------

        df[EQUITY_CORR_INDICATOR] = (
            df["historical_btc_return"]
            .rolling(
                window=ROLLING_WINDOW,
                min_periods=MIN_PERIODS,
            )
            .corr(df["historical_nasdaq_return"])
        )

        logger.info(
            "equity_corr valid correlations: %d",
            df[EQUITY_CORR_INDICATOR].notna().sum(),
        )

        # --------------------------------------------------
        # 8. Build derived records
        # --------------------------------------------------

        records: list[dict[str, Any]] = []

        for _, row in df.iterrows():
            correlation = row[EQUITY_CORR_INDICATOR]

            if pd.isna(correlation):
                continue

            records.append(
                {
                    "indicator_name": EQUITY_CORR_INDICATOR,
                    "time": datetime.combine(
                        row["date"],
                        datetime.min.time(),
                        tzinfo=timezone.utc,
                    ),
                    "value": round(float(correlation), 4),
                    "previous_value": None,
                    "change_percent": None,
                    "source": "derived",
                }
            )

        logger.info(
            "Calculated %s equity_corr records",
            len(records),
        )

        return records