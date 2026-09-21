"""
Aggregate raw database data into daily ML-ready source frames.

This is the aggregation stage only.

Pipeline:
1. Validate minimum raw source counts.
2. Filter data from START_DATE onward.
3. Reduce each source to one observation per UTC day.
4. Save the aggregated source data locally.

It does NOT:
- impute missing values
- interpolate
- forward-fill
- engineer features
- calculate targets
- scale data
- modify the database
- perform PIT merging yet

Raw database timestamps are preserved during processing.
observation_date is derived in memory only.
"""

import logging
from pathlib import Path

import pandas as pd

from app.database.session import SessionLocal
from app.models.btc_price import BTCPrice
from app.models.btc_dominance import BTCDominance
from app.models.macro_indicator import MacroIndicator


logger = logging.getLogger(__name__)


START_DATE = pd.Timestamp(
    "2017-08-17",
    tz="UTC",
)

OUTPUT_PATH = Path(
    "app/data/ml_btc_daily_raw.csv"
)


MACRO_INDICATORS = [
    "gold_spot",
    "active_addresses",
    "cpi",
    "federal_funds_rate",
    "m2_money_supply",
    "dxy",
    "ten_year_treasury",
    "gdp",
    "unemployment",
    "vix",
    "high_yield_spread",
    "nasdaq_composite",
    "equity_corr",
]


# Minimum raw records required BEFORE any date filtering.
MIN_RAW_COUNTS = {
    "btc_prices": 3000,
    "btc_dominance": 4000,
    "gdp": 318,
    "cpi": 955,
    "unemployment": 943,
    "federal_funds_rate": 866,
    "m2_money_supply": 811,
    "ten_year_treasury": 16162,
    "nasdaq_composite": 14022,
    "vix": 9275,
    "high_yield_spread": 7109,
    "dxy": 5188,
    "active_addresses": 1608,
    "gold_spot": 2524,
    "equity_corr": 2253,
}


def check_minimum_raw_counts(db) -> None:
    """
    Validate raw database counts before any date filtering.

    This check intentionally does NOT use START_DATE.
    """

    actual_counts = {}

    actual_counts["btc_prices"] = (
        db.query(BTCPrice).count()
    )

    actual_counts["btc_dominance"] = (
        db.query(BTCDominance).count()
    )

    for indicator_name in MACRO_INDICATORS:
        actual_counts[indicator_name] = (
            db.query(MacroIndicator)
            .filter(
                MacroIndicator.indicator_name == indicator_name
            )
            .count()
        )

    print()
    print("=" * 70)
    print("PRE-AGGREGATION RAW COUNT CHECK")
    print("=" * 70)

    failures = []

    for feature_name, minimum_count in MIN_RAW_COUNTS.items():
        actual_count = actual_counts.get(
            feature_name,
            0,
        )

        if actual_count >= minimum_count:
            status = "PASS"
        else:
            status = "FAIL"

            failures.append(
                (
                    feature_name,
                    actual_count,
                    minimum_count,
                )
            )

        print(
            f"{status:<6} "
            f"{feature_name:<22} "
            f"{actual_count:>6} / {minimum_count}"
        )

    print("=" * 70)

    if failures:
        print()
        print(
            "Aggregation aborted: "
            "one or more raw source counts are below "
            "the minimum."
        )

        failure_details = ", ".join(
            (
                f"{name}={actual} "
                f"(minimum={minimum})"
            )
            for name, actual, minimum in failures
        )

        raise ValueError(
            "Minimum raw count check failed: "
            + failure_details
        )

    logger.info(
        "All minimum raw source count checks passed."
    )


def add_observation_date(
    df: pd.DataFrame,
    timestamp_column: str = "timestamp",
) -> pd.DataFrame:
    """Derive UTC observation_date without modifying the DB."""

    df[timestamp_column] = pd.to_datetime(
        df[timestamp_column],
        utc=True,
    )

    df["observation_date"] = (
        df[timestamp_column]
        .dt.normalize()
    )

    return df


def load_btc_prices(db) -> pd.DataFrame:
    """Load BTC prices and reduce to one observation per UTC day."""

    rows = (
        db.query(BTCPrice)
        .filter(
            BTCPrice.time >= START_DATE.to_pydatetime()
        )
        .order_by(BTCPrice.time)
        .all()
    )

    records = [
        {
            "timestamp": row.time,
            "btc_price": float(row.price),
            "btc_volume": float(row.volume),
        }
        for row in rows
    ]

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError(
            "No BTC price records found."
        )

    df = add_observation_date(df)

    df = (
        df.sort_values("timestamp")
        .drop_duplicates(
            subset=["observation_date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    logger.info(
        "BTC daily observations: %d",
        len(df),
    )

    logger.info(
        "BTC range: %s -> %s",
        df["observation_date"].min(),
        df["observation_date"].max(),
    )

    return df


def load_btc_dominance(db) -> pd.DataFrame:
    """Load BTC dominance and reduce to one observation per UTC day."""

    rows = (
        db.query(BTCDominance)
        .filter(
            BTCDominance.time >= START_DATE.to_pydatetime()
        )
        .order_by(BTCDominance.time)
        .all()
    )

    records = [
        {
            "timestamp": row.time,
            "btc_dominance": float(row.dominance),
        }
        for row in rows
    ]

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError(
            "No BTC dominance records found."
        )

    df = add_observation_date(df)

    df = (
        df.sort_values("timestamp")
        .drop_duplicates(
            subset=["observation_date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    logger.info(
        "BTC dominance daily observations: %d",
        len(df),
    )

    logger.info(
        "BTC dominance range: %s -> %s",
        df["observation_date"].min(),
        df["observation_date"].max(),
    )

    return df


def load_macro_indicator(
    db,
    indicator_name: str,
) -> pd.DataFrame:
    """Load one macro indicator and reduce to daily observations."""

    rows = (
        db.query(MacroIndicator)
        .filter(
            MacroIndicator.indicator_name == indicator_name,
            MacroIndicator.time >= START_DATE.to_pydatetime(),
        )
        .order_by(MacroIndicator.time)
        .all()
    )

    records = [
        {
            "timestamp": row.time,
            "value": float(row.value),
        }
        for row in rows
    ]

    df = pd.DataFrame(records)

    if df.empty:
        logger.warning(
            "No records found for %s",
            indicator_name,
        )

        return pd.DataFrame(
            columns=[
                "timestamp",
                "observation_date",
                indicator_name,
            ]
        )

    df = add_observation_date(df)

    df = (
        df.sort_values("timestamp")
        .drop_duplicates(
            subset=["observation_date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    df = df.rename(
        columns={
            "value": indicator_name
        }
    )

    logger.info(
        "%s daily observations: %d",
        indicator_name,
        len(df),
    )

    return df[
        [
            "timestamp",
            "observation_date",
            indicator_name,
        ]
    ]


def save_aggregated_source_data(
    btc: pd.DataFrame,
    dominance: pd.DataFrame,
    macro_frames: dict,
) -> None:
    """Save the aggregated source data as one local CSV."""

    output = btc.copy()

    output = output.rename(
        columns={
            "timestamp": "btc_timestamp",
        }
    )

    dominance_to_merge = dominance[
        [
            "observation_date",
            "timestamp",
            "btc_dominance",
        ]
    ].rename(
        columns={
            "timestamp": "dominance_timestamp",
        }
    )

    output = output.merge(
        dominance_to_merge,
        on="observation_date",
        how="outer",
    )

    for name, frame in macro_frames.items():
        macro_to_merge = frame[
            [
                "observation_date",
                "timestamp",
                name,
            ]
        ].rename(
            columns={
                "timestamp": f"{name}_timestamp",
            }
        )

        output = output.merge(
            macro_to_merge,
            on="observation_date",
            how="outer",
        )

    output = output.sort_values(
        "observation_date"
    ).reset_index(drop=True)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    logger.info(
        "Saved aggregated source data to %s",
        OUTPUT_PATH,
    )


def main():
    """Run daily source aggregation."""

    logger.info(
        "Starting ML data aggregation"
    )

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. PRE-AGGREGATION RAW COUNT GATE
        #
        # No START_DATE filtering happens here.
        # -------------------------------------------------

        check_minimum_raw_counts(db)

        # -------------------------------------------------
        # 2. After the count gate passes, begin the
        #    2017-08-17 filtering and daily aggregation.
        # -------------------------------------------------

        btc = load_btc_prices(db)

        dominance = load_btc_dominance(db)

        macro_frames = {}

        for indicator_name in MACRO_INDICATORS:
            macro_frames[indicator_name] = (
                load_macro_indicator(
                    db,
                    indicator_name,
                )
            )

        # -------------------------------------------------
        # 3. Save aggregated source data.
        # -------------------------------------------------

        save_aggregated_source_data(
            btc,
            dominance,
            macro_frames,
        )

        # -------------------------------------------------
        # 4. Build source summary.
        # -------------------------------------------------

        print()
        print("=" * 70)
        print("DAILY SOURCE AGGREGATION")
        print("=" * 70)

        print(
            f"BTC:              {len(btc):>6} rows"
        )

        print(
            f"BTC dominance:    {len(dominance):>6} rows"
        )

        for name, frame in macro_frames.items():
            print(
                f"{name:<20} {len(frame):>6} rows"
            )

        print("=" * 70)

        # -------------------------------------------------
        # 5. Show samples.
        # -------------------------------------------------

        print()
        print("BTC sample:")

        print(
            btc[
                [
                    "timestamp",
                    "observation_date",
                    "btc_price",
                    "btc_volume",
                ]
            ].head()
        )

        print()
        print("BTC dominance sample:")

        print(
            dominance[
                [
                    "timestamp",
                    "observation_date",
                    "btc_dominance",
                ]
            ].head()
        )

        logger.info(
            "Daily source aggregation completed."
        )

    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
    )

    main()

