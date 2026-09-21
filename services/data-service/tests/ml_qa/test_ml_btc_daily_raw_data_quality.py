"""
Integration tests for ml_btc_daily_raw.csv data quality.

These tests validate the aggregated raw ML dataset before downstream
ML preprocessing. Missing feature values are reported rather than
rejected because source availability naturally differs across indicators.
"""

from pathlib import Path

import pandas as pd
import pytest


DATA_FILE = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "data"
    / "ml_btc_daily_raw.csv"
)

EXPECTED_COLUMNS = {
    "btc_timestamp",
    "btc_price",
    "btc_volume",
    "observation_date",
    "dominance_timestamp",
    "btc_dominance",
    "gold_spot_timestamp",
    "gold_spot",
    "active_addresses_timestamp",
    "active_addresses",
    "cpi_timestamp",
    "cpi",
    "federal_funds_rate_timestamp",
    "federal_funds_rate",
    "m2_money_supply_timestamp",
    "m2_money_supply",
    "dxy_timestamp",
    "dxy",
    "ten_year_treasury_timestamp",
    "ten_year_treasury",
    "gdp_timestamp",
    "gdp",
    "unemployment_timestamp",
    "unemployment",
    "vix_timestamp",
    "vix",
    "high_yield_spread_timestamp",
    "high_yield_spread",
    "nasdaq_composite_timestamp",
    "nasdaq_composite",
    "equity_corr_timestamp",
    "equity_corr",
}

VALUE_COLUMNS = {
    "btc_price",
    "btc_volume",
    "btc_dominance",
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
}

TIMESTAMP_COLUMNS = {
    "btc_timestamp",
    "dominance_timestamp",
    "gold_spot_timestamp",
    "active_addresses_timestamp",
    "cpi_timestamp",
    "federal_funds_rate_timestamp",
    "m2_money_supply_timestamp",
    "dxy_timestamp",
    "ten_year_treasury_timestamp",
    "gdp_timestamp",
    "unemployment_timestamp",
    "vix_timestamp",
    "high_yield_spread_timestamp",
    "nasdaq_composite_timestamp",
    "equity_corr_timestamp",
}

TIMESTAMP_VALUE_PAIRS = {
    "btc_timestamp": "btc_price",
    "dominance_timestamp": "btc_dominance",
    "gold_spot_timestamp": "gold_spot",
    "active_addresses_timestamp": "active_addresses",
    "cpi_timestamp": "cpi",
    "federal_funds_rate_timestamp": "federal_funds_rate",
    "m2_money_supply_timestamp": "m2_money_supply",
    "dxy_timestamp": "dxy",
    "ten_year_treasury_timestamp": "ten_year_treasury",
    "gdp_timestamp": "gdp",
    "unemployment_timestamp": "unemployment",
    "vix_timestamp": "vix",
    "high_yield_spread_timestamp": "high_yield_spread",
    "nasdaq_composite_timestamp": "nasdaq_composite",
    "equity_corr_timestamp": "equity_corr",
}


@pytest.fixture(scope="module")
def ml_btc_daily_raw():
    """Load the current aggregated raw ML dataset."""
    assert DATA_FILE.exists(), (
        f"ML raw dataset not found: {DATA_FILE}"
    )

    return pd.read_csv(DATA_FILE)


@pytest.fixture(scope="module")
def parsed_dataset(ml_btc_daily_raw):
    """
    Return a copy with date/timestamp columns parsed as UTC timestamps.

    The CSV stores timestamps as strings, so parsing is part of the
    validation boundary rather than a requirement on the CSV itself.
    """
    df = ml_btc_daily_raw.copy()

    for column in TIMESTAMP_COLUMNS | {"observation_date"}:
        df[column] = pd.to_datetime(
            df[column],
            utc=True,
            errors="coerce",
            format="mixed",
        )

    return df


def test_ml_btc_daily_raw_data_exists(ml_btc_daily_raw):
    """The aggregated raw ML dataset must exist and contain data."""
    assert not ml_btc_daily_raw.empty, (
        "ml_btc_daily_raw.csv contains no rows"
    )


def test_ml_btc_daily_raw_row_count(ml_btc_daily_raw):
    """The aggregated raw ML dataset should contain substantial history."""
    row_count = len(ml_btc_daily_raw)

    print(f"\nML raw dataset row count: {row_count}")

    assert row_count >= 1800, (
        f"ML raw dataset is unexpectedly small: {row_count} rows"
    )


def test_ml_btc_daily_raw_has_expected_columns(ml_btc_daily_raw):
    """The dataset must contain the expected aggregation columns."""
    actual_columns = set(ml_btc_daily_raw.columns)

    missing_columns = sorted(
        EXPECTED_COLUMNS - actual_columns
    )

    assert not missing_columns, (
        f"Missing expected ML raw columns: {missing_columns}"
    )


def test_ml_btc_daily_raw_has_no_unexpected_columns(ml_btc_daily_raw):
    """Unexpected columns should not be silently introduced."""
    actual_columns = set(ml_btc_daily_raw.columns)

    unexpected_columns = sorted(
        actual_columns - EXPECTED_COLUMNS
    )

    assert not unexpected_columns, (
        f"Unexpected ML raw columns found: {unexpected_columns}"
    )


def test_ml_btc_daily_raw_excludes_market_cap(ml_btc_daily_raw):
    """Market cap must remain excluded from the ML raw dataset."""
    assert "btc_market_cap" not in ml_btc_daily_raw.columns, (
        "btc_market_cap must not be included in the ML raw dataset"
    )


def test_ml_btc_daily_raw_observation_dates_are_valid(
    parsed_dataset,
):
    """Every observation date must parse as a valid UTC timestamp."""
    invalid_dates = parsed_dataset["observation_date"].isna().sum()

    assert invalid_dates == 0, (
        f"Found {invalid_dates} invalid observation_date values"
    )


def test_ml_btc_daily_raw_observation_dates_are_utc(
    parsed_dataset,
):
    """Observation dates must be represented in UTC."""
    timestamps = parsed_dataset["observation_date"]

    assert all(
        timestamp.utcoffset().total_seconds() == 0
        for timestamp in timestamps
    ), "One or more observation dates are not UTC"


def test_ml_btc_daily_raw_has_one_row_per_observation_date(
    parsed_dataset,
):
    """The aggregated dataset must contain exactly one row per day."""
    duplicate_dates = (
        parsed_dataset["observation_date"]
        .duplicated()
        .sum()
    )

    assert duplicate_dates == 0, (
        f"Found {duplicate_dates} duplicate observation dates"
    )


def test_ml_btc_daily_raw_observation_dates_are_chronological(
    parsed_dataset,
):
    """Observation dates must be in chronological order."""
    dates = parsed_dataset["observation_date"]

    assert dates.is_monotonic_increasing, (
        "Observation dates are not in chronological order"
    )


def test_ml_btc_daily_raw_has_no_future_observations(
    parsed_dataset,
):
    """The dataset must not contain future observation dates."""
    now = pd.Timestamp.now(tz="UTC")

    future_rows = parsed_dataset[
        parsed_dataset["observation_date"] > now
    ]

    assert future_rows.empty, (
        f"Found {len(future_rows)} future observation dates"
    )


def test_ml_btc_daily_raw_observation_dates_are_daily(
    parsed_dataset,
):
    """
    Observation dates must represent UTC calendar days.

    This validates the daily aggregation key without requiring every
    source timestamp itself to occur at midnight.
    """
    dates = parsed_dataset["observation_date"]

    invalid_times = dates[
        (dates.dt.hour != 0)
        | (dates.dt.minute != 0)
        | (dates.dt.second != 0)
        | (dates.dt.microsecond != 0)
    ]

    assert invalid_times.empty, (
        f"Found {len(invalid_times)} observation dates "
        "that are not normalized to midnight UTC"
    )


def test_ml_btc_daily_raw_btc_price_is_complete_and_positive(
    parsed_dataset,
):
    """BTC price must be present and positive for every daily row."""
    missing_count = parsed_dataset["btc_price"].isna().sum()

    assert missing_count == 0, (
        f"Found {missing_count} rows with missing BTC price"
    )

    assert (parsed_dataset["btc_price"] > 0).all(), (
        "BTC price contains zero or negative values"
    )


def test_ml_btc_daily_raw_btc_volume_is_complete_and_non_negative(
    parsed_dataset,
):
    """BTC volume must be present and non-negative for every daily row."""
    missing_count = parsed_dataset["btc_volume"].isna().sum()

    assert missing_count == 0, (
        f"Found {missing_count} rows with missing BTC volume"
    )

    assert (parsed_dataset["btc_volume"] >= 0).all(), (
        "BTC volume contains negative values"
    )


def test_ml_btc_daily_raw_numeric_columns_are_numeric(
    ml_btc_daily_raw,
):
    """All feature/value columns must contain numeric data."""
    invalid_columns = []

    for column in VALUE_COLUMNS:
        if not pd.api.types.is_numeric_dtype(
            ml_btc_daily_raw[column]
        ):
            invalid_columns.append(column)

    assert not invalid_columns, (
        f"Non-numeric ML feature columns found: {invalid_columns}"
    )


def test_ml_btc_daily_raw_timestamp_columns_are_valid_when_present(
    parsed_dataset,
):
    """
    Source timestamps must be valid UTC timestamps when their values
    are present. Missing timestamps are allowed when the corresponding
    source feature is unavailable.
    """
    invalid_columns = []

    for timestamp_column, value_column in TIMESTAMP_VALUE_PAIRS.items():
        invalid_mask = (
            parsed_dataset[timestamp_column].isna()
            & parsed_dataset[value_column].notna()
        )

        if invalid_mask.any():
            invalid_columns.append(
                timestamp_column
            )

    assert not invalid_columns, (
        "Found feature values without corresponding valid "
        f"timestamps: {invalid_columns}"
    )


def test_ml_btc_daily_raw_timestamp_value_nullability_matches(
    parsed_dataset,
):
    """
    Each feature timestamp/value pair must agree on availability.

    A feature is either present with a valid timestamp or absent with
    a missing timestamp.
    """
    mismatches = []

    for timestamp_column, value_column in TIMESTAMP_VALUE_PAIRS.items():
        timestamp_present = (
            parsed_dataset[timestamp_column].notna()
        )
        value_present = (
            parsed_dataset[value_column].notna()
        )

        mismatch_count = (
            timestamp_present != value_present
        ).sum()

        if mismatch_count:
            mismatches.append(
                f"{value_column}: {mismatch_count}"
            )

    assert not mismatches, (
        "Timestamp/value availability mismatches found: "
        f"{mismatches}"
    )


def test_ml_btc_daily_raw_source_timestamps_are_utc(
    parsed_dataset,
):
    """All populated source timestamps must represent UTC."""
    non_utc_columns = []

    for column in TIMESTAMP_COLUMNS:
        timestamps = parsed_dataset[column].dropna()

        if not timestamps.empty:
            non_utc = [
                timestamp
                for timestamp in timestamps
                if timestamp.utcoffset().total_seconds() != 0
            ]

            if non_utc:
                non_utc_columns.append(column)

    assert not non_utc_columns, (
        f"Non-UTC source timestamps found in: {non_utc_columns}"
    )


def test_ml_btc_daily_raw_coverage_is_reported(
    parsed_dataset,
):
    """Report the overall daily coverage of the aggregated dataset."""
    dates = parsed_dataset["observation_date"]

    first_date = dates.min()
    last_date = dates.max()
    distinct_dates = dates.nunique()

    print(
        "\nML raw dataset coverage: "
        f"{first_date} -> {last_date} | "
        f"{distinct_dates} distinct observation dates"
    )

    assert first_date <= last_date


def test_ml_btc_daily_raw_missing_feature_counts_are_reported(
    ml_btc_daily_raw,
):
    """
    Report feature-level missingness.

    Missing historical observations are allowed at this aggregation
    stage because source availability differs across indicators.
    """
    print("\nML raw dataset missing feature counts:")

    for column in sorted(VALUE_COLUMNS):
        missing_count = ml_btc_daily_raw[column].isna().sum()

        print(
            f"  {column}: "
            f"{missing_count} missing / {len(ml_btc_daily_raw)} rows"
        )

    assert True
    
def test_ml_btc_daily_raw_has_no_missing_observation_dates(
    parsed_dataset,
):
    """The aggregated dataset must contain every calendar day in its range."""
    dates = (
        parsed_dataset["observation_date"]
        .sort_values()
        .drop_duplicates()
    )

    expected_dates = pd.date_range(
        start=dates.min(),
        end=dates.max(),
        freq="D",
        tz="UTC",
    )

    missing_dates = expected_dates.difference(dates)

    assert missing_dates.empty, (
        f"Found {len(missing_dates)} missing observation dates: "
        f"{missing_dates.tolist()}"
    )