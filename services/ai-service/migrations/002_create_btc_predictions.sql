-- ============================================================
-- Migration 002: Create btc_predictions table (unified, all horizons)
-- ============================================================
-- This is the primary output table of the AI Service. It stores
-- one row per (forecast_timestamp, prediction_time, horizon,
-- model_name, confidence) combination.
--
-- Design notes:
--   - Unified table for all horizons (24h, 7d) and all models
--     (prophet, xgboost, lightgbm) — filter by `horizon` and
--     `model_name` at query time. This avoids N tables per
--     horizon × model combination.
--   - Converted to a TimescaleDB hypertable partitioned on `time`
--     (the forecast timestamp), which is the primary query axis.
--   - Composite primary key includes every dimension needed to
--     deduplicate a prediction batch.
--
-- Owner: AI Service
-- Read by: API Gateway, Alert Service
-- Written by: app.database.repositories.prediction_repository
-- ============================================================

-- ------------------------------------------------------------
-- Table
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS btc_predictions (
    time                TIMESTAMPTZ       NOT NULL,
    prediction_time     TIMESTAMPTZ       NOT NULL,
    horizon             VARCHAR(8)        NOT NULL,
    model_name          VARCHAR(64)       NOT NULL,
    confidence          DOUBLE PRECISION  NOT NULL,
    predicted_price     DOUBLE PRECISION  NOT NULL,
    lower_bound         DOUBLE PRECISION  NOT NULL,
    upper_bound         DOUBLE PRECISION  NOT NULL,
    created_at          TIMESTAMPTZ       NOT NULL DEFAULT NOW(),

    CONSTRAINT btc_predictions_pkey PRIMARY KEY (
        time,
        prediction_time,
        horizon,
        model_name,
        confidence
    ),

    CONSTRAINT btc_predictions_bounds_ordered CHECK (
        lower_bound <= predicted_price
        AND predicted_price <= upper_bound
    ),

    CONSTRAINT btc_predictions_horizon_valid CHECK (
        horizon IN ('24h', '7d')
    ),

    CONSTRAINT btc_predictions_confidence_valid CHECK (
        confidence IN (0.70, 0.85, 0.95)
    )
);

-- ------------------------------------------------------------
-- Convert to a TimescaleDB hypertable (partition on `time`)
-- ------------------------------------------------------------
-- `if_not_exists => TRUE` makes this safe to re-run.
-- `migrate_data => TRUE` moves any pre-existing rows into the
-- hypertable (harmless when the table is new).
SELECT create_hypertable(
    'btc_predictions',
    'time',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
-- Common read pattern: "give me the latest predictions for a
-- given horizon and model" (used by the API in T1.4).
CREATE INDEX IF NOT EXISTS idx_btc_predictions_horizon_model_time
    ON btc_predictions (horizon, model_name, prediction_time DESC);

-- Time-range scans: "give me all predictions for the last N days"
CREATE INDEX IF NOT EXISTS idx_btc_predictions_time_desc
    ON btc_predictions (time DESC);

-- Per-batch queries: "show me all predictions made at time T"
CREATE INDEX IF NOT EXISTS idx_btc_predictions_prediction_time
    ON btc_predictions (prediction_time DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE btc_predictions IS
    'AI Service BTC price predictions (all horizons, all models)';

COMMENT ON COLUMN btc_predictions.time IS
    'Timestamp the prediction is FOR (the forecast time)';
COMMENT ON COLUMN btc_predictions.prediction_time IS
    'Timestamp when the prediction was GENERATED';
COMMENT ON COLUMN btc_predictions.horizon IS
    'Prediction horizon: 24h or 7d';
COMMENT ON COLUMN btc_predictions.model_name IS
    'Model that produced the prediction: prophet, xgboost, lightgbm';
COMMENT ON COLUMN btc_predictions.confidence IS
    'Confidence level for the bounds: 0.70, 0.85, or 0.95';
COMMENT ON COLUMN btc_predictions.predicted_price IS
    'Point forecast for BTC price (USD)';
COMMENT ON COLUMN btc_predictions.lower_bound IS
    'Lower bound at the given confidence level';
COMMENT ON COLUMN btc_predictions.upper_bound IS
    'Upper bound at the given confidence level';