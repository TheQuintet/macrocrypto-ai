-- ============================================================
-- Migration 014: Create CLI mirror tables for champion state
-- ============================================================
-- Adds `_cli` variants of the two champion-state tables so that
-- CLI runs are fully sandboxed:
--
--     model_champions         <-> model_champions_cli
--     champion_candidates     <-> champion_candidates_cli
--
-- When CLI_MODE=true, the promotion job reads and writes these
-- CLI variants instead of the production tables. The prediction
-- jobs in CLI mode also read the CLI champion. Production is
-- untouched.
--
-- This mirrors the pattern used by migrations/011_create_cli_tables.sql
-- for the six data tables. The champion-state tables were not
-- included in migration 011 because at the time we assumed the
-- champion was a single source of truth. On reflection, full CLI
-- isolation requires the champion state to be sandboxed as well.
--
-- ------------------------------------------------------------------
-- Why LIKE ... INCLUDING DEFAULTS INCLUDING CONSTRAINTS (not ALL)
-- ------------------------------------------------------------------
-- PostgreSQL's LIKE ... INCLUDING INDEXES tries to copy indexes
-- with their original names, which collides with the production
-- indexes in the same schema. We instead:
--   1. Copy the table structure (columns, defaults, constraints).
--   2. Recreate indexes explicitly, with `_cli` names.
--
-- We DO need to recreate the partial unique index
-- `idx_model_champions_active` (defined in migration 012) because
-- the CLI table needs the same "one active champion per
-- (horizon, COALESCE(market_condition, '__global__'))" invariant.
-- `LIKE ... INCLUDING ALL` would not have preserved the expression
-- anyway.
--
-- ------------------------------------------------------------------
-- Idempotency
-- ------------------------------------------------------------------
-- Every statement uses IF NOT EXISTS. Re-running is safe.
--
-- Owner: AI Service
-- Applied by: app.database.migrations_runner
-- ============================================================


-- ============================================================
-- model_champions_cli
-- ============================================================
CREATE TABLE IF NOT EXISTS model_champions_cli (
    LIKE model_champions
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

-- ------------------------------------------------------------
-- Unique index: one champion per (horizon, market_condition)
-- ------------------------------------------------------------
-- Same invariant as the production table. COALESCE makes NULL
-- participate in uniqueness (in Postgres, NULL != NULL), so
-- at most one global champion per horizon.
CREATE UNIQUE INDEX IF NOT EXISTS idx_model_champions_cli_active
    ON model_champions_cli (
        horizon,
        COALESCE(market_condition, '__global__')
    );

-- ------------------------------------------------------------
-- Read indexes
-- ------------------------------------------------------------
-- The common read pattern: prediction jobs query the champion
-- for a given horizon.
CREATE INDEX IF NOT EXISTS idx_model_champions_cli_horizon
    ON model_champions_cli (horizon);

-- Audit: promotion history.
CREATE INDEX IF NOT EXISTS idx_model_champions_cli_promoted_at
    ON model_champions_cli (promoted_at DESC);

COMMENT ON TABLE model_champions_cli IS
    'CLI-mode mirror of model_champions — populated by app.cli.pipeline only';


-- ============================================================
-- champion_candidates_cli
-- ============================================================
CREATE TABLE IF NOT EXISTS champion_candidates_cli (
    LIKE champion_candidates
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

-- ------------------------------------------------------------
-- Stability-check index
-- ------------------------------------------------------------
-- Same shape as the production index. Used by the CLI promotion
-- job to answer "how many consecutive days has model X been the
-- top candidate?"
CREATE INDEX IF NOT EXISTS idx_champion_candidates_cli_stability
    ON champion_candidates_cli (
        horizon,
        COALESCE(market_condition, '__global__'),
        model_name,
        candidate_date DESC
    );

-- Secondary read: "show me the most recent candidates across
-- (horizon, regime)".
CREATE INDEX IF NOT EXISTS idx_champion_candidates_cli_date
    ON champion_candidates_cli (candidate_date DESC);

COMMENT ON TABLE champion_candidates_cli IS
    'CLI-mode mirror of champion_candidates — populated by app.cli.pipeline only';


-- ============================================================
-- End of migration 014
-- ============================================================