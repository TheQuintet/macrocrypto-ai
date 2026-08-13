-- Migration: Create macroeconomic regime tables
-- Sprint 4 - A3.1

CREATE TABLE IF NOT EXISTS macro_regimes (
    id SERIAL PRIMARY KEY,
    regime_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    duration_days INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_macro_regime_type
        CHECK (
            regime_type IN (
                'high_inflation',
                'low_inflation',
                'rising_rates',
                'falling_rates',
                'recession',
                'growth'
            )
        )
);

CREATE TABLE IF NOT EXISTS regime_performance (
    id SERIAL PRIMARY KEY,
    regime_id INTEGER NOT NULL,
    avg_return DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    volatility DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    btc_price_start DOUBLE PRECISION,
    btc_price_end DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_regime_performance_regime
        FOREIGN KEY (regime_id)
        REFERENCES macro_regimes(id)
);

CREATE TABLE IF NOT EXISTS current_regime (
    id SERIAL PRIMARY KEY,
    regime_type VARCHAR(50) NOT NULL,
    identified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    CONSTRAINT ck_current_regime_type
        CHECK (
            regime_type IN (
                'high_inflation',
                'low_inflation',
                'rising_rates',
                'falling_rates',
                'recession',
                'growth'
            )
        )
);

CREATE INDEX IF NOT EXISTS ix_macro_regimes_regime_type
    ON macro_regimes (regime_type);

CREATE INDEX IF NOT EXISTS ix_macro_regimes_start_date
    ON macro_regimes (start_date);

CREATE INDEX IF NOT EXISTS ix_macro_regimes_end_date
    ON macro_regimes (end_date);

CREATE INDEX IF NOT EXISTS ix_regime_performance_regime_id
    ON regime_performance (regime_id);