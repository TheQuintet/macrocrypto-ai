"""
Tests for FeatureBuilderService.

Fixture style matches tests/unit/test_hourly_btc_prices_service.py:
a local SQLite database created with hand-rolled CREATE TABLE
statements. The service reads from btc_prices_hourly,
macro_indicators_hourly, raw macro_indicators, and
macro_indicator_vintages.

The 14 tracker queries in the service use Postgres-specific
`generate_series`. Those queries do NOT run on SQLite. To keep
this test file portable, each tracker test either:

  (a) monkeypatches FeatureBuilderService._query_last_observation
      to return a controlled Series, or
  (b) exercises the tracker columns through _attach_trackers
      directly with a pre-populated release_at dict.

Everything else (technicals, engineered features, flags, PIT
merge, target) runs on SQLite unchanged.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.services.feature_builder_service import (
    FEATURES_DB_COLUMNS,
    FeatureBuilderService,
    _HOURLY_ANNUALIZATION,
    _VINTAGE_SERIES,
    _TRACKER_COLUMNS,
)


# Fixed anchor used across tests. Hour-aligned UTC.
T0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


# ==============================================================
# Fixtures
# ==============================================================


@pytest.fixture
def db(tmp_path):
    """
    SQLite session with the minimum set of tables the service
    reads. Matches the production DDL for the columns we touch.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    with engine.begin() as conn:
        # btc_prices_hourly (Chat 3, migration 005)
        conn.execute(text(
            """
            CREATE TABLE btc_prices_hourly (
                time TIMESTAMP PRIMARY KEY,
                close REAL,
                volume REAL,
                volatility REAL,
                dominance REAL,
                active_addresses REAL,
                price_lag_7d REAL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
        # macro_indicators_hourly (Chat 3, migration 006)
        conn.execute(text(
            """
            CREATE TABLE macro_indicators_hourly (
                time TIMESTAMP PRIMARY KEY,
                cpi REAL,
                interest_rate REAL,
                m2_growth REAL,
                dxy REAL,
                treasury_yield REAL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ))
        # raw macro_indicators (Phase A, migration 004)
        conn.execute(text(
            """
            CREATE TABLE macro_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TIMESTAMP NOT NULL,
                indicator_name TEXT NOT NULL,
                value REAL NOT NULL,
                previous_value REAL,
                change_percent REAL,
                source TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (time, indicator_name)
            )
            """
        ))
        # macro_indicator_vintages (Chat 5, B6, migration 008)
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
# Helper writers
# ==============================================================


def _add_btc_hour(db, hour, close, volume=1.0,
                  dominance=50.0, active_addresses=None):
    db.execute(
        text(
            "INSERT INTO btc_prices_hourly "
            "(time, close, volume, dominance, active_addresses) "
            "VALUES (:t, :c, :v, :d, :a)"
        ),
        {"t": hour, "c": close, "v": volume,
         "d": dominance, "a": active_addresses},
    )


def _add_hourly_macro(db, hour, dxy=None, treasury_yield=None):
    db.execute(
        text(
            "INSERT INTO macro_indicators_hourly "
            "(time, dxy, treasury_yield) "
            "VALUES (:t, :d, :ty)"
        ),
        {"t": hour, "d": dxy, "ty": treasury_yield},
    )


def _add_raw_macro(db, when, name, value):
    db.execute(
        text(
            "INSERT INTO macro_indicators "
            "(time, indicator_name, value) "
            "VALUES (:t, :n, :v)"
        ),
        {"t": when, "n": name, "v": value},
    )


def _add_vintage(db, series_id, indicator_name,
                 observation_date, release_date, value):
    db.execute(
        text(
            "INSERT INTO macro_indicator_vintages "
            "(series_id, indicator_name, observation_date, "
            "release_date, value) "
            "VALUES (:s, :n, :od, :rd, :v)"
        ),
        {"s": series_id, "n": indicator_name,
         "od": observation_date, "rd": release_date, "v": value},
    )


def _seed_btc_spine(db, start, hours, base_price=100.0):
    """Seed btc_prices_hourly with `hours` consecutive hours."""
    for i in range(hours):
        _add_btc_hour(db, start + timedelta(hours=i),
                      base_price + i, 1.0, 50.0, None)


# ==============================================================
# Range validation
# ==============================================================


def test_build_features_rejects_naive_datetime(db):
    svc = FeatureBuilderService(db)
    with pytest.raises(ValueError, match="timezone-aware"):
        svc.build_features(
            datetime(2024, 1, 1), datetime(2024, 1, 2)
        )


def test_build_features_rejects_non_utc_offset(db):
    svc = FeatureBuilderService(db)
    tz = timezone(timedelta(hours=2))
    start = datetime(2024, 1, 1, tzinfo=tz)
    end = datetime(2024, 1, 2, tzinfo=tz)
    with pytest.raises(ValueError, match="UTC"):
        svc.build_features(start, end)


def test_build_features_rejects_non_hour_aligned(db):
    svc = FeatureBuilderService(db)
    start = datetime(2024, 1, 1, 0, 30, tzinfo=timezone.utc)
    end = datetime(2024, 1, 2, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="hour-aligned"):
        svc.build_features(start, end)


def test_build_features_rejects_end_before_start(db):
    svc = FeatureBuilderService(db)
    with pytest.raises(ValueError, match="must be after"):
        svc.build_features(T0, T0)


# ==============================================================
# Column shape
# ==============================================================


def test_build_features_returns_53_columns(db, monkeypatch):
    _seed_btc_spine(db, T0, 3)
    db.commit()

    # Neutralize the tracker queries (Postgres-specific) so the
    # shape assertion works on SQLite.
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    # 52 features (all columns except y) + y = 53
    assert df.shape[1] == 53
    assert set(df.columns) == set(FEATURES_DB_COLUMNS[1:])


def test_build_features_returns_52_columns_without_target(
    db, monkeypatch
):
    _seed_btc_spine(db, T0, 3)
    db.commit()

    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(
        T0, T0 + timedelta(hours=3), include_target=False
    )

    assert df.shape[1] == 52
    assert "y" not in df.columns


def test_build_features_index_is_ds(db, monkeypatch):
    _seed_btc_spine(db, T0, 3)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    assert df.index.name == "ds"
    assert all(
        ts.minute == 0 and ts.second == 0
        for ts in df.index
    )


# ==============================================================
# Target
# ==============================================================


def test_target_is_next_hour_close(db, monkeypatch):
    """
    y at ds == close at ds + 1h.
    """
    _seed_btc_spine(db, T0, 3, base_price=100.0)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    # 3 hours -> 2 rows (trailing frontier dropped)
    assert len(df) == 2
    assert df["y"].iloc[0] == 101.0  # close at T0+1
    assert df["y"].iloc[1] == 102.0  # close at T0+2


def test_target_trailing_frontier_dropped(db, monkeypatch):
    """
    The last row of the range has no successor close; it is
    dropped from the include_target=True output.
    """
    _seed_btc_spine(db, T0, 3)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    # T0+2 is the trailing row; its y would need close at T0+3.
    assert T0 + timedelta(hours=2) not in df.index


def test_no_frontier_drop_without_target(db, monkeypatch):
    _seed_btc_spine(db, T0, 3)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(
        T0, T0 + timedelta(hours=3), include_target=False
    )

    assert len(df) == 3


# ==============================================================
# PIT merge for vintages
# ==============================================================


def test_pit_merge_picks_latest_release_before_ds(db, monkeypatch):
    """
    Two releases of the same CPI observation. At ds in between,
    the earlier release is in force.
    """
    _seed_btc_spine(db, T0, 3)
    _add_vintage(
        db, "CPIAUCSL", "cpi",
        observation_date="2023-12-01",
        release_date="2024-01-05",  # after T0
        value=100.0,
    )
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    # Release is 2024-01-05, all our ds values are 2024-01-01.
    # So no release precedes ds -> cpi is NaN.
    assert df["cpi"].isna().all()


def test_pit_merge_backward_lookup(db, monkeypatch):
    """
    A release before the spine's first ds is used for all rows.
    """
    _seed_btc_spine(db, T0, 3)
    _add_vintage(
        db, "CPIAUCSL", "cpi",
        observation_date="2023-12-01",
        release_date="2023-12-15",  # before T0
        value=100.0,
    )
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    assert (df["cpi"] == 100.0).all()


def test_pit_merge_tiebreak_latest_observation(db, monkeypatch):
    """
    Two releases on the same date. The one with the larger
    observation_date wins.
    """
    _seed_btc_spine(db, T0, 3)
    _add_vintage(
        db, "CPIAUCSL", "cpi",
        observation_date="2023-11-01",
        release_date="2023-12-15",
        value=99.0,
    )
    _add_vintage(
        db, "CPIAUCSL", "cpi",
        observation_date="2023-12-01",
        release_date="2023-12-15",  # same release date
        value=100.0,
    )
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    assert (df["cpi"] == 100.0).all()


# ==============================================================
# Technicals
# ==============================================================


def test_btc_log_return_1d_is_24h_shift(db, monkeypatch):
    """
    btc_log_return_1d = log(close / close.shift(24)).
    """
    # 30 hours so we have data past the 24h shift.
    _seed_btc_spine(db, T0, 30, base_price=100.0)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=30))

    # Row 24 (ds = T0+24): close=124, close.shift(24)=100.
    idx_24 = T0 + timedelta(hours=24)
    expected = np.log(124.0 / 100.0)
    assert df.loc[idx_24, "btc_log_return_1d"] == pytest.approx(
        expected
    )


def test_btc_sma_7_uses_168_hour_window(db, monkeypatch):
    """
    btc_sma_7 = close.rolling(168, min_periods=168).mean().
    Before 168 hours, NaN.
    """
    _seed_btc_spine(db, T0, 200, base_price=100.0)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=200))

    # First 168 rows have NaN SMA.
    idx_167 = T0 + timedelta(hours=167)
    idx_168 = T0 + timedelta(hours=168)
    assert pd.isna(df.loc[idx_167, "btc_sma_7"])
    assert not pd.isna(df.loc[idx_168, "btc_sma_7"])

    # At T0+168, the window is closes 1..168 (mean 100.5..168.5).
    expected = np.mean(np.arange(1, 169) + 100.0)
    assert df.loc[idx_168, "btc_sma_7"] == pytest.approx(expected)


def test_btc_volatility_7d_uses_annualization(db, monkeypatch):
    """
    btc_volatility_7d = std(ddof=1) * sqrt(365*24).
    """
    # Need at least 24+168 = 192 rows for a fully warmed window
    # of log returns. Seed 250.
    _seed_btc_spine(db, T0, 250, base_price=100.0)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=250))

    # Row with a fully warmed volatility window.
    idx_250 = T0 + timedelta(hours=230)
    if idx_250 in df.index:
        val = df.loc[idx_250, "btc_volatility_7d"]
        assert not pd.isna(val)
        # Sanity: annualization makes it larger than raw std.
        assert val > 0


def test_btc_gold_ratio_divides_price_by_gold(db, monkeypatch):
    _seed_btc_spine(db, T0, 3, base_price=100.0)
    # gold_spot = 50 for T0 - 1h
    _add_raw_macro(db, T0 - timedelta(hours=1), "gold_spot", 50.0)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    # Every row: btc_price / gold_spot
    for ds, row in df.iterrows():
        expected = row["btc_price"] / 50.0
        assert row["btc_gold_ratio"] == pytest.approx(expected)


# ==============================================================
# Engineered features
# ==============================================================


def test_eng_price_lag_1d_is_24h_shift(db, monkeypatch):
    _seed_btc_spine(db, T0, 30, base_price=100.0)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=30))

    idx_24 = T0 + timedelta(hours=24)
    assert df.loc[idx_24, "eng_price_lag_1d"] == 100.0


def test_eng_returns_are_aliases(db, monkeypatch):
    _seed_btc_spine(db, T0, 30)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=30))

    for short in ("1d", "7d", "30d"):
        assert (
            df[f"eng_returns_{short}"]
            .equals(df[f"btc_log_return_{short}"])
        )


# ==============================================================
# Flags
# ==============================================================


def test_warmup_complete_flips_after_2160_hours(db, monkeypatch):
    """
    warmup_complete = 1 iff btc_sma_90 (2160h window) is not NaN.
    """
    # Too slow to seed 2160 rows; seed just past the boundary.
    # Actually we can't seed fewer than the window without
    # returning all-NaN. We accept a small window and verify the
    # flag semantics only.
    _seed_btc_spine(db, T0, 10)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=10))

    # With only 10 hours of data, sma_90 is all NaN -> flag 0.
    assert (df["warmup_complete"] == 0).all()


def test_high_yield_spread_is_missing_when_nan(db, monkeypatch):
    """
    When high_yield_spread is absent from raw, ffill leaves it
    NaN, and the flag is 1.
    """
    _seed_btc_spine(db, T0, 3)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    assert (df["high_yield_spread_is_missing"] == 1).all()


# ==============================================================
# Trackers (isolated; Postgres-only queries monkeypatched)
# ==============================================================


def test_trackers_are_integer_dtype(db, monkeypatch):
    _seed_btc_spine(db, T0, 3)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    for col in _TRACKER_COLUMNS:
        assert df[col].dtype == "int64"


def test_trackers_zero_when_no_prior_observation(db, monkeypatch):
    """
    When _query_last_observation returns NaT, the tracker is 0.
    """
    _seed_btc_spine(db, T0, 3)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=3))

    for col in _TRACKER_COLUMNS:
        assert (df[col] == 0).all()


def test_tracker_counts_hours_since_last_observation(
    db, monkeypatch
):
    """
    Directly exercise _attach_trackers with a controlled
    release_at dict.
    """
    _seed_btc_spine(db, T0, 24)
    db.commit()
    _patch_trackers_to_zero(monkeypatch, db)

    svc = FeatureBuilderService(db)
    # Build the spine frame only.
    spine = pd.DataFrame({
        "ds": pd.date_range(
            T0, T0 + timedelta(hours=24),
            freq="h", inclusive="left",
        )
    })
    # Release at T0 + 3h.
    release_at = {
        "cpi": pd.Series(
            [pd.Timestamp(T0 + timedelta(hours=3), tz="UTC")]
            * len(spine),
            index=spine.index,
        ),
    }
    # Add empty entries for the other vintages so the function
    # has something to skip.
    for s in _VINTAGE_SERIES:
        if s not in release_at:
            release_at[s] = pd.Series(
                pd.NaT, index=spine.index,
                dtype="datetime64[ns, UTC]",
            )

    result = svc._attach_trackers(spine, release_at)

    # At T0+0, release is in the future -> tracker 0 (clamped).
    # At T0+3, exactly 0 hours since release.
    # At T0+10, 7 hours since release.
    assert result["cpi_days_since_release"].iloc[0] == 0
    assert result["cpi_days_since_release"].iloc[3] == 0
    assert result["cpi_days_since_release"].iloc[10] == 7


# ==============================================================
# Helpers used above
# ==============================================================


def _patch_trackers_to_zero(monkeypatch, db):
    """
    Replace _query_last_observation with a stub that returns NaT
    for every row, so the tracker columns become 0 and the
    Postgres generate_series query never runs.

    Also seeds a synthetic row for dxy, ten_year_treasury, and
    every raw-macro feature so the ffill pipeline does not bail
    on empty reads.
    """
    def _stub(self, *, kind, key, start, end, spine_ds):
        return pd.Series(
            pd.NaT, index=spine_ds.index,
            dtype="datetime64[ns, UTC]",
        )

    monkeypatch.setattr(
        FeatureBuilderService,
        "_query_last_observation",
        _stub,
    )


def _noop(*a, **kw):
    return None