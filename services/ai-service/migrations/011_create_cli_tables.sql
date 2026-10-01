-- ============================================================
-- Migration 011: Create CLI mirror tables
-- ============================================================
-- The manual CLI (app.cli.pipeline) runs the full ML + analytics
-- flow on demand, sandboxed away from production data. When
-- CLI_MODE=true, the AI Service writes to these `_cli` tables
-- instead of the production tables.
--
-- Each `_cli` table mirrors its production counterpart exactly:
-- same columns, same NOT NULL / DEFAULT / CHECK constraints.
-- Indexes are recreated with `_cli`-suffixed names so they can
-- coexist with the production indexes in the same schema.
--
-- Covered tables (6):
--   - btc_predictions         -> btc_predictions_cli
--   - prediction_performance  -> prediction_performance_cli
--   - threshold_breaches      -> threshold_breaches_cli
--   - model_performance       -> model_performance_cli
--   - btc_macro_correlation   -> btc_macro_correlation_cli
--   - historical_event_impacts-> historical_event_impacts_cli
--
-- Source tables (btc_prices, macro_indicators, features_db) are
-- NOT mirrored — they are shared, read-only inputs.
--
-- Owner: AI Service
-- Applied by: app.database.migrations_runner
-- ============================================================


-- ============================================================
-- btc_predictions_cli
-- ============================================================
-- Mirror of btc_predictions. Holds CLI-generated prediction
-- batches. Composite PK (time, prediction_time, horizon,
-- model_name, confidence), same as the production table.
--
-- We do NOT copy indexes with `LIKE ... INCLUDING INDEXES` because
-- index names would collide. Indexes are created explicitly below.
CREATE TABLE IF NOT EXISTS btc_predictions_cli (
    LIKE btc_predictions
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

-- Recreate production indexes with `_cli` suffix.
-- The production table has:
--   idx_btc_predictions_horizon_model_time
-- plus indexes defined only in migrations (prediction_time,
-- time desc, id). Since we don't have visibility into those, we
-- recreate the two most important patterns:
CREATE INDEX IF NOT EXISTS idx_btc_predictions_cli_horizon_model_time
    ON btc_predictions_cli (horizon, model_name, prediction_time DESC);

CREATE INDEX IF NOT EXISTS idx_btc_predictions_cli_time_desc
    ON btc_predictions_cli (time DESC);

CREATE INDEX IF NOT EXISTS idx_btc_predictions_cli_prediction_time
    ON btc_predictions_cli (prediction_time DESC);

COMMENT ON TABLE btc_predictions_cli IS
    'CLI-mode mirror of btc_predictions — populated by app.cli.pipeline only';


-- ============================================================
-- prediction_performance_cli
-- ============================================================
-- Mirror of prediction_performance. Holds CLI-generated
-- backtest evaluation rows. Same nullable prediction_id
-- semantics as the production table (migration 005).
CREATE TABLE IF NOT EXISTS prediction_performance_cli (
    LIKE prediction_performance
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_cli_horizon_model_date
    ON prediction_performance_cli (horizon, model_name, forecast_date DESC);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_cli_forecast_date
    ON prediction_performance_cli (forecast_date DESC);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_cli_prediction_id
    ON prediction_performance_cli (prediction_id);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_cli_market_condition
    ON prediction_performance_cli (market_condition)
    WHERE market_condition IS NOT NULL;

COMMENT ON TABLE prediction_performance_cli IS
    'CLI-mode mirror of prediction_performance — populated by app.cli.pipeline only';


-- ============================================================
-- threshold_breaches_cli
-- ============================================================
-- Mirror of threshold_breaches. Holds CLI-generated accuracy
-- check breach records.
CREATE TABLE IF NOT EXISTS threshold_breaches_cli (
    LIKE threshold_breaches
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

CREATE INDEX IF NOT EXISTS idx_threshold_breaches_cli_horizon_model_date
    ON threshold_breaches_cli (horizon, model_name, detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_threshold_breaches_cli_detected_at
    ON threshold_breaches_cli (detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_threshold_breaches_cli_metric_date
    ON threshold_breaches_cli (horizon, model_name, metric, detected_at DESC);

COMMENT ON TABLE threshold_breaches_cli IS
    'CLI-mode mirror of threshold_breaches — populated by app.cli.pipeline only';


-- ============================================================
-- model_performance_cli
-- ============================================================
-- Mirror of model_performance. Holds CLI-generated aggregate
-- performance rows.
CREATE TABLE IF NOT EXISTS model_performance_cli (
    LIKE model_performance
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

CREATE INDEX IF NOT EXISTS idx_model_performance_cli_model_name
    ON model_performance_cli (model_name);

CREATE INDEX IF NOT EXISTS idx_model_performance_cli_horizon
    ON model_performance_cli (horizon);

CREATE INDEX IF NOT EXISTS idx_model_performance_cli_calculated_at
    ON model_performance_cli (calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_performance_cli_model_horizon_calc
    ON model_performance_cli (model_name, horizon, calculated_at DESC);

COMMENT ON TABLE model_performance_cli IS
    'CLI-mode mirror of model_performance — populated by app.cli.pipeline only';


-- ============================================================
-- btc_macro_correlation_cli
-- ============================================================
-- Mirror of btc_macro_correlation. Holds CLI-computed
-- correlations. Composite PK (indicator_name, window_days,
-- calculated_at).
CREATE TABLE IF NOT EXISTS btc_macro_correlation_cli (
    LIKE btc_macro_correlation
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_cli_indicator_name
    ON btc_macro_correlation_cli (indicator_name);

CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_cli_window_days
    ON btc_macro_correlation_cli (window_days);

CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_cli_calculated_at
    ON btc_macro_correlation_cli (calculated_at DESC);

CREATE INDEX IF NOT EXISTS idx_btc_macro_correlation_cli_indicator_window_calc
    ON btc_macro_correlation_cli (indicator_name, window_days, calculated_at DESC);

COMMENT ON TABLE btc_macro_correlation_cli IS
    'CLI-mode mirror of btc_macro_correlation — populated by app.cli.pipeline only';


-- ============================================================
-- historical_event_impacts_cli
-- ============================================================
-- Mirror of historical_event_impacts. Holds CLI-recomputed
-- event reactions. The UNIQUE (event_name, event_date)
-- constraint is preserved by INCLUDING CONSTRAINTS — this
-- keeps the delete-then-insert idempotency semantics intact.
CREATE TABLE IF NOT EXISTS historical_event_impacts_cli (
    LIKE historical_event_impacts
    INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS
);

CREATE INDEX IF NOT EXISTS idx_historical_event_impacts_cli_event_name
    ON historical_event_impacts_cli (event_name);

CREATE INDEX IF NOT EXISTS idx_historical_event_impacts_cli_event_date
    ON historical_event_impacts_cli (event_date DESC);

COMMENT ON TABLE historical_event_impacts_cli IS
    'CLI-mode mirror of historical_event_impacts — populated by app.cli.pipeline only';


-- ============================================================
-- Grants (if applicable)
-- ============================================================
-- If your Postgres user is not the table owner, and you have a
-- dedicated `ai_service` role, grant it access. Replace the role
-- name to match your setup. This is a no-op if the roles don't
-- exist.
--
-- DO $$
-- BEGIN
--     IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ai_service') THEN
--         GRANT SELECT, INSERT, UPDATE, DELETE
--             ON btc_predictions_cli, prediction_performance_cli,
--                threshold_breaches_cli, model_performance_cli,
--                btc_macro_correlation_cli, historical_event_impacts_cli
--             TO ai_service;
--     END IF;
-- END $$;


-- ============================================================
-- End of migration 011
-- ============================================================