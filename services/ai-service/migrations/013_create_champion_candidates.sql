-- ============================================================
-- Migration 013: Create champion_candidates table
-- ============================================================
-- Tracks the top-ranked candidate per (horizon, market_condition)
-- on each day the promotion job runs.
--
-- Why this table exists
-- ------------------------------------------------------------------
-- The stability gate needs to answer: "How many consecutive days
-- has model X been the top candidate for horizon H?" Without a
-- history of daily top candidates, that question cannot be answered
-- cleanly — reading from prediction_performance would require
-- re-ranking every day of the window on every promotion run.
--
-- This table records one row per (candidate_date, horizon,
-- market_condition, model_name) — so the top candidate for each
-- key is written once per day. The stability check is then a simple
-- "how many consecutive candidate_date rows exist for this
-- (horizon, market_condition, model_name)?" query.
--
-- ------------------------------------------------------------------
-- What "candidate" means
-- ------------------------------------------------------------------
-- On each run, the promotion job:
--   1. Ranks eligible models by the configured metric (typically
--      MAE) over the primary lookback window.
--   2. Picks the top-ranked model.
--   3. Writes one row here recording that pick.
--
-- If a model is the top candidate for 3 consecutive days (by
-- default), it becomes eligible for promotion.
--
-- ------------------------------------------------------------------
-- Why the market_condition column
-- ------------------------------------------------------------------
-- Regime-aware selection ranks models per regime in addition to
-- globally. To support the same stability logic for regime-specific
-- champions, we track candidates per (horizon, regime). When
-- regime selection is disabled, only market_condition=NULL rows
-- are written.
--
-- ------------------------------------------------------------------
-- Uniqueness
-- ------------------------------------------------------------------
-- One row per (candidate_date, horizon, model_name, metric_name) —
-- the metric_name is included so a future project could track
-- multiple metrics per candidate without a schema change.
--
-- If the same model is the top candidate on multiple days, multiple
-- rows exist with different candidate_date values. That's the point.
--
-- Owner: AI Service
-- Applied by: app.database.migrations_runner
-- ============================================================

CREATE TABLE IF NOT EXISTS champion_candidates (
    -- Surrogate primary key
    id                    BIGSERIAL       PRIMARY KEY,

    -- The date this candidate was the top pick
    candidate_date        DATE            NOT NULL,

    -- Which horizon this candidate is for
    horizon               VARCHAR(8)      NOT NULL,

    -- Which market regime. NULL = global candidate.
    -- Non-null values: 'bull', 'bear', 'volatile', 'neutral'.
    market_condition      VARCHAR(16),

    -- The top-ranked model for this (date, horizon, regime)
    model_name            VARCHAR(64)     NOT NULL,

    -- The metric and value that made this model the top candidate
    metric_name           VARCHAR(16)     NOT NULL,
    metric_value          DOUBLE PRECISION NOT NULL,

    -- Sample size used to compute metric_value
    sample_size           INTEGER         NOT NULL,

    -- Housekeeping
    created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Uniqueness: one top candidate per (date, horizon, regime, model, metric).
    -- The model_name is in the key because two models cannot be
    -- joint-top on the same day by design; if they tie, one is
    -- picked deterministically and only that row is written.
    CONSTRAINT champion_candidates_unique
        UNIQUE (candidate_date, horizon, model_name, metric_name)
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE champion_candidates
    ADD CONSTRAINT champion_candidates_horizon_valid
    CHECK (horizon IN ('24h', '7d'));

ALTER TABLE champion_candidates
    ADD CONSTRAINT champion_candidates_market_condition_valid
    CHECK (
        market_condition IS NULL
        OR market_condition IN ('bull', 'bear', 'volatile', 'neutral')
    );

ALTER TABLE champion_candidates
    ADD CONSTRAINT champion_candidates_metric_valid
    CHECK (metric_name IN ('mae', 'rmse', 'mape', 'directional_accuracy'));

ALTER TABLE champion_candidates
    ADD CONSTRAINT champion_candidates_sample_size_positive
    CHECK (sample_size > 0);

-- ------------------------------------------------------------
-- Read indexes
-- ------------------------------------------------------------
-- Primary read pattern: stability check. "Give me the consecutive
-- run of candidate_date rows for this (horizon, market_condition,
-- model_name), most recent first."
--
-- We index on (horizon, market_condition, model_name, candidate_date DESC)
-- so the stability query is a simple range scan.
CREATE INDEX IF NOT EXISTS idx_champion_candidates_stability
    ON champion_candidates (
        horizon,
        COALESCE(market_condition, '__global__'),
        model_name,
        candidate_date DESC
    );

-- Secondary read: "show me the top candidate for every (horizon,
-- regime) on the most recent N days" — used by the promotion job
-- to compute streaks efficiently.
CREATE INDEX IF NOT EXISTS idx_champion_candidates_date
    ON champion_candidates (candidate_date DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE champion_candidates IS
    'Daily top-ranked candidate per (horizon, regime) — feeds the stability gate';

COMMENT ON COLUMN champion_candidates.candidate_date IS
    'Date on which this model was the top-ranked candidate';

COMMENT ON COLUMN champion_candidates.horizon IS
    'Horizon label: 24h or 7d';

COMMENT ON COLUMN champion_candidates.market_condition IS
    'Market regime for regime-aware candidates. NULL = global candidate.';

COMMENT ON COLUMN champion_candidates.model_name IS
    'Top-ranked model identifier for this (date, horizon, regime)';

COMMENT ON COLUMN champion_candidates.metric_name IS
    'Metric used to rank candidates (typically "mae")';

COMMENT ON COLUMN champion_candidates.metric_value IS
    'Value of metric_name for this candidate';

COMMENT ON COLUMN champion_candidates.sample_size IS
    'Number of matched points contributing to metric_value';