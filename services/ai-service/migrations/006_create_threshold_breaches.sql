-- ============================================================
-- Migration 006: Create threshold_breaches table
-- ============================================================
-- Stores one row per (horizon, model_name, metric) that breached
-- its configured threshold during a daily accuracy check.
--
-- This table feeds T5.6's escalation logic (3-day streak rule)
-- and provides an audit trail of when the model started to
-- degrade.
--
-- Design notes:
--   - One row per metric breach, not per evaluation.
--     If MAE, RMSE, and MAPE all breach on the same day for the
--     same (horizon, model), we store 3 rows.
--   - consecutive_days is a simple counter that the daily job
--     computes on write. T5.6 will read it and escalate when
--     it reaches the configured threshold.
--   - value is the actual metric value (in the same unit as
--     threshold — see metric_unit below).
--   - CHECK constraints enforce that metric and metric_unit are
--     from known sets.
--
-- Owner: AI Service
-- ============================================================

CREATE TABLE IF NOT EXISTS threshold_breaches (
    id                  BIGSERIAL       PRIMARY KEY,

    -- When the daily check ran
    detected_at         TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Which model-horizon the breach belongs to
    horizon             VARCHAR(8)      NOT NULL,
    model_name          VARCHAR(64)     NOT NULL,

    -- Which metric breached
    metric              VARCHAR(32)     NOT NULL,
    metric_unit         VARCHAR(16)     NOT NULL,

    -- The actual value and the configured threshold
    value               DOUBLE PRECISION NOT NULL,
    threshold           DOUBLE PRECISION NOT NULL,

    -- Direction of the breach:
    --   'above' — for MAE, RMSE, MAPE (higher is worse)
    --   'below' — for directional accuracy (lower is worse)
    breach_direction    VARCHAR(8)      NOT NULL,

    -- Number of consecutive days this metric has been breaching.
    -- Populated by the daily job (T5.4); T5.6 will read it.
    consecutive_days    INT             NOT NULL DEFAULT 1,

    -- Optional context
    model_version       VARCHAR(64),
    notes               TEXT
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE threshold_breaches
    ADD CONSTRAINT threshold_breaches_horizon_valid
    CHECK (horizon IN ('24h', '7d'));

ALTER TABLE threshold_breaches
    ADD CONSTRAINT threshold_breaches_metric_valid
    CHECK (
        metric IN ('mae_pct', 'rmse_pct', 'mape', 'directional_accuracy')
    );

ALTER TABLE threshold_breaches
    ADD CONSTRAINT threshold_breaches_direction_valid
    CHECK (breach_direction IN ('above', 'below'));

ALTER TABLE threshold_breaches
    ADD CONSTRAINT threshold_breaches_consecutive_positive
    CHECK (consecutive_days >= 1);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
-- Common query: latest breaches for a (horizon, model)
CREATE INDEX IF NOT EXISTS idx_threshold_breaches_horizon_model_date
    ON threshold_breaches (horizon, model_name, detected_at DESC);

-- Time-range scans: all breaches in the last N days
CREATE INDEX IF NOT EXISTS idx_threshold_breaches_detected_at
    ON threshold_breaches (detected_at DESC);

-- Streak lookup for T5.6: recent breaches of a specific metric
CREATE INDEX IF NOT EXISTS idx_threshold_breaches_metric_date
    ON threshold_breaches (horizon, model_name, metric, detected_at DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE threshold_breaches IS
    'Threshold breach history for model performance monitoring (T5.4+)';
COMMENT ON COLUMN threshold_breaches.metric IS
    'mae_pct, rmse_pct, mape, or directional_accuracy';
COMMENT ON COLUMN threshold_breaches.metric_unit IS
    'Unit of the value/threshold: "percent" or "usd"';
COMMENT ON COLUMN threshold_breaches.breach_direction IS
    '"above" for error metrics (higher is worse), '
    '"below" for directional accuracy (lower is worse)';
COMMENT ON COLUMN threshold_breaches.consecutive_days IS
    'How many consecutive daily checks have breached this threshold';