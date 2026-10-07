-- 008_create_macro_indicator_vintages.sql
--
-- Point-in-time (PIT) store for revision-prone FRED macro series.
--
-- Problem this solves: FRED series like CPI, GDP, unemployment,
-- and M2 get revised after initial release. Training an ML model
-- on the *final* value of, say, January 2024 CPI leaks future
-- information into training: at prediction time in January 2024
-- the model would only have seen the initially-released value,
-- not the revision.
--
-- This table stores the full vintage history: for each
-- (series_id, observation_date), one row per release_date, with
-- the value as it was known at that release. The features writer
-- (B4) merges PIT-correct values by selecting, for each feature
-- hour H, the latest vintage row whose release_date <= H.
--
-- Scope:
--   Populated for 5 series only:
--     CPIAUCSL  -> cpi
--     UNRATE    -> unemployment
--     FEDFUNDS  -> federal_funds_rate
--     M2SL      -> m2_money_supply
--     GDP       -> gdp
--   Market features (DXY, VIX, 10Y, NASDAQ, HY spread) are not
--   revision-prone and do not get vintages.
--
-- Retention: unlimited (a few thousand rows per series per year).
--
-- Migration numbering note:
--   007_promote_hourly_to_hypertables.sql exists on this branch
--   (Chat 3) for an unrelated concern. 009_create_features_db.sql
--   is created on a sibling branch (B4). Migration filenames sort
--   lexicographically, so at runtime the order is 007 -> 008 ->
--   009 (whichever of 008/009 lands in the working tree first is
--   still fine: the two tables are independent at the DDL level;
--   B4's dependency on this table is at the DATA level, not the
--   SCHEMA level).
--
-- Idempotent: safe to run on an existing database.

CREATE TABLE IF NOT EXISTS macro_indicator_vintages (
    id                SERIAL           PRIMARY KEY,
    series_id         VARCHAR(50)      NOT NULL,
    indicator_name    VARCHAR(100)     NOT NULL,
    observation_date  DATE             NOT NULL,
    release_date      DATE             NOT NULL,
    value             DOUBLE PRECISION NOT NULL,
    created_at        TIMESTAMPTZ      NOT NULL DEFAULT now(),

    CONSTRAINT uq_macro_vintage_series_obs_release
        UNIQUE (series_id, observation_date, release_date)
);

-- Look up the full vintage history for one series.
CREATE INDEX IF NOT EXISTS idx_macro_vintages_series_obs
    ON macro_indicator_vintages (series_id, observation_date);

-- PIT merge support: for a given feature hour, find the latest
-- release on or before it.
CREATE INDEX IF NOT EXISTS idx_macro_vintages_release
    ON macro_indicator_vintages (release_date);

-- ============================================================
-- NO-OP VINTAGE POLICY
-- ============================================================
--
-- The service (MacroVintageService) filters out "no-op vintages":
-- consecutive releases for the same (series_id, observation_date)
-- where the value did not change from the previous release.
--
-- This filter is applied in the SERVICE, not enforced by the
-- TABLE. The schema permits duplicate-value rows; the service
-- simply does not write them. Consequences:
--
--   - The PIT merge in B4 works identically with or without the
--     filter: "latest release_date <= H" still yields the value
--     in force at H, because the value didn't change between
--     filtered-out releases.
--
--   - The no-op filter halves the row count for little cost.
--
--   - Dropping the filter later is a SERVICE change, not a
--     SCHEMA change. If full revision history is ever needed
--     (e.g. for auditing), the service can simply stop filtering
--     and re-run; the ON CONFLICT DO NOTHING clause will coexist
--     with the previously-written non-no-op rows without
--     conflict.
--
-- See app/services/macro_vintage_service.py for the filter
-- implementation.

-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'macro_indicator_vintages'
ORDER BY ordinal_position;