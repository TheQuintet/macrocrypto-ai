-- 009_create_features_db.sql
--
-- The ML feature table. One row per hour (UTC) containing the
-- 53-column contract v2 feature vector and its target.
--
-- Consumers:
--   - The AI Service reads this via the DB path
--     (fetch_training_frame_from_features_db) after its
--     config defaults point at the hourly tables.
--   - The hourly parquet writer produces a matching 53-column
--     frame written to app/data/processed_v2_builder/ for the
--     parquet path.
--
-- Contract v2 (53 columns):
--     2  ds, y
--     4  raw market & on-chain
--    13  macro & external assets
--    10  technical indicators & ratios
--     4  data-quality flags        (INTEGER, not BOOLEAN — D8)
--    14  observation recency trackers (INTEGER, HOURS, but
--         names keep the _days_since_* suffix — D8)
--     6  engineered features
--    ---
--    53
--
-- Column types: 45 base + 6 engineered = DOUBLE PRECISION;
-- 4 flags + 14 trackers = INTEGER.
--
-- Migration numbering note: 007_promote_hourly_to_hypertables.sql
-- (Chat 3) occupies the 007 slot. 008_create_macro_indicator_vintages.sql
-- (B6) is on a sibling branch. This migration continues the
-- sequence at 009. Migration numbers do not match landing order;
-- the runner sorts by filename.
--
-- Target semantics (D9): y at ds is btc_prices_hourly.close at
-- ds + 1h. The writer lags 1 hour so y is always populated for
-- every persisted row (y is NOT NULL).
--
-- Retention: unlimited. At hourly resolution this is ~8,760 rows
-- per year.
--
-- Idempotent: safe to run on an existing database.

CREATE TABLE IF NOT EXISTS features_db (
    -- Timestamp and target (2)
    ds                                TIMESTAMPTZ      NOT NULL,
    y                                 DOUBLE PRECISION NOT NULL,

    -- Raw market & on-chain (4)
    btc_price                         DOUBLE PRECISION,
    btc_volume                        DOUBLE PRECISION,
    btc_dominance                     DOUBLE PRECISION,
    active_addresses                  DOUBLE PRECISION,

    -- Macro & external assets (13)
    gold_spot                         DOUBLE PRECISION,
    dxy                               DOUBLE PRECISION,
    ten_year_treasury                 DOUBLE PRECISION,
    vix                               DOUBLE PRECISION,
    high_yield_spread                 DOUBLE PRECISION,
    nasdaq_composite                  DOUBLE PRECISION,
    equity_corr                       DOUBLE PRECISION,
    high_yield_credit_stress_proxy    DOUBLE PRECISION,
    cpi                               DOUBLE PRECISION,
    federal_funds_rate                DOUBLE PRECISION,
    gdp                               DOUBLE PRECISION,
    m2_money_supply                   DOUBLE PRECISION,
    unemployment                      DOUBLE PRECISION,

    -- Technical indicators & ratios (10)
    btc_log_return_1d                 DOUBLE PRECISION,
    btc_log_return_7d                 DOUBLE PRECISION,
    btc_log_return_30d                DOUBLE PRECISION,
    btc_sma_7                         DOUBLE PRECISION,
    btc_sma_30                        DOUBLE PRECISION,
    btc_sma_90                        DOUBLE PRECISION,
    btc_volatility_7d                 DOUBLE PRECISION,
    btc_volatility_30d                DOUBLE PRECISION,
    btc_gold_ratio                    DOUBLE PRECISION,
    btc_nasdaq_ratio                  DOUBLE PRECISION,

    -- Data-quality flags (4) — INTEGER, not BOOLEAN
    high_yield_spread_is_missing      INTEGER,
    active_addresses_is_imputed       INTEGER,
    unemployment_is_imputed           INTEGER,
    warmup_complete                   INTEGER,

    -- Observation recency trackers (14) — INTEGER, stored in HOURS,
    -- names keep the _days_since_* suffix (D8)
    btc_dominance_days_since_last_observation                INTEGER,
    gold_spot_days_since_last_observation                    INTEGER,
    dxy_days_since_last_observation                          INTEGER,
    ten_year_treasury_days_since_last_observation            INTEGER,
    vix_days_since_last_observation                          INTEGER,
    nasdaq_composite_days_since_last_observation             INTEGER,
    equity_corr_days_since_last_observation                  INTEGER,
    high_yield_credit_stress_proxy_days_since_last_observation INTEGER,
    active_addresses_days_since_last_observation             INTEGER,
    cpi_days_since_release                                   INTEGER,
    federal_funds_rate_days_since_release                    INTEGER,
    gdp_days_since_release                                   INTEGER,
    m2_money_supply_days_since_release                       INTEGER,
    unemployment_days_since_release                          INTEGER,

    -- Engineered features (6)
    eng_price_lag_1d                  DOUBLE PRECISION,
    eng_price_lag_7d                  DOUBLE PRECISION,
    eng_price_lag_30d                 DOUBLE PRECISION,
    eng_returns_1d                    DOUBLE PRECISION,
    eng_returns_7d                    DOUBLE PRECISION,
    eng_returns_30d                   DOUBLE PRECISION,

    PRIMARY KEY (ds)
);

CREATE INDEX IF NOT EXISTS idx_features_db_ds_desc
    ON features_db (ds DESC);

-- ============================================================
-- HYPERTABLE NOTE
-- ============================================================
--
-- This table is NOT converted to a TimescaleDB hypertable.
-- At ~8,760 rows/year it is small enough that a single
-- partition is fine, and the AI Service's access pattern is
-- "SELECT ... WHERE ds >= now() - N hours ORDER BY ds", which
-- the desc index handles without chunk pruning.
--
-- If the row count grows substantially (e.g. sub-hourly
-- resolution is added later), revisit this decision.

-- ============================================================
-- GOVERNANCE NOTE
-- ============================================================
--
-- The parquet writer runs the training/validation/test split
-- through SplitProcessor, which drops rows with
-- warmup_complete == 0 or NaN active_addresses, and adds a
-- target_next_price column via TargetGenerator. This table
-- does NOT go through that path: it stores every row the
-- feature builder produces, with warmup_complete as a flag
-- the AI Service can filter on later.
--
-- Consequence: the DB writer and the parquet writer have
-- different row sets for the same time range. The D22
-- consistency guarantee is asserted on the INTERSECTION of
-- row indices, not on the full sets. See
-- tests/unit/test_features_db_vs_parquet_consistency.py.

-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'features_db'
ORDER BY ordinal_position;