-- ============================================================
-- Migration 001: Create schema_migrations bookkeeping table
-- ============================================================
-- This table tracks which migrations have been applied by the
-- AI Service's migration runner. It is created first (idempotent)
-- so subsequent migrations can be recorded reliably.
--
-- Owner: AI Service
-- Applied by: app.database.migrations_runner
-- ============================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     VARCHAR(255) PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE schema_migrations IS
    'Tracks applied schema migrations for the AI Service';