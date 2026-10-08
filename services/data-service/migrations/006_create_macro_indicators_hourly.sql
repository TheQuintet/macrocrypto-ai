-- 006_create_macro_indicators_hourly.sql
--
-- Materialized hourly macro table. One row per hour (UTC).
-- Pivots raw macro_indicators (long format) into wide hourly
-- columns, with forward-fill.
--
-- Missingness policy (locked in Chat 3):
--   - Each column is the latest raw macro_indicators observation
--     for the matching indicator_name with time <= hour.
--   - NULL if no such observation exists.
--   - No age limit: a stale value is carried forward.
--     Staleness is tracked downstream in features_db.
--
-- Rename map (raw indicator_name -> hourly column):
--   cpi                 -> cpi
--   federal_funds_rate  -> interest_rate
--   m2_money_supply     -> m2_growth
--   dxy                 -> dxy
--   ten_year_treasury   -> treasury_yield

CREATE TABLE IF NOT EXISTS macro_indicators_hourly (
    time             TIMESTAMPTZ      NOT NULL,
    cpi              DOUBLE PRECISION,
    interest_rate    DOUBLE PRECISION,
    m2_growth        DOUBLE PRECISION,
    dxy              DOUBLE PRECISION,
    treasury_yield   DOUBLE PRECISION,
    created_at       TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (time)
);

CREATE INDEX IF NOT EXISTS idx_macro_indicators_hourly_time_desc
    ON macro_indicators_hourly (time DESC);