import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()

FRED_API_KEY = os.getenv("FRED_API_KEY")

if not FRED_API_KEY:
    raise ValueError("FRED_API_KEY is missing from .env")

fred = Fred(api_key=FRED_API_KEY)

SERIES_ID = "M2SL"
START_DATE = "2015-01-01"


def main():
    print("=" * 64)
    print("             M2 VINTAGE REDUNDANCY CHECK")
    print("=" * 64)

    # ----------------------------------------------------------
    # Fetch raw FRED data
    # ----------------------------------------------------------
    print("[START] Fetching raw M2SL vintage history...")

    df = fred.get_series_all_releases(SERIES_ID)

    raw_count = len(df)

    df["observation_date"] = pd.to_datetime(df["date"])
    df["release_date"] = pd.to_datetime(df["realtime_start"])

    df = df[
        df["observation_date"] >= pd.to_datetime(START_DATE)
    ].copy()

    print(f"[FETCHED] Raw M2SL records: {raw_count:,}")
    print(
        f"[FILTERED] Records from {START_DATE}: "
        f"{len(df):,}"
    )

    # ----------------------------------------------------------
    # Sort exactly as QA suggested
    # ----------------------------------------------------------
    df = df.sort_values(
        ["SERIES_ID" if False else "observation_date", "release_date"]
    )

    # ----------------------------------------------------------
    # Check consecutive no-op vintages
    # ----------------------------------------------------------
    df["previous_value"] = (
        df.groupby("observation_date")["value"].shift(1)
    )

    df["is_consecutive_noop"] = (
        df["value"] == df["previous_value"]
    )

    consecutive_noops = df["is_consecutive_noop"].sum()

    # ----------------------------------------------------------
    # Check repeated values regardless of position
    # ----------------------------------------------------------
    repeated_groups = (
        df.groupby(
            ["observation_date", "value"]
        )
        .size()
        .reset_index(name="count")
    )

    repeated_groups = repeated_groups[
        repeated_groups["count"] > 1
    ]

    repeated_rows = repeated_groups["count"].sum()

    # ----------------------------------------------------------
    # Unique values per observation date
    # ----------------------------------------------------------
    unique_values = (
        df.groupby("observation_date")["value"]
        .nunique()
    )

    dates_with_multiple_values = (
        (unique_values > 1).sum()
    )

    dates_with_one_value = (
        (unique_values == 1).sum()
    )

    # ----------------------------------------------------------
    # Apply QA's exact filtering logic
    # ----------------------------------------------------------
    df["value_changed"] = (
        df.groupby("observation_date")["value"]
        .diff()
        .fillna(1)
        != 0
    )

    optimized_count = df["value_changed"].sum()
    filtered_count = len(df) - optimized_count

    # ----------------------------------------------------------
    # Summary
    # ----------------------------------------------------------
    print()
    print("=" * 64)
    print("                    RESULTS")
    print("=" * 64)

    print(f"Raw FRED records:                    {raw_count:,}")
    print(f"Records from {START_DATE}:           {len(df):,}")
    print()
    print(
        f"Consecutive no-op vintages:          "
        f"{consecutive_noops:,}"
    )
    print(
        f"Rows removed by QA diff() logic:     "
        f"{filtered_count:,}"
    )
    print(
        f"Records after QA filtering:          "
        f"{optimized_count:,}"
    )
    print()
    print(
        f"Repeated-value groups:                "
        f"{len(repeated_groups):,}"
    )
    print(
        f"Rows involved in repeated values:     "
        f"{repeated_rows:,}"
    )
    print()
    print(
        f"Observation dates with one value:     "
        f"{dates_with_one_value:,}"
    )
    print(
        f"Observation dates with multiple values:"
        f" {dates_with_multiple_values:,}"
    )

    # ----------------------------------------------------------
    # Show examples of repeated values
    # ----------------------------------------------------------
    if not repeated_groups.empty:
        print()
        print("Examples of repeated values:")
        print(repeated_groups.head(10).to_string(index=False))

    print()
    print(
        "[COMPLETED] M2 vintage redundancy check completed."
    )
    print("=" * 64)


if __name__ == "__main__":
    main()