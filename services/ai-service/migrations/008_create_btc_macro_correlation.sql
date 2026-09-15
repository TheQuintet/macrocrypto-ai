-- ============================================================
-- Migration 008: Create btc_macro_correlation table
-- ============================================================
-- Stores one row per (indicator_name, window_days, calculated_at).
-- Each row captures the Pearson correlation between BTC price and
-- one macroeconomic indicator over a rolling window at a specific
-- point in time.
--
-- This table is the storage layer for A1 (correlation analysis).
-- A1.2 populates it with rows; A1.3 derives the strength and
-- direction labels; A1.4 computes the p-value and significance;
-- A1.6 exposes it via an API endpoint.
--
-- Design notes:
--   - The composite primary key is
--     (indicator_name, window_days, calculated_at). All three
--     business columns are required for uniqueness, so no
--     surrogate id is needed.
--   - indicator_name is a product-facing label, not the raw
--     source column name. A1.2 maps source columns (cpi,
--     interest_rate, ...) to these labels.
--   - correlation_coefficient is stored as a plain float and
--     CHECK-constrained to [-1, 1].
--   - strength and direction are derived labels, stored on the
--     row so queries don't need to recompute thresholds. The
--     mapping is fixed by A1.3:
--       strength: strong (>0.7), medium (0.3-0.7), weak (<0.3)
--                 (applied to |coefficient|)
--       direction: positive (>=0), negative (<0)
--   - p_value is nullable because A1.4 is a separate ticket.
--     A1.2 can write rows before significance is computed.
--   - calculated_at is the timestamp of the calculation run,
--     matching model_performance's semantics.
--
-- Owner: AI Service
-- ============================================================

CREATE TABLE IF NOT EXISTS btc_macro_correlation (
    indicator_name              VARCHAR(32)     NOT NULL,
    window_days                 INT             NOT NULL,
    calculated_at               TIMESTAMPTZ     NOT NULL,

    correlation_coefficient     DOUBLE PRECISION NOT NULL,
    strength                    VARCHAR(16)     NOT NULL,
    direction                   VARCHAR(16)     NOT NULL,
    p_value                     DOUBLE PRECISION,

    created_at                  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    PRIMARY KEY (indicator_name, window_days, calculated_at)
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE btc_macro_correlation
    ADD CONSTRAINT btc_macro_correlation_indicator_valid
    CHECK (
        indicator_name IN (
            'inflation', 'rates', 'gdp', 'unemployment'
        )
    );

ALTER TABLE btc_macro_correlation
    ADD CONSTRAINT btc_macro_correlation_window_valid
    CHECK (window_days IN (30, 90, 365));

ALTER TABLE btc_macro_correlation
    ADD CONSTRAINT btc_macro_correlation_coefficient_range
    CHECK (
        correlation_coefficient >= -1.0
        AND correlation_coefficient <= 1.0
    );

ALTER TABLE btc_macro_correlation
    ADD CONSTRAINT btc_macro_correlation_strength_valid
    CHECK (strength IN ('strong', 'medium', 'weak'));

ALTER TABLE btc_macro_correlation
    ADD CONSTRAINT btc_macro_correlation_direction_valid
    CHECK (direction IN ('positive', 'negative'));

ALTER TABLE btc_macro_correlation
    ADD CONSTRAINT btc_macro_correlation_p_value_range
    CHECK (
        p_value IS NULL
        OR (p_value >= 0.0 AND p_value <= 1.0)
    );

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
-- Single-column indexes for the three most common filter columns
CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_indicator_name
    ON btc_macro_correlation (indicator_name);

CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_window_days
    ON btc_macro_correlation (window_days);

CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_calculated_at
    ON btc_macro_correlation (calculated_at DESC);

-- Composite index for the primary read pattern:
-- "latest N rows for this (indicator, window)"
CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_indicator_window_calc
    ON btc_macro_correlation (indicator_name, window_days, calculated_at DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE btc_macro_correlation IS
    'BTC-vs-macroeconomic correlation metrics per (indicator, window, run) — A1.1';
COMMENT ON COLUMN btc_macro_correlation.indicator_name IS
    'Product-facing indicator label: inflation, rates, gdp, unemployment';
COMMENT ON COLUMN btc_macro_correlation.window_days IS
    'Rolling window length in days: 30, 90, or 365';
COMMENT ON COLUMN btc_macro_correlation.calculated_at IS
    'When the correlation was computed (UTC)';
COMMENT ON COLUMN btc_macro_correlation.correlation_coefficient IS
    'Pearson correlation coefficient in [-1, 1]';
COMMENT ON COLUMN btc_macro_correlation.strength IS
    'Derived strength label (A1.3): strong, medium, weak';
COMMENT ON COLUMN btc_macro_correlation.direction IS
    'Derived direction label (A1.3): positive, negative';
COMMENT ON COLUMN btc_macro_correlation.p_value IS
    'Two-tailed p-value for the correlation (A1.4). NULL until computed.';
COMMENT ON COLUMN btc_macro_correlation.created_at IS
    'Row insertion timestamp (UTC)';