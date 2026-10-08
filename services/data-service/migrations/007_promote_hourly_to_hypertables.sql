-- 007_promote_hourly_to_hypertables.sql
--
-- 005 and 006 create the hourly tables but predate the decision
-- to make hypertable conversion part of the migration. This file
-- promotes any existing installations.
--
-- Idempotent: if a table is already a hypertable, or if 005/006
-- already promoted it on a fresh install, this file is a no-op.

SELECT create_hypertable(
    'btc_prices_hourly',
    'time',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

SELECT create_hypertable(
    'macro_indicators_hourly',
    'time',
    if_not_exists => TRUE,
    migrate_data => TRUE
);