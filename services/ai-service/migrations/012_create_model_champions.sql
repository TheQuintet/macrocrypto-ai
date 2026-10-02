-- ============================================================
-- Migration 012: Create model_champions table
-- ============================================================
-- Stores the currently-active champion model per (horizon,
-- market_condition). One row per active champion.
--
-- This table is written by the daily promotion job
-- (daily_promote_champion_job) which:
--   1. Ranks candidate models by backtested MAE over a rolling
--      30-day + 90-day window.
--   2. Applies safety gates: minimum sample size, meaningful
--      lead over the current champion, and stability (the
--      challenger must have been the top candidate for N
--      consecutive days).
--   3. Promotes the challenger only when all gates pass.
--
-- The prediction jobs then read from this table to decide which
-- model to load for the current horizon (and optionally for the
-- current market regime).
--
-- ------------------------------------------------------------------
-- Market_condition semantics
-- ------------------------------------------------------------------
-- The market_condition column is NULLABLE:
--
--   NULL       — the global champion for the horizon (no regime
--                split). This is the default mode while
--                champion_enable_regime_selection=false.
--
--   'bull'     — the champion when the current market is in a
--   'bear'       bull / bear / volatile / neutral regime. Used
--   'volatile'   when champion_enable_regime_selection=true.
--   'neutral'
--
-- When regime selection is enabled, the prediction jobs:
--   1. Classify the current market regime via
--      app.prediction.market.classify_market_condition_safe.
--   2. Look up the champion for (horizon, regime).
--   3. Fall back to the global champion (market_condition IS NULL)
--      if no regime-specific champion exists.
--
-- When regime selection is disabled, only global champions
-- (market_condition IS NULL) are written, and the prediction jobs
-- ignore the market_condition column entirely.
--
-- ------------------------------------------------------------------
-- The unique constraint
-- ------------------------------------------------------------------
-- We enforce "one active champion per (horizon, market_condition)"
-- via a partial unique index. A UNIQUE constraint cannot use
-- expressions, and NULL is not equal to itself in Postgres, so we
-- COALESCE the market_condition to a sentinel string.
--
-- This index guarantees at most one row per (horizon, regime,
-- global) at any time. Promotions do not create new rows; they
-- UPDATE the existing row for the affected key.
--
-- Owner: AI Service
-- Applied by: app.database.migrations_runner
-- ============================================================

CREATE TABLE IF NOT EXISTS model_champions (
    -- Surrogate primary key
    id                    BIGSERIAL       PRIMARY KEY,

    -- Which horizon this champion is for
    horizon               VARCHAR(8)      NOT NULL,

    -- Which market regime. NULL = global champion.
    -- Values when non-null: 'bull', 'bear', 'volatile', 'neutral'.
    market_condition      VARCHAR(16),

    -- The champion model
    model_name            VARCHAR(64)     NOT NULL,
    model_version         VARCHAR(64)     NOT NULL,

    -- When the champion was promoted
    promoted_at           TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- The metric and value that justified the promotion
    metric_name           VARCHAR(16)     NOT NULL,
    metric_value          DOUBLE PRECISION NOT NULL,

    -- Sample size and window used to compute metric_value
    sample_size           INTEGER         NOT NULL,
    lookback_days         INTEGER         NOT NULL,

    -- The model that was displaced (NULL for the first champion)
    previous_champion     VARCHAR(64),

    -- Free-form reason for the promotion, for audit
    reason                TEXT,

    -- Housekeeping
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE model_champions
    ADD CONSTRAINT model_champions_horizon_valid
    CHECK (horizon IN ('24h', '7d'));

ALTER TABLE model_champions
    ADD CONSTRAINT model_champions_market_condition_valid
    CHECK (
        market_condition IS NULL
        OR market_condition IN ('bull', 'bear', 'volatile', 'neutral')
    );

ALTER TABLE model_champions
    ADD CONSTRAINT model_champions_metric_valid
    CHECK (metric_name IN ('mae', 'rmse', 'mape', 'directional_accuracy'));

ALTER TABLE model_champions
    ADD CONSTRAINT model_champions_sample_size_positive
    CHECK (sample_size > 0);

ALTER TABLE model_champions
    ADD CONSTRAINT model_champions_lookback_positive
    CHECK (lookback_days > 0);

-- ------------------------------------------------------------
-- Unique index: one champion per (horizon, market_condition)
-- ------------------------------------------------------------
-- We COALESCE market_condition to a sentinel string so that NULL
-- participates in uniqueness (in Postgres, NULL != NULL).
--
-- The result: at most one global champion and at most one
-- regime-specific champion per regime, per horizon.
CREATE UNIQUE INDEX IF NOT EXISTS idx_model_champions_active
    ON model_champions (
        horizon,
        COALESCE(market_condition, '__global__')
    );

-- ------------------------------------------------------------
-- Read indexes
-- ------------------------------------------------------------
-- Common read pattern: "give me the current champion(s) for
-- horizon X" (used by prediction jobs at every cycle).
CREATE INDEX IF NOT EXISTS idx_model_champions_horizon
    ON model_champions (horizon);

-- Audit: "show me promotion history".
CREATE INDEX IF NOT EXISTS idx_model_champions_promoted_at
    ON model_champions (promoted_at DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE model_champions IS
    'Active champion model per (horizon, market_condition) — read by prediction jobs';

COMMENT ON COLUMN model_champions.horizon IS
    'Horizon label: 24h or 7d';

COMMENT ON COLUMN model_champions.market_condition IS
    'Market regime for regime-aware champions. NULL = global champion. '
    'Non-null values: bull, bear, volatile, neutral.';

COMMENT ON COLUMN model_champions.model_name IS
    'Champion model identifier (e.g. prophet_fresh, xgboost_incremental)';

COMMENT ON COLUMN model_champions.model_version IS
    'Version string at promotion time (e.g. semver "1.0.0")';

COMMENT ON COLUMN model_champions.promoted_at IS
    'When this champion was promoted';

COMMENT ON COLUMN model_champions.metric_name IS
    'Metric used to rank candidates during promotion (typically "mae")';

COMMENT ON COLUMN model_champions.metric_value IS
    'Value of metric_name for the champion at promotion time';

COMMENT ON COLUMN model_champions.sample_size IS
    'Number of matched points contributing to metric_value';

COMMENT ON COLUMN model_champions.lookback_days IS
    'Rolling window used to compute metric_value';

COMMENT ON COLUMN model_champions.previous_champion IS
    'The model that was champion before this promotion (NULL for first)';

COMMENT ON COLUMN model_champions.reason IS
    'Human-readable reason for the promotion';