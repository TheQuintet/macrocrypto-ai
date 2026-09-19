"""
Integration tests for BTC dominance historical data quality.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.database.session import SessionLocal
from app.models.btc_dominance import BTCDominance


EXPECTED_SOURCES = {
    "coingecko",
    "coinranking_backfill",
    "bgeometrics",
    "bgeometrics_backfill",
}


@pytest.fixture(scope="module")
def btc_dominance_records():
    """
    Load all BTC dominance records directly from the database.

    A dedicated session is used here so this module-scoped fixture does
    not depend on the scope of the shared pytest database fixture.
    """
    db = SessionLocal()

    try:
        records = (
            db.query(BTCDominance)
            .order_by(BTCDominance.time)
            .all()
        )
        return records
    finally:
        db.close()


def test_btc_dominance_data_exists(btc_dominance_records):
    """BTC dominance historical data must exist."""
    assert btc_dominance_records, "No BTC dominance records found"


def test_btc_dominance_row_count(btc_dominance_records):
    """BTC dominance history should contain the expected volume of data."""
    row_count = len(btc_dominance_records)

    print(f"\nBTC dominance row count: {row_count}")

    assert row_count >= 4000, (
        f"BTC dominance history is unexpectedly small: {row_count} rows"
    )


def test_btc_dominance_coverage(btc_dominance_records):
    """
    BTC dominance history should cover the expected historical period.

    Raw timestamps are allowed to contain source-specific time-of-day
    values, so coverage is validated using UTC calendar dates rather
    than requiring the first timestamp to be exactly midnight.
    """
    first_timestamp = btc_dominance_records[0].time
    last_timestamp = btc_dominance_records[-1].time

    first_date = first_timestamp.astimezone(timezone.utc).date()
    last_date = last_timestamp.astimezone(timezone.utc).date()

    expected_first_date = datetime(
        2013,
        4,
        29,
        tzinfo=timezone.utc,
    ).date()

    expected_last_date = datetime.now(timezone.utc).date()

    print(f"\nBTC dominance first timestamp: {first_timestamp}")
    print(f"BTC dominance last timestamp:  {last_timestamp}")
    print(f"BTC dominance first UTC date:  {first_date}")
    print(f"BTC dominance last UTC date:   {last_date}")

    assert first_date <= expected_first_date, (
        f"BTC dominance history starts too late: {first_date}"
    )

    assert last_date <= expected_last_date, (
        f"BTC dominance history contains future dates: {last_date}"
    )


def test_btc_dominance_timestamps_are_timezone_aware(
    btc_dominance_records,
):
    """All BTC dominance timestamps must be timezone-aware."""
    naive_records = [
        record
        for record in btc_dominance_records
        if record.time.tzinfo is None
    ]

    assert not naive_records, (
        f"Found {len(naive_records)} timezone-naive BTC dominance timestamps"
    )


def test_btc_dominance_timestamps_are_utc(btc_dominance_records):
    """All BTC dominance timestamps must represent UTC."""
    non_utc_records = [
        record
        for record in btc_dominance_records
        if record.time.utcoffset() != timedelta(0)
    ]

    assert not non_utc_records, (
        f"Found {len(non_utc_records)} BTC dominance timestamps "
        "that are not UTC"
    )


def test_btc_dominance_has_no_future_observations(
    btc_dominance_records,
):
    """BTC dominance must not contain observations from the future."""
    now = datetime.now(timezone.utc)

    future_records = [
        record
        for record in btc_dominance_records
        if record.time > now
    ]

    assert not future_records, (
        f"Found {len(future_records)} future BTC dominance observations"
    )


def test_btc_dominance_has_no_duplicate_timestamps(
    btc_dominance_records,
):
    """
    Raw BTC dominance timestamps must be unique.

    Multiple observations on the same UTC calendar date are allowed
    because different sources can provide observations at different
    times during the same day.
    """
    timestamps = [record.time for record in btc_dominance_records]

    assert len(timestamps) == len(set(timestamps)), (
        "Duplicate BTC dominance timestamps found"
    )


def test_btc_dominance_values_are_present(btc_dominance_records):
    """All BTC dominance records must contain a dominance value."""
    missing_values = [
        record
        for record in btc_dominance_records
        if record.dominance is None
    ]

    assert not missing_values, (
        f"Found {len(missing_values)} BTC dominance records "
        "with missing values"
    )


def test_btc_dominance_values_are_valid_percentages(
    btc_dominance_records,
):
    """
    BTC dominance values must be valid percentages between 0 and 100.
    """
    invalid_records = [
        record
        for record in btc_dominance_records
        if not 0 <= float(record.dominance) <= 100
    ]

    assert not invalid_records, (
        f"Found {len(invalid_records)} BTC dominance values "
        "outside the 0-100 percentage range"
    )


def test_btc_dominance_sources_are_present(btc_dominance_records):
    """Every BTC dominance record must identify its source."""
    missing_sources = [
        record
        for record in btc_dominance_records
        if not record.source
    ]

    assert not missing_sources, (
        f"Found {len(missing_sources)} BTC dominance records "
        "with missing sources"
    )


def test_btc_dominance_sources_are_expected(btc_dominance_records):
    """All BTC dominance sources must be recognized sources."""
    actual_sources = {
        record.source
        for record in btc_dominance_records
    }

    unexpected_sources = sorted(
        actual_sources - EXPECTED_SOURCES
    )

    print(f"\nBTC dominance sources: {sorted(actual_sources)}")

    assert not unexpected_sources, (
        f"Unexpected BTC dominance sources found: "
        f"{unexpected_sources}"
    )


def test_btc_dominance_daily_coverage_is_reported(
    btc_dominance_records,
):
    """
    Report daily calendar coverage and maximum gap.

    Missing calendar days are reported rather than treated as a hard
    failure because raw historical sources can contain legitimate
    coverage gaps.
    """
    dates = sorted(
        {
            record.time.astimezone(timezone.utc).date()
            for record in btc_dominance_records
        }
    )

    assert dates, "No BTC dominance observation dates found"

    expected_days = (dates[-1] - dates[0]).days + 1
    observed_days = len(dates)
    missing_days = expected_days - observed_days

    gaps = [
        (current - previous).days
        for previous, current in zip(dates, dates[1:])
    ]

    max_gap = max(gaps, default=0)

    print(f"\nBTC dominance first date:   {dates[0]}")
    print(f"BTC dominance last date:    {dates[-1]}")
    print(f"Expected calendar days:     {expected_days}")
    print(f"Observed calendar days:     {observed_days}")
    print(f"Missing calendar days:      {missing_days}")
    print(f"Maximum calendar-day gap:   {max_gap}")

    assert observed_days > 0


def test_btc_dominance_timestamps_are_chronological(
    btc_dominance_records,
):
    """BTC dominance records must be returned in chronological order."""
    timestamps = [
        record.time
        for record in btc_dominance_records
    ]

    assert timestamps == sorted(timestamps), (
        "BTC dominance records are not in chronological order"
    )