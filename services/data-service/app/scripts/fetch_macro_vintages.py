import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

if not FRED_API_KEY:
    raise ValueError(
        "FRED_API_KEY environment variable is missing. "
        "Please set it in your .env file."
    )

fred = Fred(api_key=FRED_API_KEY)

MACRO_SERIES = {
    "cpi": "CPIAUCSL",
    "unemployment": "UNRATE",
    "federal_funds_rate": "FEDFUNDS",
    "m2_money_supply": "M2SL",
    "gdp": "GDP",
}


def fetch_all_releases(series_id, name, start_date="2015-01-01"):
    print(f"[START] Fetching {name.upper()} ({series_id})...")

    try:
        if name == "m2_money_supply":
            print(
                "       Note: M2SL has a large vintage history; "
                "this may take a little longer."
            )

        print(f"[FETCH] Downloading all releases for {series_id}...")

        df = fred.get_series_all_releases(series_id)

        raw_count = len(df)

        df["date"] = pd.to_datetime(df["date"])
        df = df[df["date"] >= pd.to_datetime(start_date)].copy()

        filtered_count = len(df)

        df["series_id"] = series_id
        df["feature_name"] = name

        print(
            f"[FETCHED] {name.upper()}: "
            f"{raw_count:,} raw records → "
            f"{filtered_count:,} records from {start_date}"
        )

        return df

    except Exception as e:
        print(f"[ERROR] Failed to fetch {series_id}: {e}")
        return None


def remove_noop_vintages(df):
    """
    Remove consecutive vintages where the value did not change
    for the same series and observation date.
    """

    df = df.sort_values(
        ["series_id", "observation_date", "release_date"]
    ).copy()

    before_count = len(df)

    value_changed = (
        df.groupby(["series_id", "observation_date"])["value"]
        .diff()
        .fillna(1)
        != 0
    )

    df = df[value_changed].copy()

    after_count = len(df)
    no_op_filtered = before_count - after_count

    return df, before_count, no_op_filtered, after_count


def main():
    print("=" * 64)
    print("        MACROECONOMIC VINTAGE INGESTION JOB")
    print("=" * 64)
    print("[START] Macro vintage ingestion started.")
    print()

    all_data = []

    # ----------------------------------------------------------
    # Fetch all macro series
    # ----------------------------------------------------------
    for name, series_id in MACRO_SERIES.items():
        df = fetch_all_releases(series_id, name)

        if df is not None:
            all_data.append(df)

        print()

    if not all_data:
        print("[ERROR] No data was fetched. Job failed.")
        return

    # ----------------------------------------------------------
    # Combine datasets
    # ----------------------------------------------------------
    print("[PROCESS] Combining fetched datasets...")

    combined_df = pd.concat(all_data, ignore_index=True)

    # Rename columns to consistent names
    combined_df = combined_df.rename(
        columns={
            "date": "observation_date",
            "realtime_start": "release_date",
        }
    )

    print(
        f"[PROCESS] Combined records before optimization: "
        f"{len(combined_df):,}"
    )

    # ----------------------------------------------------------
    # Remove consecutive no-op vintages
    # ----------------------------------------------------------
    print()
    print("[OPTIMIZATION] Removing consecutive no-op vintages...")

    (
        combined_df,
        before_optimization,
        no_op_filtered,
        after_optimization,
    ) = remove_noop_vintages(combined_df)

    print(
        f"[OPTIMIZATION] Records before filtering: "
        f"{before_optimization:,}"
    )
    print(
        f"[OPTIMIZATION] No-op vintages filtered: "
        f"{no_op_filtered:,}"
    )
    print(
        f"[OPTIMIZATION] Final records: "
        f"{after_optimization:,}"
    )

    # ----------------------------------------------------------
    # Final counts per feature
    # ----------------------------------------------------------
    final_counts = (
        combined_df.groupby("feature_name")
        .size()
        .to_dict()
    )

    # ----------------------------------------------------------
    # Save output
    # ----------------------------------------------------------
    output_path = "app/data/macro_raw_with_vintages.csv"

    print()
    print(f"[SAVE] Writing dataset to {output_path}...")

    os.makedirs("app/data", exist_ok=True)

    combined_df.to_csv(output_path, index=False)

    print("[SAVED] Dataset successfully written.")

    # ----------------------------------------------------------
    # Final summary
    # ----------------------------------------------------------
    print()
    print("=" * 64)
    print("             MACRO VINTAGE INGESTION SUMMARY")
    print("=" * 64)

    print(f"Total records fetched:              {before_optimization:,}")
    print(f"Total no-op vintages filtered:     {no_op_filtered:,}")
    print(f"Total final records:                {after_optimization:,}")

    print()
    print("Final records by feature:")

    for name, series_id in MACRO_SERIES.items():
        count = final_counts.get(name, 0)

        print(
            f"  * {name.upper():<20} "
            f"({series_id}): {count:,}"
        )

    print()
    print(f"Output: {output_path}")
    print()
    print("[COMPLETED] Macro vintage ingestion completed successfully.")
    print("=" * 64)


if __name__ == "__main__":
    main()