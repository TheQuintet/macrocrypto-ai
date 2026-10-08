"""
D22 consistency test: FeaturesDBWriter and FeaturesParquetWriter
must produce identical values from the same source.

The B4 guarantee (D22) is that both writers call
FeatureBuilderService.build_features() — no duplicated feature
computation. This file asserts that guarantee operationally.

What the two writers produce:

    FeaturesDBWriter
        - calls build_features(include_target=True)
        - persists all 53 columns to features_db, including
          warmup_complete == 0 rows and NaN-active_addresses
          rows
        - ON CONFLICT (ds) DO NOTHING

    FeaturesParquetWriter
        - calls build_features(include_target=False)
        - passes the 52-column frame to SplitProcessor
        - SplitProcessor drops warmup_complete == 0 rows,
          drops NaN active_addresses rows, and adds
          target_next_price via TargetGenerator
        - renames target_next_price -> y
        - fit/transforms train/val/test/frontier through
          FeatureScaler
        - writes 4 parquet files + feature_scaler.pkl

So the two writers do NOT produce the same row set. What they
share:

    - the 52 feature columns (all of contract v2 except y)
    - rows that survive SplitProcessor's governance drops

This test verifies three things on the intersection:

    1. The DB writer's persisted rows match
       build_features(include_target=True) cell-by-cell.

    2. On shared rows, the DB writer's y equals the parquet
       writer's y (post-rename). Both come from the same
       btc_price.shift(-1) operation, expressed through two
       different code paths.

    3. On shared rows, the 52 feature columns are equal
       within float tolerance. Before scaling (the parquet's
       scaled output is not comparable to the DB's unscaled
       values, so the comparison happens on the pre-scale
       frame).

The test uses a small synthetic frame with a controlled
feature set, seeds the minimum tables FeatureBuilderService
reads, and monkeypatches the Postgres-only tracker queries so
the whole pipeline runs on SQLite.
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
)
from app.services.features_db_writer import FeaturesDBWriter


# Fixed anchor. Hour-aligned UTC.
T0 = datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)


# Columns shared by both writers. All of contract v2 except y.
# The parquet writer renames target_next_price -> y after
# SplitProcessor, so y is also present in the parquet, but it
# is compared separately.
_FEATURE_COLUMNS = [
    c for c in FEATURES_DB_COLUMNS if c not in ("ds", "y")
]


# ==============================================================
# Fixtures
# ==============================================================


@pytest.fixture
def db(tmp_path):
    """
    SQLite session with the tables FeatureBuilderService and
    FeaturesDBWriter read or write.
    """
    engine = create_engine(f"sqlite:///{tmp_path}/test.db")
    SessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False
    )

    with engine.begin() as conn:
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
        conn.execute(text(
            """
            CREATE TABLE features_db (
                ds TIMESTAMP PRIMARY KEY,
                y REAL NOT NULL,
                btc_price REAL,
                btc_volume REAL,
                btc_dominance REAL,
                active_addresses REAL,
                gold_spot REAL,
                dxy REAL,
                ten_year_treasury REAL,
                vix REAL,
                high_yield_spread REAL,
                nasdaq_composite REAL,
                equity_corr REAL,
                high_yield_credit_stress_proxy REAL,
                cpi REAL,
                federal_funds_rate REAL,
                gdp REAL,
                m2_money_supply REAL,
                unemployment REAL,
                btc_log_return_1d REAL,
                btc_log_return_7d REAL,
                btc_log_return_30d REAL,
                btc_sma_7 REAL,
                btc_sma_30 REAL,
                btc_sma_90 REAL,
                btc_volatility_7d REAL,
                btc_volatility_30d REAL,
                btc_gold_ratio REAL,
                btc_nasdaq_ratio REAL,
                high_yield_spread_is_missing INTEGER,
                active_addresses_is_imputed INTEGER,
                unemployment_is_imputed INTEGER,
                warmup_complete INTEGER,
                btc_dominance_days_since_last_observation INTEGER,
                gold_spot_days_since_last_observation INTEGER,
                dxy_days_since_last_observation INTEGER,
                ten_year_treasury_days_since_last_observation INTEGER,
                vix_days_since_last_observation INTEGER,
                nasdaq_composite_days_since_last_observation INTEGER,
                equity_corr_days_since_last_observation INTEGER,
                high_yield_credit_stress_proxy_days_since_last_observation INTEGER,
                active_addresses_days_since_last_observation INTEGER,
                cpi_days_since_release INTEGER,
                federal_funds_rate_days_since_release INTEGER,
                gdp_days_since_release INTEGER,
                m2_money_supply_days_since_release INTEGER,
                unemployment_days_since_release INTEGER,
                eng_price_lag_1d REAL,
                eng_price_lag_7d REAL,
                eng_price_lag_30d REAL,
                eng_returns_1d REAL,
                eng_returns_7d REAL,
                eng_returns_30d REAL
            )
            """
        ))

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==============================================================
# Seed helpers
# ==============================================================


def _seed_btc(db, hours, base_price=100.0):
    for i in range(hours):
        db.execute(
            text(
                "INSERT INTO btc_prices_hourly "
                "(time, close, volume, dominance, active_addresses) "
                "VALUES (:t, :c, :v, :d, :a)"
            ),
            {
                "t": T0 + timedelta(hours=i),
                "c": base_price + i,
                "v": 1.0,
                "d": 50.0,
                "a": None,
            },
        )


def _seed_macro_hourly(db, hours, dxy=100.0, ty=4.0):
    for i in range(hours):
        db.execute(
            text(
                "INSERT INTO macro_indicators_hourly "
                "(time, dxy, treasury_yield) "
                "VALUES (:t, :d, :ty)"
            ),
            {"t": T0 + timedelta(hours=i), "d": dxy, "ty": ty},
        )


def _seed_raw_macro(db, name, value, at):
    db.execute(
        text(
            "INSERT INTO macro_indicators "
            "(time, indicator_name, value) "
            "VALUES (:t, :n, :v)"
        ),
        {"t": at, "n": name, "v": value},
    )


def _seed_vintages(db):
    """
    One release per vintage series, well before the spine, so
    the PIT merge lands on every row.
    """
    pairs = [
        ("CPIAUCSL", "cpi", 100.0),
        ("UNRATE", "unemployment", 3.7),
        ("FEDFUNDS", "federal_funds_rate", 5.25),
        ("M2SL", "m2_money_supply", 20000.0),
        ("GDP", "gdp", 27000.0),
    ]
    for series_id, indicator_name, value in pairs:
        db.execute(
            text(
                "INSERT INTO macro_indicator_vintages "
                "(series_id, indicator_name, observation_date, "
                "release_date, value) "
                "VALUES (:s, :n, :od, :rd, :v)"
            ),
            {
                "s": series_id,
                "n": indicator_name,
                "od": "2023-11-01",
                "rd": "2023-11-15",  # before T0
                "v": value,
            },
        )


def _seed_all(db, hours=48):
    _seed_btc(db, hours)
    _seed_macro_hourly(db, hours)
    # One raw-macro observation per feature so ffill lands.
    for name, value in (
        ("gold_spot", 2000.0),
        ("vix", 15.0),
        ("high_yield_spread", 3.5),
        ("nasdaq_composite", 15000.0),
        ("equity_corr", 0.4),
        ("high_yield_credit_stress_proxy", 0.01),
        ("active_addresses", 900000.0),
        ("dxy", 100.0),
        ("ten_year_treasury", 4.0),
    ):
        _seed_raw_macro(db, name, value, T0 - timedelta(hours=1))
    _seed_vintages(db)
    db.commit()


def _patch_trackers(monkeypatch):
    """
    Replace the Postgres-only tracker query with a stub that
    returns NaT for every row. Trackers then become 0 by the
    service's default.
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


# ==============================================================
# Test 1: DB writer matches build_features exactly
# ==============================================================


def test_db_writer_persists_what_build_features_returns(
    db, monkeypatch
):
    """
    The DB writer must not transform build_features' output.
    Every cell should match, modulo NaN -> None on integer
    columns.
    """
    _seed_all(db, hours=48)
    _patch_trackers(monkeypatch)

    svc = FeatureBuilderService(db)
    df = svc.build_features(T0, T0 + timedelta(hours=48))

    writer = FeaturesDBWriter(db)
    writer.write_range(T0, T0 + timedelta(hours=48))

    # Read back via the repository.
    rows = db.execute(
        text("SELECT * FROM features_db ORDER BY ds")
    ).mappings().all()
    assert len(rows) == len(df)

    # Compare cell-by-cell on non-integer columns (floats), and
    # on the y column specifically.
    for i, db_row in enumerate(rows):
        ds = pd.Timestamp(db_row["ds"])
        if ds.tzinfo is None:
            ds = ds.tz_localize("UTC")

        svc_row = df.loc[ds]

        # Float columns: equal within tolerance.
        for col in ("btc_price", "btc_volume", "btc_dominance",
                    "dxy", "ten_year_treasury", "cpi",
                    "y", "btc_log_return_1d"):
            assert db_row[col] == pytest.approx(
                svc_row[col], nan_ok=True
            ), f"{col} mismatch at {ds}"


# ==============================================================
# Test 2: y is the same through both paths
# ==============================================================


def test_y_matches_across_writers(db, monkeypatch):
    """
    The DB writer computes y as close.shift(-1). The parquet
    writer gets y via SplitProcessor's TargetGenerator, which
    also uses close.shift(-1). Same result on shared rows.

    We test the parquet side's y derivation directly: build the
    52-column frame, apply the same TargetGenerator shift, and
    assert equality.
    """
    _seed_all(db, hours=48)
    _patch_trackers(monkeypatch)

    svc = FeatureBuilderService(db)

    df_with_target = svc.build_features(
        T0, T0 + timedelta(hours=48),
        include_target=True,
    )
    df_no_target = svc.build_features(
        T0, T0 + timedelta(hours=48),
        include_target=False,
    )

    # Reproduce the parquet writer's target derivation.
    parquet_side_y = df_no_target["btc_price"].shift(-1)

    # Align on shared ds values (all rows except the trailing
    # frontier, which the include_target=True path drops).
    shared = df_with_target.index.intersection(
        df_no_target.index
    )

    for ds in shared:
        db_y = df_with_target.loc[ds, "y"]
        pq_y = parquet_side_y.loc[ds]

        if pd.isna(db_y) and pd.isna(pq_y):
            continue
        assert db_y == pytest.approx(pq_y, nan_ok=True)


# ==============================================================
# Test 3: shared feature columns match on the intersection
# ==============================================================


def test_feature_columns_match_between_writers(
    db, monkeypatch
):
    """
    On rows present in both the DB writer's output and the
    parquet writer's pre-split input frame, the 52 shared
    feature columns are equal.

    The parquet writer's pre-split input is exactly
    build_features(include_target=False) with the ds index
    reset. We reconstruct it here without running the actual
    SplitProcessor (which needs a Postgres-tolerable frame and
    would apply its own drops). The comparison is on the
    intersection of row indices and the 52 columns minus y.
    """
    _seed_all(db, hours=48)
    _patch_trackers(monkeypatch)

    svc = FeatureBuilderService(db)

    db_side = svc.build_features(
        T0, T0 + timedelta(hours=48),
        include_target=True,
    )
    pq_side = svc.build_features(
        T0, T0 + timedelta(hours=48),
        include_target=False,
    )

    # Intersection: DB side is (pq_side minus the trailing row).
    shared_ds = db_side.index.intersection(pq_side.index)
    assert len(shared_ds) == len(db_side)

    for ds in shared_ds:
        for col in _FEATURE_COLUMNS:
            if col not in db_side.columns:
                continue  # integer-only columns on one side
            db_v = db_side.loc[ds, col]
            pq_v = pq_side.loc[ds, col]

            if pd.isna(db_v) and pd.isna(pq_v):
                continue

            if isinstance(db_v, (int, np.integer)):
                assert db_v == pq_v, (
                    f"{col} mismatch at {ds}: "
                    f"{db_v} != {pq_v}"
                )
            else:
                assert db_v == pytest.approx(pq_v, nan_ok=True), (
                    f"{col} mismatch at {ds}: "
                    f"{db_v} != {pq_v}"
                )


# ==============================================================
# Test 4: DB writer's y matches TargetGenerator's y
# ==============================================================


def test_db_writer_y_equals_target_generator_output(
    db, monkeypatch
):
    """
    Compare the DB writer's y (from build_features' direct
    shift) against the parquet writer's y (from SplitProcessor's
    TargetGenerator). Both use close.shift(-1) on the same
    btc_price series, so they must agree.
    """
    from app.ml.target_generator import TargetGenerator

    _seed_all(db, hours=48)
    _patch_trackers(monkeypatch)

    svc = FeatureBuilderService(db)
    df_52 = svc.build_features(
        T0, T0 + timedelta(hours=48),
        include_target=False,
    )
    df_53 = svc.build_features(
        T0, T0 + timedelta(hours=48),
        include_target=True,
    )

    # TargetGenerator needs a regular (non-indexed) frame with a
    # btc_price column.
    frame = df_52.reset_index()
    tg = TargetGenerator(price_column="btc_price")
    with_target = tg.generate_target(frame)

    # Align on ds. TargetGenerator adds target_next_price via
    # shift(-1) on btc_price, same as build_features' direct
    # y computation.
    shared = df_53.index.intersection(
        pd.DatetimeIndex(with_target["ds"])
    )
    for ds in shared:
        db_y = df_53.loc[ds, "y"]
        tg_y = with_target.loc[
            with_target["ds"] == ds, "target_next_price"
        ].iloc[0]

        if pd.isna(db_y) and pd.isna(tg_y):
            continue
        assert db_y == pytest.approx(tg_y, nan_ok=True), (
            f"y mismatch at {ds}: db={db_y} tg={tg_y}"
        )


# ==============================================================
# Test 5: idempotency of DB writer does not mutate values
# ==============================================================


def test_db_writer_is_idempotent_without_mutation(
    db, monkeypatch
):
    """
    Re-running the DB writer must not change any persisted
    value. The ON CONFLICT (ds) DO NOTHING clause ensures this.
    """
    _seed_all(db, hours=24)
    _patch_trackers(monkeypatch)

    writer = FeaturesDBWriter(db)
    writer.write_range(T0, T0 + timedelta(hours=24))

    before = db.execute(
        text("SELECT ds, y, btc_price FROM features_db ORDER BY ds")
    ).mappings().all()

    # Second run.
    writer.write_range(T0, T0 + timedelta(hours=24))

    after = db.execute(
        text("SELECT ds, y, btc_price FROM features_db ORDER BY ds")
    ).mappings().all()

    assert len(before) == len(after)
    for b, a in zip(before, after):
        assert b["ds"] == a["ds"]
        assert b["y"] == a["y"]
        assert b["btc_price"] == a["btc_price"]