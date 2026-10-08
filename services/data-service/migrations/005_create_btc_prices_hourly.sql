-- 005_create_btc_prices_hourly.sql
--
-- Materialized hourly BTC price table. One row per hour (UTC).
-- Reads from raw btc_prices (ticks), btc_dominance, and
-- macro_indicators (for active_addresses).
--
-- Missingness policy (locked in Chat 3):
--   - close, volume: rows only exist for hours that had >= 1
--     raw tick. Hours with zero ticks are skipped entirely.
--   - volatility: NULL if < 2 ticks in the hour; otherwise
--     std(ddof=1) of log returns of ticks in the hour.
--     NOT annualized.
--   - dominance, active_addresses: latest raw observation with
--     time <= hour; NULL if none exists; no age limit.
--   - price_lag_7d: close at exactly hour - 7 days; NULL if that
--     row doesn't exist.

CREATE TABLE IF NOT EXISTS btc_prices_hourly (
    time              TIMESTAMPTZ      NOT NULL,
    close             DOUBLE PRECISION,
    volume            DOUBLE PRECISION,
    volatility        DOUBLE PRECISION,
    dominance         DOUBLE PRECISION,
    active_addresses  DOUBLE PRECISION,
    price_lag_7d      DOUBLE PRECISION,
    created_at        TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (time)
);

CREATE INDEX IF NOT EXISTS idx_btc_prices_hourly_time_desc
    ON btc_prices_hourly (time DESC);

-- Convert to a TimescaleDB hypertable.
--
-- if_not_exists: safe on existing databases.
-- migrate_data:   moves any pre-existing rows into the hypertable.
--
-- No chunk_time_interval is set; TimescaleDB's default (7 days)
-- is appropriate for hourly-resolution tables (24x the row
-- density of daily tables).

SELECT create_hypertable(
    'btc_prices_hourly',
    'time',
    if_not_exists => TRUE,
    migrate_data => TRUE
);