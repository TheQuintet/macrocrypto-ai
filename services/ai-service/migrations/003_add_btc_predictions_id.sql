-- ============================================================
-- Migration 003: Add surrogate id to btc_predictions
-- ============================================================
-- The prediction_performance table (migration 004) needs a
-- single-column identifier to reference each prediction row.
-- btc_predictions uses a composite primary key
-- (time, prediction_time, horizon, model_name, confidence),
-- which is awkward for foreign keys.
--
-- This migration adds a surrogate `id BIGSERIAL` column with a
-- UNIQUE constraint. Existing rows get populated automatically
-- by PostgreSQL on the ADD COLUMN step.
--
-- Owner: AI Service
-- ============================================================

-- Add the surrogate id column (existing rows auto-populate)
ALTER TABLE btc_predictions
    ADD COLUMN IF NOT EXISTS id BIGSERIAL;

-- Enforce uniqueness. IF NOT EXISTS is not supported for ADD
-- CONSTRAINT, so we guard with a DO block.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'btc_predictions_id_key'
    ) THEN
        ALTER TABLE btc_predictions
            ADD CONSTRAINT btc_predictions_id_key UNIQUE (id);
    END IF;
END $$;

-- Index for foreign-key lookups from prediction_performance
CREATE INDEX IF NOT EXISTS idx_btc_predictions_id
    ON btc_predictions (id);

COMMENT ON COLUMN btc_predictions.id IS
    'Surrogate identifier added in migration 003 for FK references.';