"""
Backfill historical daily BTC prices from Binance into btc_prices.

Uses Binance REST klines and preserves the original candle timestamps.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from app.collectors.binance import BinanceCollector
from app.config import settings
from app.database.btc_price_repository import BTCPriceRepository

logger = logging.getLogger(__name__)

# # ~6 years of daily data.
# BACKFILL_DAYS = 6 * 365
# Explicit historical start for BTCUSDT daily backfill.
BACKFILL_START = datetime(2017, 8, 1, tzinfo=timezone.utc)

BINANCE_INTERVAL = "1d"
BINANCE_LIMIT = 1000
SOURCE = "binance_backfill"


async def backfill_btc_prices() -> None:
    """Fetch and persist historical daily BTC candles."""
    end_time = datetime.now(timezone.utc)
    start_time = BACKFILL_START

    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    logger.info(
        "Starting BTC historical backfill: %s -> %s",
        start_time.isoformat(),
        end_time.isoformat(),
    )

    collector = BinanceCollector()
    repository = BTCPriceRepository()

    try:
        candles = await collector.get_klines(
            symbol=settings.BINANCE_DEFAULT_SYMBOL,
            interval=BINANCE_INTERVAL,
            limit=BINANCE_LIMIT,
            start_time=start_ms,
            end_time=end_ms,
        )

        if not candles:
            logger.warning("No BTC historical candles returned")
            return

        logger.info(
            "Received %d BTC daily candles from Binance",
            len(candles),
        )

        records = []

        for candle in candles:
            candle_time = datetime.fromtimestamp(
                candle["open_time"] / 1000,
                tz=timezone.utc,
            )

            records.append(
                {
                    "time": candle_time,
                    "price": float(candle["close"]),
                    "volume": float(candle["volume"]),
                    "market_cap": None,
                }
            )

        inserted = repository.save_historical_prices(
            records,
            source=SOURCE,
        )

        logger.info(
            "BTC historical backfill completed: %d records persisted",
            inserted,
        )

    finally:
        await collector.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(backfill_btc_prices())