-- -- Migration: Create macroeconomic regime tables
-- -- Sprint 4 - A3.1

-- CREATE TABLE IF NOT EXISTS macro_regimes (
--     id SERIAL PRIMARY KEY,
--     regime_type VARCHAR(50) NOT NULL,
--     start_date DATE NOT NULL,
--     end_date DATE,
--     duration_days INTEGER,
--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     CONSTRAINT ck_macro_regime_type
--         CHECK (
--             regime_type IN (
--                 'high_inflation',
--                 'low_inflation',
--                 'rising_rates',
--                 'falling_rates',
--                 'recession',
--                 'growth'
--             )
--         )
-- );

-- CREATE TABLE IF NOT EXISTS regime_performance (
--     id SERIAL PRIMARY KEY,
--     regime_id INTEGER NOT NULL,
--     avg_return DOUBLE PRECISION,
--     max_drawdown DOUBLE PRECISION,
--     volatility DOUBLE PRECISION,
--     sharpe_ratio DOUBLE PRECISION,
--     btc_price_start DOUBLE PRECISION,
--     btc_price_end DOUBLE PRECISION,
--     created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

--     CONSTRAINT fk_regime_performance_regime
--         FOREIGN KEY (regime_id)
--         REFERENCES macro_regimes(id)
-- );

-- CREATE TABLE IF NOT EXISTS current_regime (
--     id SERIAL PRIMARY KEY,
--     regime_type VARCHAR(50) NOT NULL,
--     identified_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
--     expires_at TIMESTAMPTZ,

--     CONSTRAINT ck_current_regime_type
--         CHECK (
--             regime_type IN (
--                 'high_inflation',
--                 'low_inflation',
--                 'rising_rates',
--                 'falling_rates',
--                 'recession',
--                 'growth'
--             )
--         )
-- );

-- CREATE INDEX IF NOT EXISTS ix_macro_regimes_regime_type
--     ON macro_regimes (regime_type);

-- CREATE INDEX IF NOT EXISTS ix_macro_regimes_start_date
--     ON macro_regimes (start_date);

-- CREATE INDEX IF NOT EXISTS ix_macro_regimes_end_date
--     ON macro_regimes (end_date);

-- CREATE INDEX IF NOT EXISTS ix_regime_performance_regime_id
--     ON regime_performance (regime_id);


--------------------------------------------------------------------------------------------
-- ============================================================
-- Migration: Macroeconomic Regime Tables
-- Sprint 4 - A3.1 + A3.4
--
-- A3.1:
--   - Macro regime periods
--   - BTC performance by regime
--   - Current regime
--
-- A3.4:
--   - Current regime confidence (%)
--   - Current regime visual indicator
-- ============================================================


-- ============================================================
-- MACRO REGIMES
-- ============================================================

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


-- ============================================================
-- REGIME PERFORMANCE
-- ============================================================

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


-- ============================================================
-- CURRENT REGIME
-- ============================================================

CREATE TABLE IF NOT EXISTS current_regime (
    id SERIAL PRIMARY KEY,

    regime_type VARCHAR(50) NOT NULL,

    -- Classification confidence expressed as percentage.
    -- Valid range: 0-100.
    confidence DOUBLE PRECISION NOT NULL,

    -- Presentation-level market indicator.
    -- Valid values: bull, bear, recession.
    visual_indicator VARCHAR(20) NOT NULL,

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
        ),

    CONSTRAINT ck_current_regime_confidence
        CHECK (
            confidence >= 0
            AND confidence <= 100
        ),

    CONSTRAINT ck_current_regime_visual_indicator
        CHECK (
            visual_indicator IN (
                'bull',
                'bear',
                'recession'
            )
        )
);


-- ============================================================
-- A3.4 COMPATIBILITY FOR EXISTING DATABASES
--
-- If current_regime was already created by A3.1, the
-- CREATE TABLE IF NOT EXISTS statement above does not modify it.
--
-- These statements add the new A3.4 columns when necessary.
-- ============================================================

ALTER TABLE current_regime
    ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION;

ALTER TABLE current_regime
    ADD COLUMN IF NOT EXISTS visual_indicator VARCHAR(20);


-- ============================================================
-- BACKFILL EXISTING CURRENT REGIME RECORDS
--
-- Existing A3.1 records did not have confidence or
-- visual_indicator.
--
-- Until the A3.4 service starts writing calculated values,
-- existing records receive neutral/default values.
-- ============================================================

UPDATE current_regime
SET confidence = 0
WHERE confidence IS NULL;

UPDATE current_regime
SET visual_indicator = 'recession'
WHERE visual_indicator IS NULL;


-- ============================================================
-- ADD NOT NULL CONSTRAINTS
-- ============================================================

ALTER TABLE current_regime
    ALTER COLUMN confidence SET NOT NULL;

ALTER TABLE current_regime
    ALTER COLUMN visual_indicator SET NOT NULL;


-- ============================================================
-- ADD A3.4 CHECK CONSTRAINTS SAFELY
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_current_regime_confidence'
    ) THEN

        ALTER TABLE current_regime
            ADD CONSTRAINT ck_current_regime_confidence
            CHECK (
                confidence >= 0
                AND confidence <= 100
            );

    END IF;
END
$$;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_current_regime_visual_indicator'
    ) THEN

        ALTER TABLE current_regime
            ADD CONSTRAINT ck_current_regime_visual_indicator
            CHECK (
                visual_indicator IN (
                    'bull',
                    'bear',
                    'recession'
                )
            );

    END IF;
END
$$;


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS ix_macro_regimes_regime_type
    ON macro_regimes (regime_type);

CREATE INDEX IF NOT EXISTS ix_macro_regimes_start_date
    ON macro_regimes (start_date);

CREATE INDEX IF NOT EXISTS ix_macro_regimes_end_date
    ON macro_regimes (end_date);

CREATE INDEX IF NOT EXISTS ix_regime_performance_regime_id
    ON regime_performance (regime_id);


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'current_regime'
ORDER BY ordinal_position;