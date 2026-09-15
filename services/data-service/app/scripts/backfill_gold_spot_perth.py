"""
One-time backfill of historical gold spot prices from Perth Mint.

Source:
    Perth Mint historical gold prices CSV

Uses:
    Perth Mint USD Bid Average (Perth Mint Spot.12)

Coverage:
    2017-08-17 through 2021-09-13

The existing Yahoo Finance gold data beginning on 2021-09-14
is left untouched.
"""

import pandas as pd

from app.database.session import SessionLocal
from app.database.macro_indicator_repository import MacroIndicatorRepository


CSV_PATH = "app/scripts/daily-gold-prices-01-01-2016-to-31-12-2021.csv"

START_DATE = "2017-08-17"
END_DATE = "2021-09-13"

INDICATOR_NAME = "gold_spot"
SOURCE = "perth_mint_backfill"


def main():
    df = pd.read_csv(CSV_PATH)

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
        (data["date"] >= START_DATE)
        & (data["date"] <= END_DATE)
        & data["value"].notna()
    ].copy()

    # Ensure one record per date.
    data = data.drop_duplicates(subset=["date"])

    records = []

    for _, row in data.iterrows():
        records.append(
            {
                "time": row["date"].to_pydatetime(),
                "indicator_name": INDICATOR_NAME,
                "value": float(row["value"]),
                "source": SOURCE,
            }
        )

    print(f"CSV records selected: {len(records)}")

    if not records:
        print("No records found. Nothing to insert.")
        return

    db = SessionLocal()

    try:
        repository = MacroIndicatorRepository(db)

        inserted = repository.create_many(records)

        db.commit()

        print(f"Backfill completed: {len(inserted)} records processed.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()


