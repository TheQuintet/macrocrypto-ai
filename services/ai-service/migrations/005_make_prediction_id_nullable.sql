-- ============================================================
-- Migration 005: Make prediction_id nullable
-- ============================================================
-- T5.2's walk-forward backtesting writes "hypothetical"
-- evaluation rows — predictions that were never stored in
-- btc_predictions because they were produced and immediately
-- compared during the backtest.
--
-- These rows cannot reference a real prediction, so
-- prediction_id must allow NULL for backtest rows. Production
-- evaluation rows (T5.x future) still set it.
--
-- The FK constraint remains active — it simply does not apply
-- when prediction_id IS NULL.
--
-- Owner: AI Service
-- ============================================================

ALTER TABLE prediction_performance
    ALTER COLUMN prediction_id DROP NOT NULL;

COMMENT ON COLUMN prediction_performance.prediction_id IS
    'FK to btc_predictions.id. NULL for backtest rows produced '
    'during walk-forward evaluation (T5.2).';