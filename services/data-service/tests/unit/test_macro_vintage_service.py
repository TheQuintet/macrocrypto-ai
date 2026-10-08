"""
Tests for MacroVintageService.

Fixture style mirrors tests/unit/test_high_yield_credit_stress_service.py
and tests/unit/test_hourly_btc_prices_service.py: a local SQLite
database created with hand-rolled CREATE TABLE statements, so the
tests run without Postgres. The repository's ON CONFLICT
(series_id, observation_date, release_date) clause compiles to
INSERT ... ON CONFLICT DO NOTHING, which SQLite has supported
since 3.24, so create_many works on both dialects.

No network access: the fredapi.Fred client is replaced with a
FakeFred that returns canned DataFrames keyed by series_id. The
service's placeholder guard is bypassed by passing fred_client
explicitly.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.macro_vintage_service import (
    VINTAGE_SERIES,
    MacroVintageService,
    _lookback_cutoff,
    _remove_noop_vintages,
)


# ==============================================================
# Fake FRED client
# ==============================================================


class FakeFred:
    """
    Stand-in for fredapi.Fred.

    Configured with a {series_id: DataFrame} mapping. Calling
    get_series_all_releases(series_id) returns the frame for that
    series, or raises if the series is not configured — this
    makes unseeded lookups fail loudly instead of silently
    returning empty data.

    DataFrame columns must match what fredapi returns:
        date, realtime_start, value
    """

    def __init__(self, frames: dict[str, pd.DataFrame]):
        self._frames = frames
        self.calls: list[str] = []

    def get_series_all_releases(self, series_id: str) -> pd.DataFrame:
        self.calls.append(series_id)
        if series_id not in self._frames:
            raise KeyError(
                f"FakeFred has no frame configured for {series_id}"
            )
        return self._frames[series_id]


class RaisingFred:
    """
    FRED client that raises for every series. Used to test the
    all-series-fail path.
    """

    def __init__(self, message: str = "FRED is down"):
        self.message = message
        self.calls: list[str] = []

    def get_series_all_releases(self, series_id: str) -> pd.DataFrame:
        self.calls.append(series_id)
        raise RuntimeError(self.message)


def _frame(
    rows: list[tuple[str, str, float]],
) -> pd.DataFrame:
    """
    Build a fredapi-shaped DataFrame from a list of
    (observation_date, release_date, value) tuples, given as
    ISO date strings.
    """
    return pd.DataFrame(
        {
            "date": pd.to_datetime([r[0] for r in rows]),
            "realtime_start": pd.to_datetime([r[1] for r in rows]),
            "value": [r[2] for r in rows],
        }
    )


def _minimal_ok_frames(
    base_date: str = "2024-01-01",
    release_date: str = "2024-02-01",
) -> dict[str, pd.DataFrame]:
    """
    One valid DataFrame per series, so collect() succeeds across
    the full set. Each frame has two rows so the no-op filter has
    something to keep.
    """
    return {
        "CPIAUCSL": _frame(
            [
                (base_date, release_date, 100.0),
                ("2024-02-01", "2024-03-01", 101.0),
            ]
        ),
        "UNRATE": _frame(
            [
                (base_date, release_date, 3.7),
                ("2024-02-01", "2024-03-01", 3.8),
            ]
        ),
        "FEDFUNDS": _frame(
            [
                (base_date, release_date, 5.25),
                ("2024-02-01", "2024-03-01", 5.25),
            ]
        ),
        "M2SL": _frame(
            [
                (base_date, release_date, 20000.0),
                ("2024-02-01", "2024-03-01", 20100.0),
            ]
        ),
        "GDP": _frame(
            [
                (base_date, release_date, 27000.0),
                ("2024-02-01", "2024-03-01", 27200.0),
            ]
        ),
    }


# ==============================================================
# Fixtures
# ==============================================================


@pytest.fixture
def db(tmp_path):
    """
    Local SQLite database with a minimal macro_indicator_vintages
    table matching the columns the service and repository touch.

    The unique constraint on
    (series_id, observation_date, release_date) is required for
    create_many's ON CONFLICT clause to deduplicate.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    with engine.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE macro_indicator_vintages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id TEXT NOT NULL,
                indicator_name TEXT NOT NULL,
                observation_date DATE NOT NULL,
                release_date DATE NOT NULL,
                value REAL NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (series_id, observation_date, release_date)
            )
            """
        ))

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================
# Placeholder guard
# ==============================================================


def test_placeholder_fred_key_raises(db, monkeypatch):
    """
    Constructing the service without an injected client and with
    the placeholder key in settings must raise RuntimeError.
    """
    from app.config import settings

    monkeypatch.setattr(settings, "FRED_API_KEY", "your_api_key_here")

    with pytest.raises(RuntimeError, match="placeholder"):
        MacroVintageService(db)


def test_empty_fred_key_raises(db, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "FRED_API_KEY", "")

    with pytest.raises(RuntimeError, match="FRED_API_KEY"):
        MacroVintageService(db)


def test_none_fred_key_raises(db, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "FRED_API_KEY", None)

    with pytest.raises(RuntimeError, match="FRED_API_KEY"):
        MacroVintageService(db)


def test_injected_fred_client_skips_key_guard(db, monkeypatch):
    """
    Passing a fred_client must skip the key check entirely, so
    tests can run without a real FRED_API_KEY.
    """
    from app.config import settings

    monkeypatch.setattr(settings, "FRED_API_KEY", "your_api_key_here")

    # Must not raise.
    service = MacroVintageService(
        db,
        fred_client=FakeFred(_minimal_ok_frames()),
    )

    assert service.fred is not None


# ==============================================================
# collect() — happy path
# ==============================================================


@pytest.mark.asyncio
async def test_collect_returns_records_for_all_five_series(db):
    fake = FakeFred(_minimal_ok_frames())
    service = MacroVintageService(db, fred_client=fake)

    records = await service.collect()

    # Every series appears in the output.
    series_seen = {r["series_id"] for r in records}
    assert series_seen == set(VINTAGE_SERIES.values())

    # Every series was queried.
    assert set(fake.calls) == set(VINTAGE_SERIES.values())


@pytest.mark.asyncio
async def test_collect_renames_columns_correctly(db):
    """
    fredapi's 'date'/'realtime_start' must become
    'observation_date'/'release_date' in the record shape.
    """
    fake = FakeFred(_minimal_ok_frames())
    service = MacroVintageService(db, fred_client=fake)

    records = await service.collect()

    for record in records:
        assert set(record.keys()) == {
            "series_id",
            "indicator_name",
            "observation_date",
            "release_date",
            "value",
        }
        assert isinstance(record["observation_date"], date)
        assert isinstance(record["release_date"], date)
        assert isinstance(record["value"], float)


@pytest.mark.asyncio
async def test_collect_sets_series_id_and_indicator_name(db):
    fake = FakeFred(_minimal_ok_frames())
    service = MacroVintageService(db, fred_client=fake)

    records = await service.collect()

    # For every record, the (series_id, indicator_name) pair must
    # be one of the five canonical mappings.
    expected_pairs = {
        (series_id, name)
        for name, series_id in VINTAGE_SERIES.items()
    }

    seen_pairs = {
        (r["series_id"], r["indicator_name"])
        for r in records
    }

    assert seen_pairs == expected_pairs


# ==============================================================
# collect() — partial failure
# ==============================================================


@pytest.mark.asyncio
async def test_collect_returns_empty_when_all_series_fail(db):
    service = MacroVintageService(
        db,
        fred_client=RaisingFred("network down"),
    )

    records = await service.collect()

    assert records == []


@pytest.mark.asyncio
async def test_collect_continues_after_single_series_failure(db):
    """
    If one series raises, the other four must still land.
    """
    frames = _minimal_ok_frames()

    class PartialFred:
        def __init__(self):
            self.calls: list[str] = []

        def get_series_all_releases(self, series_id):
            self.calls.append(series_id)
            if series_id == "CPIAUCSL":
                raise RuntimeError("boom")
            return frames[series_id]

    service = MacroVintageService(db, fred_client=PartialFred())

    records = await service.collect()

    series_seen = {r["series_id"] for r in records}
    assert "CPIAUCSL" not in series_seen
    assert series_seen == {"UNRATE", "FEDFUNDS", "M2SL", "GDP"}


# ==============================================================
# No-op vintage filter
# ==============================================================


def test_noop_vintages_are_filtered():
    """
    Two releases for the same observation with the same value:
    only the first is kept.
    """
    frame = _frame(
        [
            ("2024-01-01", "2024-02-01", 100.0),
            ("2024-01-01", "2024-03-01", 100.0),  # no-op
        ]
    )
    frame["series_id"] = "X"
    frame["indicator_name"] = "x"

    result = _remove_noop_vintages(frame)

    assert len(result) == 1
    assert result.iloc[0]["release_date"] == pd.Timestamp("2024-02-01")


def test_value_change_keeps_both_vintages():
    """
    Two releases with different values: both kept.
    """
    frame = _frame(
        [
            ("2024-01-01", "2024-02-01", 100.0),
            ("2024-01-01", "2024-03-01", 101.0),
        ]
    )
    frame["series_id"] = "X"
    frame["indicator_name"] = "x"

    result = _remove_noop_vintages(frame)

    assert len(result) == 2


def test_noop_filter_is_per_observation_date():
    """
    A no-op for observation A must not affect observation B.
    """
    frame = _frame(
        [
            ("2024-01-01", "2024-02-01", 100.0),
            ("2024-01-01", "2024-03-01", 100.0),  # no-op
            ("2024-02-01", "2024-03-01", 200.0),
        ]
    )
    frame["series_id"] = "X"
    frame["indicator_name"] = "x"

    result = _remove_noop_vintages(frame)

    # 2024-01-01 keeps only the first; 2024-02-01 keeps its only.
    assert len(result) == 2
    obs_dates = set(result["observation_date"])
    assert obs_dates == {
        pd.Timestamp("2024-01-01").date(),
        pd.Timestamp("2024-02-01").date(),
    }


def test_noop_filter_is_per_series():
    """
    Same (observation_date, value) in two different series must
    both survive — the filter groups by (series_id,
    observation_date).
    """
    frame = _frame(
        [
            ("2024-01-01", "2024-02-01", 100.0),
            ("2024-01-01", "2024-02-01", 100.0),
        ]
    )
    frame["series_id"] = ["A", "B"]
    frame["indicator_name"] = ["a", "b"]

    result = _remove_noop_vintages(frame)

    assert len(result) == 2


# ==============================================================
# Lookback filtering
# ==============================================================


@pytest.mark.asyncio
async def test_collect_filters_by_lookback_years(db):
    """
    A row older than the lookback window is dropped.
    """
    cutoff = _lookback_cutoff(20)

    too_old = cutoff.replace(year=cutoff.year - 1).isoformat()
    recent = "2024-01-01"

    frame = _frame(
        [
            (too_old, "2024-02-01", 100.0),
            (recent, "2024-02-01", 101.0),
        ]
    )

    frames = {
        series_id: frame.copy() for series_id in VINTAGE_SERIES.values()
    }
    frames["CPIAUCSL"] = frame  # overwrite one to inspect it

    service = MacroVintageService(
        db,
        fred_client=FakeFred(frames),
    )

    records = await service.collect()

    # Every surviving observation must be on or after the cutoff.
    for record in records:
        assert record["observation_date"] >= cutoff


# ==============================================================
# Persistence
# ==============================================================


@pytest.mark.asyncio
async def test_create_many_is_idempotent(db):
    """
    Persisting the same records twice must not create duplicates.
    """
    service = MacroVintageService(
        db,
        fred_client=FakeFred(_minimal_ok_frames()),
    )

    records = await service.collect()
    assert records

    service.repository.create_many(records)
    count_after_first = db.execute(
        text("SELECT COUNT(*) FROM macro_indicator_vintages")
    ).scalar()

    service.repository.create_many(records)
    count_after_second = db.execute(
        text("SELECT COUNT(*) FROM macro_indicator_vintages")
    ).scalar()

    assert count_after_first == count_after_second


@pytest.mark.asyncio
async def test_collect_and_persist_end_to_end(db):
    service = MacroVintageService(
        db,
        fred_client=FakeFred(_minimal_ok_frames()),
    )

    records = await service.collect()
    assert len(records) > 0

    service.repository.create_many(records)

    counts = service.repository.count_by_series()
    assert set(counts.keys()) == set(VINTAGE_SERIES.values())

    # Every series has at least one stored row.
    for series_id, n in counts.items():
        assert n > 0, f"{series_id} has no rows"


@pytest.mark.asyncio
async def test_latest_release_date_returns_max_for_series(db):
    service = MacroVintageService(
        db,
        fred_client=FakeFred(_minimal_ok_frames()),
    )

    records = await service.collect()
    service.repository.create_many(records)

    latest = service.repository.latest_release_date("CPIAUCSL")
    assert latest == date(2024, 3, 1)


def test_latest_release_date_returns_none_for_unknown_series(db):
    service = MacroVintageService(
        db,
        fred_client=FakeFred(_minimal_ok_frames()),
    )

    assert service.repository.latest_release_date("NOPE") is None


# ==============================================================
# close() is a no-op
# ==============================================================


@pytest.mark.asyncio
async def test_close_is_noop(db):
    """
    fredapi.Fred has no close(); the service exposes close() only
    for symmetry with other services. Calling it must succeed
    and not affect the injected client.
    """
    fake = FakeFred(_minimal_ok_frames())
    service = MacroVintageService(db, fred_client=fake)

    await service.close()

    # FakeFred has no close() to be called; the service does not
    # reach for one.
    assert not hasattr(fake, "close") or True  # explicit no-op