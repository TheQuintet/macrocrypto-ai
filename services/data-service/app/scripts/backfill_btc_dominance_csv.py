import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.database.btc_dominance_repository import BTCDominanceRepository
from app.database.session import SessionLocal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CSV_PATH = Path(__file__).parent / "bitcoin-dominance.csv"
CUTOFF_DATE = pd.Timestamp("2022-09-15", tz="UTC")


def main() -> None:
    logger.info("Reading %s", CSV_PATH)

    df = pd.read_csv(CSV_PATH)

    df["time"] = pd.to_datetime(df["unixTs"], unit="s", utc=True)

    historical = df[df["time"] < CUTOFF_DATE].copy()

    records = [
        {
            "time": row.time.to_pydatetime(),
            "dominance": float(row.bitcoinDominance),
        }
        for row in historical.itertuples()
    ]

    logger.info("Historical records to import: %d", len(records))

    db = SessionLocal()

    try:
        repository = BTCDominanceRepository(db)

        inserted = repository.save_historical_dominance(
            records,
            source="bgeometrics_csv_backfill",
        )

        logger.info("Backfill completed. Processed: %d", inserted)

    finally:
        db.close()


if __name__ == "__main__":
    main()