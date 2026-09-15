import logging
from pathlib import Path

import pandas as pd

from app.database.macro_indicator_repository import MacroIndicatorRepository
from app.database.session import SessionLocal


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_PATH = Path(__file__).parent / "BAMLH0A0HYM2.csv"
INDICATOR_NAME = "high_yield_spread"


def main() -> None:
    logger.info("Reading %s", CSV_PATH)

    df = pd.read_csv(CSV_PATH, na_values=["."])

    df["DATE"] = pd.to_datetime(df["DATE"], utc=True)
    df["BAMLH0A0HYM2"] = pd.to_numeric(
        df["BAMLH0A0HYM2"],
        errors="coerce",
    )

    df = df.dropna(subset=["BAMLH0A0HYM2"])

    records = [
        {
            "time": row.DATE.to_pydatetime(),
            "indicator_name": INDICATOR_NAME,
            "value": float(row.BAMLH0A0HYM2),
            "previous_value": None,
            "change_percent": None,
            "source": "fred_archive_backfill",
        }
        for row in df.itertuples()
    ]

    logger.info("Historical records to import: %d", len(records))

    db = SessionLocal()

    try:
        repository = MacroIndicatorRepository(db)

        inserted = repository.create_many(records)

        logger.info("Backfill processed: %d", len(inserted))

    finally:
        db.close()


if __name__ == "__main__":
    main()