-- ============================================================
-- Migration: Economic Calendar Tables
-- Sprint 5 - S3.1
--
-- Creates:
--   - economic_events
--   - user_calendar_preferences
--
-- Economic event timestamps are stored in UTC.
-- PostgreSQL TIMESTAMPTZ is used for timezone-aware storage.
-- ============================================================


-- ============================================================
-- ECONOMIC EVENTS
-- ============================================================

CREATE TABLE IF NOT EXISTS economic_events (
    id SERIAL PRIMARY KEY,

    event_name VARCHAR(150) NOT NULL,

    event_type VARCHAR(30) NOT NULL,

    event_date TIMESTAMPTZ NOT NULL,

    impact_level VARCHAR(20) NOT NULL,

    description TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_economic_events_event_type
        CHECK (
            event_type IN (
                'fed',
                'cpi',
                'employment',
                'gdp'
            )
        ),

    CONSTRAINT ck_economic_events_impact_level
        CHECK (
            impact_level IN (
                'high',
                'medium',
                'low'
            )
        )
);


-- ============================================================
-- USER CALENDAR PREFERENCES
-- ============================================================

CREATE TABLE IF NOT EXISTS user_calendar_preferences (
    id SERIAL PRIMARY KEY,

    user_id INTEGER NOT NULL,

    timezone VARCHAR(64) NOT NULL DEFAULT 'UTC',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS ix_economic_events_event_date
    ON economic_events (event_date);

CREATE INDEX IF NOT EXISTS ix_economic_events_event_type
    ON economic_events (event_type);

CREATE INDEX IF NOT EXISTS ix_economic_events_event_date_type
    ON economic_events (event_date, event_type);

CREATE INDEX IF NOT EXISTS ix_user_calendar_preferences_user_id
    ON user_calendar_preferences (user_id);


-- ============================================================
-- VERIFICATION
-- ============================================================

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN (
    'economic_events',
    'user_calendar_preferences'
)
ORDER BY
    table_name,
    ordinal_position;