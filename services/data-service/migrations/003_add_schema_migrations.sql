-- 003_add_schema_migrations.sql
--
-- Bootstrap the migration tracking table. The runner reads this
-- to know which migrations have been applied. Must exist before
-- any other migration runs, so the runner creates it first.
--
-- Idempotent: safe to run on an existing database.

CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT        PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_schema_migrations_applied_at
    ON schema_migrations (applied_at);