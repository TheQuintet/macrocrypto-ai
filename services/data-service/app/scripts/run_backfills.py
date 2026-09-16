"""
Run all historical backfills.

Datasets:
- BTC prices
- BTC dominance
- Gold spot
- GDP
- CPI
- Unemployment
- Federal funds rate
- M2 money supply
- 10-year Treasury
- Nasdaq Composite
- VIX
- High-yield spread
- DXY
- Active addresses
- Equity correlation
"""

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.collectors.binance import BinanceCollector
from app.collectors.yahoo_finance import YahooFinanceCollector
from app.config import settings
from app.database.btc_price_repository import BTCPriceRepository
from app.database.macro_indicator_repository import MacroIndicatorRepository
from app.database.session import SessionLocal
from app.services.active_addresses_service import ActiveAddressesService
from app.services.indicator_service import IndicatorService


logger = logging.getLogger(__name__)

# BTC dominance historical CSV
BTC_DOMINANCE_URL = (
    "https://bitcoin-data.com/v1/bitcoin-dominance/csv"
)
BTC_DOMINANCE_SOURCE = "bgeometrics_backfill"

# Perth Mint historical gold prices
GOLD_PERTH_CSV_PATH = (
    "app/scripts/daily-gold-prices-01-01-2016-to-31-12-2021.csv"
)
GOLD_PERTH_START_DATE = "2017-08-17"
GOLD_PERTH_END_DATE = "2021-09-13"
GOLD_PERTH_INDICATOR_NAME = "gold_spot"
GOLD_PERTH_SOURCE = "perth_mint_backfill"

# High-yield spread historical CSV files
FRED_CSV_PATH = Path(__file__).parent / "BAMLH0A0HYM2.csv"
PROXY_CSV_PATH = Path(__file__).parent / "high_yield_spread_proxy.csv"

INDICATOR_NAME = "high_yield_spread"


async def run_backfill_module(backfill_function):
    """Run either a synchronous or asynchronous backfill function."""
    result = backfill_function()
    if inspect.isawaitable(result):
        await result


def backfill_gold_spot_perth():
    """Backfill historical gold spot prices from Perth Mint."""

    df = pd.read_csv(GOLD_PERTH_CSV_PATH)

    # Rows 0-3 contain the CSV headers/metadata.
    # Row 4 contains the first actual data row.
    data = df.iloc[4:].copy()

    data["date"] = pd.to_datetime(
        data["Market"],
        dayfirst=True,
        errors="coerce",
    )

    # Perth Mint Spot.12 = USD Bid Average
    data["value"] = pd.to_numeric(
        data["Perth Mint Spot.12"],
        errors="coerce",
    )

    data = data[
        (data["date"] >= GOLD_PERTH_START_DATE)
        & (data["date"] <= GOLD_PERTH_END_DATE)
        & data["value"].notna()
    ].copy()

    # Ensure one record per date.
    data = data.drop_duplicates(subset=["date"])

    records = []

    for _, row in data.iterrows():
        records.append(
            {
                "time": row["date"].to_pydatetime(),
                "indicator_name": GOLD_PERTH_INDICATOR_NAME,
                "value": float(row["value"]),
                "source": GOLD_PERTH_SOURCE,
            }
        )

    logger.info(
        "CSV records selected for Perth Mint gold backfill: %d",
        len(records),
    )

    if not records:
        logger.warning(
            "No Perth Mint gold records found. Nothing to insert."
        )
        return

    db = SessionLocal()

    try:
        repository = MacroIndicatorRepository(db)

        inserted = repository.create_many(records)

        logger.info(
            "Perth Mint gold backfill completed: %d records processed",
            len(inserted),
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


async def backfill_gold_spot_yahoo():
    """Backfill historical gold spot prices from Yahoo Finance."""

    collector = YahooFinanceCollector()
    db = SessionLocal()

    try:
        logger.info("Fetching 5 years of gold history...")

        records = await collector.get_gold_spot_history(
            symbol="GC=F",
            range_="5y",
            interval="1d",
        )

        logger.info(
            "Received %d gold records",
            len(records),
        )

        indicators = []

        for record in records:
            indicators.append(
                {
                    "indicator_name": "gold_spot",
                    "time": datetime.fromtimestamp(
                        record["timestamp"],
                        tz=timezone.utc,
                    ),
                    "value": float(record["price"]),
                    "previous_value": None,
                    "change_percent": None,
                    "source": "yahoo_finance",
                }
            )

        if not indicators:
            logger.warning("No valid gold records found.")
            return

        indicators.sort(
            key=lambda x: x["time"]
        )

        repository = MacroIndicatorRepository(db)

        repository.create_many(indicators)

        logger.info(
            "Gold backfill complete: %d records processed",
            len(indicators),
        )

        logger.info(
            "Backfill range: %s -> %s",
            indicators[0]["time"],
            indicators[-1]["time"],
        )

    except Exception:
        logger.exception("Gold backfill failed")
        raise

    finally:
        db.close()
        await collector.close()


async def backfill_btc_prices() -> None:
    """Fetch and persist historical daily BTC candles."""

    BACKFILL_START = datetime(
        2017,
        8,
        1,
        tzinfo=timezone.utc,
    )

    BINANCE_INTERVAL = "1d"
    BINANCE_LIMIT = 1000
    SOURCE = "binance_backfill"

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
            logger.warning(
                "No BTC historical candles returned"
            )
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


async def backfill_btc_dominance():
    """Backfill BTC dominance from the BGeometrics CSV endpoint."""

    logger.info(
        "Starting BTC dominance backfill from BGeometrics: %s",
        BTC_DOMINANCE_URL,
    )

    df = pd.read_csv(BTC_DOMINANCE_URL)

    if "bitcoinDominance" not in df.columns:
        raise ValueError(
            "Expected 'bitcoinDominance' column in BGeometrics CSV, "
            f"found: {list(df.columns)}"
        )

    if "d" not in df.columns:
        raise ValueError(
            "Expected 'd' column in BGeometrics CSV, "
            f"found: {list(df.columns)}"
        )

    df["d"] = pd.to_datetime(
        df["d"],
        utc=True,
    )

    df["bitcoinDominance"] = pd.to_numeric(
        df["bitcoinDominance"],
        errors="coerce",
    )

    df = df.dropna(
        subset=["d", "bitcoinDominance"]
    )

    df = df.sort_values("d")

    records = [
        {
            "time": row["d"].to_pydatetime(),
            "dominance": float(row["bitcoinDominance"]),
            "source": BTC_DOMINANCE_SOURCE,
        }
        for _, row in df.iterrows()
    ]

    logger.info(
        "Loaded %d BTC dominance records from BGeometrics",
        len(records),
    )

    if not records:
        logger.warning(
            "No BTC dominance records available for backfill"
        )
        return

    db = SessionLocal()

    try:
        from app.database.btc_dominance_repository import (
            BTCDominanceRepository,
        )

        repository = BTCDominanceRepository(db)

        inserted = repository.save_historical_dominance(
            records,
            source=BTC_DOMINANCE_SOURCE,
        )

        logger.info(
            "BTC dominance backfill completed: %d records inserted",
            inserted,
        )

    finally:
        db.close()


def load_high_yield_csv(
    csv_path: Path,
    source: str,
) -> list[dict]:
    """Load high-yield spread records from a CSV file."""

    logger.info(
        "Reading high-yield spread CSV: %s",
        csv_path,
    )

    df = pd.read_csv(
        csv_path,
        na_values=["."],
    )

    # Use DATE when available; otherwise use the first column.
    date_col = (
        "DATE"
        if "DATE" in df.columns
        else df.columns[0]
    )

    if "BAMLH0A0HYM2" not in df.columns:
        raise ValueError(
            f"Expected 'BAMLH0A0HYM2' column in {csv_path}, "
            f"found: {list(df.columns)}"
        )

    df[date_col] = pd.to_datetime(
        df[date_col],
        utc=True,
    )

    df["BAMLH0A0HYM2"] = pd.to_numeric(
        df["BAMLH0A0HYM2"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[date_col, "BAMLH0A0HYM2"]
    )

    df = df.sort_values(date_col)

    records = [
        {
            "time": row[date_col].to_pydatetime(),
            "indicator_name": INDICATOR_NAME,
            "value": float(row["BAMLH0A0HYM2"]),
            "previous_value": None,
            "change_percent": None,
            "source": source,
        }
        for _, row in df.iterrows()
    ]

    logger.info(
        "Loaded %d high-yield spread records from %s",
        len(records),
        csv_path.name,
    )

    return records


def backfill_high_yield_spread() -> None:
    """
    Backfill high-yield spread using the historical FRED archive
    and the proxy CSV for the missing historical period.
    """

    logger.info(
        "Starting high-yield spread backfill"
    )

    # 1. Load the original FRED archive.
    fred_records = load_high_yield_csv(
        FRED_CSV_PATH,
        source="fred_archive_backfill",
    )

    # 2. Load the proxy data for the missing historical period.
    if PROXY_CSV_PATH.exists():
        proxy_records = load_high_yield_csv(
            PROXY_CSV_PATH,
            source="hyg_proxy_backfill",
        )
    else:
        logger.warning(
            "Proxy CSV not found at %s. "
            "Skipping proxy data.",
            PROXY_CSV_PATH,
        )
        proxy_records = []

    # 3. Combine records by timestamp.
    #
    # FRED archive records take precedence if there is
    # any overlap between the two files.
    records_by_time = {}

    for record in fred_records:
        records_by_time[record["time"]] = record

    for record in proxy_records:
        if record["time"] not in records_by_time:
            records_by_time[record["time"]] = record

    records = sorted(
        records_by_time.values(),
        key=lambda record: record["time"],
    )

    logger.info(
        "Total unique high-yield spread records to import: %d",
        len(records),
    )

    if not records:
        logger.warning(
            "No high-yield spread records available for backfill"
        )
        return

    # 4. Persist records.
    db = SessionLocal()

    try:
        repository = MacroIndicatorRepository(db)

        inserted = repository.create_many(records)

        logger.info(
            "High-yield spread backfill completed: %d records processed",
            len(inserted),
        )

    finally:
        db.close()


async def backfill_fred_indicators():
    """Backfill all FRED indicators using the existing IndicatorService."""

    db = SessionLocal()

    try:
        service = IndicatorService(db)

        indicators = {
            "cpi": service.get_collector().get_cpi,
            "federal_funds_rate": (
                service.get_collector().get_federal_funds_rate
            ),
            "m2_money_supply": (
                service.get_collector().get_m2_money_supply
            ),
            "dxy": service.get_collector().get_dxy,
            "vix": service.get_collector().get_vix,
            "ten_year_treasury": (
                service.get_collector().get_ten_year_treasury
            ),
            "gdp": service.get_collector().get_gdp,
            "unemployment": (
                service.get_collector().get_unemployment
            ),
            "high_yield_spread": (
                service.get_collector().get_high_yield_spread
            ),
            "nasdaq_composite": (
                service.get_collector().get_nasdaq_composite
            ),
        }

        for indicator_name, fetch_function in indicators.items():
            logger.info(
                "Backfilling FRED indicator: %s",
                indicator_name,
            )

            await service.update_indicator(
                indicator_name,
                fetch_function,
            )

            logger.info(
                "Completed FRED backfill: %s",
                indicator_name,
            )

    finally:
        db.close()


async def backfill_active_addresses():
    """Backfill active Bitcoin addresses."""

    db = SessionLocal()
    service = ActiveAddressesService(db)

    try:
        records = await service.calculate()

        if records:
            service.repository.create_many(records)

            logger.info(
                "Active addresses backfill completed: %d records",
                len(records),
            )
        else:
            logger.warning(
                "No active addresses records returned"
            )

    finally:
        await service.close()
        db.close()


async def backfill_equity_correlation():
    """
    Backfill historical BTC/Nasdaq equity correlation.

    Calculates 30-observation rolling correlation between
    daily BTC returns and daily NASDAQ Composite returns.

    Calculation rules:
    - actual overlapping dates only
    - no forward-filling of NASDAQ
    - daily returns
    - shift(1) information barrier
    - 30-observation rolling correlation
    - source="derived"
    """

    EQUITY_CORR_INDICATOR = "equity_corr"
    NASDAQ_INDICATOR = "nasdaq_composite"
    ROLLING_WINDOW = 30
    MIN_PERIODS = 30

    BACKFILL_START = pd.Timestamp(
        "2017-08-17",
        tz="UTC",
    )

    logger.info(
        "Starting equity_corr backfill: %s",
        BACKFILL_START.date(),
    )

    db = SessionLocal()

    try:
        repository = MacroIndicatorRepository(db)

        # --------------------------------------------------
        # 1. Load NASDAQ history from the database
        # --------------------------------------------------

        end_time = pd.Timestamp.now(tz="UTC")

        lookback_days = (
            end_time - BACKFILL_START
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
        # 2. Load historical BTC prices from the database
        # --------------------------------------------------

        from app.models.btc_price import BTCPrice

        btc_rows = (
            db.query(BTCPrice)
            .filter(
                BTCPrice.time >= BACKFILL_START.to_pydatetime(),
                BTCPrice.time <= end_time.to_pydatetime(),
            )
            .order_by(BTCPrice.time)
            .all()
        )

        if not btc_rows:
            logger.error(
                "No BTC price observations found."
            )
            return

        logger.info(
            "Loaded %d BTC price observations",
            len(btc_rows),
        )

        # --------------------------------------------------
        # 3. Build normalized daily BTC dataset
        # --------------------------------------------------

        btc_df = pd.DataFrame(
            {
                "date": [
                    row.time.astimezone(
                        timezone.utc
                    ).date()
                    for row in btc_rows
                ],
                "btc_close": [
                    float(row.price)
                    for row in btc_rows
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
            df["date"] >= BACKFILL_START.date()
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
        db.close()


async def main():
    """Run all historical backfills."""

    logger.info("Starting all historical backfills")

    logger.info("Backfilling BTC prices...")
    await backfill_btc_prices()

    logger.info("Backfilling BTC dominance...")
    await backfill_btc_dominance()

    logger.info("Backfilling gold spot from Perth...")
    backfill_gold_spot_perth()

    logger.info("Backfilling gold spot from Yahoo...")
    await backfill_gold_spot_yahoo()

    logger.info("Backfilling all FRED indicators...")
    await backfill_fred_indicators()

    logger.info(
        "Backfilling high-yield spread from historical CSVs..."
    )
    backfill_high_yield_spread()

    logger.info("Backfilling active addresses...")
    await backfill_active_addresses()

    logger.info("Backfilling equity correlation...")
    await backfill_equity_correlation()

    logger.info(
        "All historical backfills completed successfully"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())