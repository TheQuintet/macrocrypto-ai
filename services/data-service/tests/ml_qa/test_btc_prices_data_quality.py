"""
Data-quality validation for persisted historical BTC prices.

These tests validate the actual Binance historical backfill stored in
the btc_prices table.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.database.session import SessionLocal
from app.models.btc_price import BTCPrice


@pytest.fixture(scope="module")
def btc_records():
    """
    Load Binance historical BTC records once for the QA test module.
    """

    session = SessionLocal()

    try:
        records = (
            session.query(BTCPrice)
            .filter(BTCPrice.source == "binance_backfill")
            .order_by(BTCPrice.time.asc())
            .all()
        )

        return records

    finally:
        session.close()


def test_btc_historical_data_exists(btc_records):
    """Verify that Binance historical BTC data exists."""

    assert btc_records, (
        "No Binance historical BTC records were found in btc_prices"
    )


def test_btc_historical_row_count(btc_records):
    """Report the number of persisted historical BTC records."""

    assert len(btc_records) > 0, (
        "Binance historical BTC dataset contains no records"
    )

    print(f"\nBTC historical row count: {len(btc_records)}")


def test_btc_historical_coverage(btc_records):
    """Report the first and last historical observations."""

    assert btc_records, "Cannot determine coverage from an empty dataset"

    first_observation = btc_records[0].time
    last_observation = btc_records[-1].time

    print(
        "\nBTC historical coverage:"
        f"\n  First observation: {first_observation.isoformat()}"
        f"\n  Last observation:  {last_observation.isoformat()}"
    )

    assert first_observation <= last_observation


def test_btc_historical_distinct_days(btc_records):
    """Verify that each persisted record represents a distinct UTC day."""

    assert btc_records, "Cannot validate distinct days from an empty dataset"

    observation_dates = [
        record.time.date()
        for record in btc_records
    ]

    distinct_days = len(set(observation_dates))

    print(f"\nBTC historical distinct days: {distinct_days}")

    assert distinct_days == len(btc_records), (
        "BTC historical dataset contains multiple observations "
        "for the same UTC calendar date"
    )


def test_btc_historical_timestamps_are_timezone_aware(btc_records):
    """Verify that all historical timestamps are timezone-aware."""

    invalid_timestamps = [
        record.time
        for record in btc_records
        if record.time.tzinfo is None
    ]

    assert not invalid_timestamps, (
        "BTC historical records contain timezone-naive timestamps: "
        f"{invalid_timestamps[:10]}"
    )


def test_btc_historical_timestamps_are_utc(btc_records):
    """Verify that all historical timestamps use UTC."""

    non_utc_timestamps = [
        record.time
        for record in btc_records
        if (
            record.time.tzinfo is None
            or record.time.astimezone(timezone.utc).utcoffset() != timedelta(0)
        )
    ]

    assert not non_utc_timestamps, (
        "BTC historical records contain non-UTC timestamps: "
        f"{non_utc_timestamps[:10]}"
    )


def test_btc_historical_timestamps_are_midnight_utc(btc_records):
    """
    Verify that Binance daily candle timestamps align to 00:00 UTC.
    """

    invalid_timestamps = [
        record.time
        for record in btc_records
        if (
            record.time.astimezone(timezone.utc).hour != 0
            or record.time.astimezone(timezone.utc).minute != 0
            or record.time.astimezone(timezone.utc).second != 0
            or record.time.astimezone(timezone.utc).microsecond != 0
        )
    ]

    assert not invalid_timestamps, (
        "BTC historical records contain timestamps that are not "
        "aligned to 00:00:00 UTC: "
        f"{invalid_timestamps[:10]}"
    )


def test_btc_historical_has_no_future_observations(btc_records):
    """Verify that no historical observation is dated in the future."""

    now = datetime.now(timezone.utc)

    future_records = [
        record.time
        for record in btc_records
        if record.time > now
    ]

    assert not future_records, (
        "BTC historical data contains future observations: "
        f"{future_records[:10]}"
    )


def test_btc_historical_has_no_duplicate_timestamps(btc_records):
    """Verify that no two historical records share the same timestamp."""

    timestamps = [
        record.time
        for record in btc_records
    ]

    duplicate_count = len(timestamps) - len(set(timestamps))

    assert duplicate_count == 0, (
        "Duplicate BTC historical timestamps detected: "
        f"{duplicate_count}"
    )


def test_btc_historical_has_one_observation_per_day(btc_records):
    """
    Verify that exactly one Binance historical observation exists
    for each UTC calendar date.
    """

    observation_dates = [
        record.time.date()
        for record in btc_records
    ]

    duplicate_dates = {
        date
        for date in observation_dates
        if observation_dates.count(date) > 1
    }

    assert not duplicate_dates, (
        "Multiple BTC historical observations found for UTC dates: "
        f"{sorted(duplicate_dates)[:10]}"
    )


def test_btc_historical_has_no_missing_dates(btc_records):
    """
    Verify that there are no missing calendar days between the first
    and last persisted historical observations.
    """

    assert btc_records, "Cannot validate date gaps from an empty dataset"

    first_date = btc_records[0].time.date()
    last_date = btc_records[-1].time.date()

    expected_dates = {
        first_date + timedelta(days=offset)
        for offset in range(
            (last_date - first_date).days + 1
        )
    }

    actual_dates = {
        record.time.date()
        for record in btc_records
    }

    missing_dates = sorted(expected_dates - actual_dates)

    assert not missing_dates, (
        "Missing BTC historical daily observations detected: "
        f"{missing_dates[:20]}"
    )


def test_btc_historical_maximum_gap_is_one_day(btc_records):
    """
    Verify that consecutive historical observations are exactly
    one calendar day apart.
    """

    assert len(btc_records) >= 2, (
        "At least two BTC historical records are required "
        "to validate the maximum gap"
    )

    timestamps = [
        record.time
        for record in btc_records
    ]

    gaps = [
        timestamps[index] - timestamps[index - 1]
        for index in range(1, len(timestamps))
    ]

    maximum_gap = max(gaps)

    print(f"\nBTC historical maximum gap: {maximum_gap}")

    assert maximum_gap == timedelta(days=1), (
        "Unexpected gap in BTC historical daily observations: "
        f"maximum gap was {maximum_gap}"
    )


def test_btc_historical_prices_are_positive(btc_records):
    """Verify that every historical BTC price is greater than zero."""

    invalid_prices = [
        (record.time, record.price)
        for record in btc_records
        if record.price is None or record.price <= 0
    ]

    assert not invalid_prices, (
        "BTC historical data contains NULL or non-positive prices: "
        f"{invalid_prices[:10]}"
    )


def test_btc_historical_volumes_are_present(btc_records):
    """
    Verify that historical Binance candles contain volume values.

    Binance daily candles are expected to provide volume, even though
    the database model allows NULL for other BTC price sources.
    """

    missing_volumes = [
        record.time
        for record in btc_records
        if record.volume is None
    ]

    assert not missing_volumes, (
        "BTC historical Binance records contain NULL volumes: "
        f"{missing_volumes[:10]}"
    )


def test_btc_historical_volumes_are_non_negative(btc_records):
    """Verify that historical BTC volumes are non-negative."""

    invalid_volumes = [
        (record.time, record.volume)
        for record in btc_records
        if record.volume < 0
    ]

    assert not invalid_volumes, (
        "BTC historical data contains negative volumes: "
        f"{invalid_volumes[:10]}"
    )


def test_btc_historical_source_is_binance_backfill(btc_records):
    """Verify that all records in this QA dataset have the expected source."""

    invalid_sources = [
        (record.time, record.source)
        for record in btc_records
        if record.source != "binance_backfill"
    ]

    assert not invalid_sources, (
        "Unexpected source found in Binance historical dataset: "
        f"{invalid_sources[:10]}"
    )

