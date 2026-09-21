-- ============================================================
-- Migration 007: Create model_performance table
-- ============================================================
-- Stores one aggregate row per (model_name, horizon, calculated_at).
-- Unlike prediction_performance (one row per evaluated point),
-- this table stores one row per aggregation run, making long-term
-- trend queries cheap and eliminating the need to re-aggregate on
-- every read.
--
-- Populated by a dedicated job (a later branch); M8 reads from it
-- for the multi-model performance API.
--
-- Design notes:
--   - calculated_at is the timestamp of the aggregation run, not
--     the forecast timestamp. Different runs of the same model
--     over the same window produce different rows.
--   - sample_size is the number of evaluated points that
--     contributed to the aggregate. It is stored explicitly
--     because it is needed for downstream confidence-weighting
--     and is not always derivable from the aggregate metrics.
--   - All metric columns are nullable because not every run
--     produces every metric (e.g. directional_accuracy requires
--     direction ground truth, which is not always available).
--   - CHECK constraints enforce that horizon is a known value
--     and that metric magnitudes are non-negative.
--
-- Owner: AI Service
-- ============================================================

CREATE TABLE IF NOT EXISTS model_performance (
    id                      BIGSERIAL       PRIMARY KEY,

    -- Which model-horizon the aggregate is for
    model_name              VARCHAR(64)     NOT NULL,
    horizon                 VARCHAR(8)      NOT NULL,

    -- Aggregate metrics (nullable — see design notes)
    mae                     DOUBLE PRECISION,
    rmse                    DOUBLE PRECISION,
    mape                    DOUBLE PRECISION,
    directional_accuracy    DOUBLE PRECISION,

    -- Number of evaluated points that contributed to this aggregate
    sample_size             INT             NOT NULL,

    -- When the aggregation was computed (the timestamp of the run)
    calculated_at           TIMESTAMPTZ     NOT NULL,

    -- Housekeeping
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE model_performance
    ADD CONSTRAINT model_performance_horizon_valid
    CHECK (horizon IN ('24h', '7d'));

ALTER TABLE model_performance
    ADD CONSTRAINT model_performance_mae_non_negative
    CHECK (mae IS NULL OR mae >= 0);

ALTER TABLE model_performance
    ADD CONSTRAINT model_performance_rmse_non_negative
    CHECK (rmse IS NULL OR rmse >= 0);

ALTER TABLE model_performance
    ADD CONSTRAINT model_performance_mape_non_negative
    CHECK (mape IS NULL OR mape >= 0);

ALTER TABLE model_performance
    ADD CONSTRAINT model_performance_directional_accuracy_range
    CHECK (
        directional_accuracy IS NULL
        OR (directional_accuracy >= 0 AND directional_accuracy <= 100)
    );

ALTER TABLE model_performance
    ADD CONSTRAINT model_performance_sample_size_positive
    CHECK (sample_size > 0);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
-- Single-column indexes for ad-hoc filters
CREATE INDEX IF NOT EXISTS idx_model_performance_model_name
    ON model_performance (model_name);

CREATE INDEX IF NOT EXISTS idx_model_performance_horizon
    ON model_performance (horizon);

CREATE INDEX IF NOT EXISTS idx_model_performance_calculated_at
    ON model_performance (calculated_at DESC);

-- Composite index for the primary read pattern:
-- "latest N rows for this (model, horizon)"
CREATE INDEX IF NOT EXISTS idx_model_performance_model_horizon_calc
    ON model_performance (model_name, horizon, calculated_at DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE model_performance IS
    'Aggregate performance metrics per (model_name, horizon, calculated_at) — M7';
COMMENT ON COLUMN model_performance.model_name IS
    'Model identifier (e.g. prophet_fresh, xgboost_incremental)';
COMMENT ON COLUMN model_performance.horizon IS
    '24h or 7d';
COMMENT ON COLUMN model_performance.mae IS
    'Mean Absolute Error in USD';
COMMENT ON COLUMN model_performance.rmse IS
    'Root Mean Square Error in USD';
COMMENT ON COLUMN model_performance.mape IS
    'Mean Absolute Percentage Error in percent';
COMMENT ON COLUMN model_performance.directional_accuracy IS
    'Percentage of correct direction predictions (0-100)';
COMMENT ON COLUMN model_performance.sample_size IS
    'Number of evaluated points contributing to this aggregate';
COMMENT ON COLUMN model_performance.calculated_at IS
    'When the aggregation was computed (UTC)';
COMMENT ON COLUMN model_performance.created_at IS
    'Row insertion timestamp (UTC)';