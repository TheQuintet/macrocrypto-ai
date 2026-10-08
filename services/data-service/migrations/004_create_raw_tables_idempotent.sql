-- 004_create_raw_tables_idempotent.sql
--
-- Idempotent guards for the three raw tables. Before Phase B,
-- these were created by Base.metadata.create_all() in init_db().
-- Phase B removes create_all() (D5), so fresh databases need
-- these DDLs to exist as migrations.
--
-- No schema change: these mirror the ORM models exactly. If a
-- table already exists, this file is a no-op.
--
-- Hypertable creation is intentionally NOT done here. It stays in
-- app/database/session.py init_db(), where it already runs on
-- every startup idempotently via if_not_exists => TRUE.

CREATE TABLE IF NOT EXISTS btc_prices (
    id          SERIAL           NOT NULL,
    time        TIMESTAMPTZ      NOT NULL DEFAULT now(),
    price       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION,
    market_cap  DOUBLE PRECISION,
    source      VARCHAR(50)      NOT NULL DEFAULT 'binance',
    PRIMARY KEY (time, id)
);

CREATE INDEX IF NOT EXISTS ix_btc_prices_time
    ON btc_prices (time);
CREATE INDEX IF NOT EXISTS ix_btc_prices_source
    ON btc_prices (source);

CREATE TABLE IF NOT EXISTS macro_indicators (
    id              SERIAL           NOT NULL,
    time            TIMESTAMPTZ      NOT NULL,
    indicator_name  VARCHAR(100)     NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    previous_value  DOUBLE PRECISION,
    change_percent  DOUBLE PRECISION,
    source          VARCHAR(50)      NOT NULL DEFAULT 'fred',
    created_at      TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (time, id),
    CONSTRAINT uq_macro_indicator_time_name
        UNIQUE (time, indicator_name)
);

CREATE INDEX IF NOT EXISTS ix_macro_indicators_time
    ON macro_indicators (time);
CREATE INDEX IF NOT EXISTS ix_macro_indicators_indicator_name
    ON macro_indicators (indicator_name);

CREATE TABLE IF NOT EXISTS btc_dominance (
    id         SERIAL           PRIMARY KEY,
    time       TIMESTAMPTZ      NOT NULL,
    dominance  DOUBLE PRECISION NOT NULL,
    source     VARCHAR(50)      NOT NULL DEFAULT 'coingecko',
    CONSTRAINT uq_btc_dominance_time UNIQUE (time)
);

CREATE INDEX IF NOT EXISTS ix_btc_dominance_time
    ON btc_dominance (time);