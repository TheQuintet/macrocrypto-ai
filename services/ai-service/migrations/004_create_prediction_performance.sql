-- -- ============================================================
-- -- Migration 004: Create prediction_performance table
-- -- ============================================================
-- -- Stores one row per evaluated prediction point: the pairing of
-- -- a predicted price with the actual price observed at the same
-- -- forecast time.
-- --
-- -- Rolling error metrics (mae, rmse, mape) are NULLABLE — they
-- -- are populated by T5.2's walk-forward backtesting job.
-- --
-- -- market_condition is populated by T5.3's classification logic.
-- --
-- -- Design notes:
-- --   - prediction_id is a FK to btc_predictions.id (added in
-- --     migration 003).
-- --   - horizon and model_name are denormalized from btc_predictions
-- --     for query performance — the most common filters (T5.5
-- --     endpoint) should not require a join.
-- --   - CHECK constraints enforce:
-- --       * market_condition in a known set (or NULL)
-- --       * mae, rmse, mape >= 0 (or NULL)
-- --       * actual_price > 0, predicted_price > 0
-- --
-- -- Owner: AI Service
-- -- Read by: API Gateway (T5.5)
-- -- Written by: T5.2's backtesting pipeline
-- -- ============================================================

CREATE TABLE IF NOT EXISTS prediction_performance (
    id                  BIGSERIAL       PRIMARY KEY,

    -- Reference to the prediction being evaluated
    prediction_id       BIGINT          NOT NULL,
    forecast_date       TIMESTAMPTZ     NOT NULL,

    -- Composite foreign key constraint matching btc_predictions (id, time)
    CONSTRAINT fk_prediction_performance_prediction
        FOREIGN KEY (prediction_id, forecast_date)
        REFERENCES btc_predictions(id, time)
        ON DELETE CASCADE,

    -- Denormalized from btc_predictions for query performance
    horizon             VARCHAR(8)      NOT NULL,
    model_name          VARCHAR(64)     NOT NULL,
    model_version       VARCHAR(64)     NOT NULL,

    -- The evaluation
    predicted_price     DOUBLE PRECISION NOT NULL,
    actual_price        DOUBLE PRECISION NOT NULL,

    -- Rolling metrics (nullable; populated by T5.2)
    mae                 DOUBLE PRECISION,
    rmse                DOUBLE PRECISION,
    mape                DOUBLE PRECISION,

    -- Classification (nullable; populated by T5.3)
    market_condition    VARCHAR(16),

    -- Housekeeping
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE prediction_performance
    ADD CONSTRAINT prediction_performance_market_condition_valid
    CHECK (
        market_condition IS NULL
        OR market_condition IN ('bull', 'bear', 'volatile', 'neutral')
    );

ALTER TABLE prediction_performance
    ADD CONSTRAINT prediction_performance_mae_non_negative
    CHECK (mae IS NULL OR mae >= 0);

ALTER TABLE prediction_performance
    ADD CONSTRAINT prediction_performance_rmse_non_negative
    CHECK (rmse IS NULL OR rmse >= 0);

ALTER TABLE prediction_performance
    ADD CONSTRAINT prediction_performance_mape_non_negative
    CHECK (mape IS NULL OR mape >= 0);

ALTER TABLE prediction_performance
    ADD CONSTRAINT prediction_performance_prices_positive
    CHECK (actual_price > 0 AND predicted_price > 0);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_prediction_performance_horizon_model_date
    ON prediction_performance (horizon, model_name, forecast_date DESC);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_forecast_date
    ON prediction_performance (forecast_date DESC);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_prediction_id
    ON prediction_performance (prediction_id);

CREATE INDEX IF NOT EXISTS idx_prediction_performance_market_condition
    ON prediction_performance (market_condition)
    WHERE market_condition IS NOT NULL;

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE prediction_performance IS
    'Per-point evaluation metrics for stored predictions (T5.1+)';
COMMENT ON COLUMN prediction_performance.prediction_id IS
    'FK component to btc_predictions.id';
COMMENT ON COLUMN prediction_performance.forecast_date IS
    'Timestamp the prediction was FOR / FK component to btc_predictions.time';
COMMENT ON COLUMN prediction_performance.predicted_price IS
    'Predicted BTC price at evaluation time (USD)';
COMMENT ON COLUMN prediction_performance.actual_price IS
    'Observed BTC price at forecast_date (USD)';
COMMENT ON COLUMN prediction_performance.mae IS
    'Rolling MAE in USD (populated by T5.2)';
COMMENT ON COLUMN prediction_performance.rmse IS
    'Rolling RMSE in USD (populated by T5.2)';
COMMENT ON COLUMN prediction_performance.mape IS
    'Rolling MAPE in percent (populated by T5.2)';
COMMENT ON COLUMN prediction_performance.market_condition IS
    'Market classification: bull, bear, volatile, neutral (populated by T5.3)';
COMMENT ON COLUMN prediction_performance.model_version IS
    'Model version string (e.g. semver "1.0.0")';
