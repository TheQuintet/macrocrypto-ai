-- ============================================================
-- Migration 010: Create historical_event_impacts table
-- ============================================================
-- Stores one row per historical event and the BTC reaction to
-- it. The row records the event's identity (event_name,
-- event_date), its classified significance (impact_level), and
-- the price reaction over the 48-hour window centered on the
-- event date (btc_price_before, btc_price_after,
-- price_change_percent, volatility, direction).
--
-- Populated by A5.2's reaction calculation; A5.3 aggregates the
-- per-event rows into per-event-type metrics; A5.4 exposes both
-- via an API endpoint; A5.5 runs the update as a scheduled job.
--
-- Design notes:
--   - event_date is a DATE, not a TIMESTAMPTZ. Events happen on
--     a calendar day, and the BTC price window that defines the
--     reaction is measured in days relative to it. Using a date
--     avoids timezone ambiguity: "the FOMC meeting of
--     2024-03-20" is a date, not a moment.
--   - UNIQUE (event_name, event_date) enforces the natural key.
--     The same event does not happen twice on the same day; if a
--     loader re-processes the same event (e.g. after correcting
--     the price window), it must UPSERT rather than INSERT. This
--     makes A5.5's daily job idempotent by construction.
--   - btc_price_before and btc_price_after are NOT NULL with a
--     positive-value CHECK. An event with no price before or
--     after its window is not a valid row; A5.2 should skip it
--     rather than write a row with NULLs.
--   - volatility is the standard deviation of percentage returns
--     over the window, so it is non-negative by definition. The
--     CHECK enforces that.
--   - direction has no CHECK beyond the enum values
--     ('up', 'down', 'neutral'). It is derived from
--     price_change_percent, but the table stores both because a
--     threshold can move a near-zero change into "neutral"
--     without changing the exact percentage.
--
-- Owner: AI Service
-- ============================================================

CREATE TABLE IF NOT EXISTS historical_event_impacts (
    id                      BIGSERIAL       PRIMARY KEY,

    -- Event identity — natural key is (event_name, event_date)
    event_name              VARCHAR(64)     NOT NULL,
    event_date              DATE            NOT NULL,

    -- Classified significance: 'high', 'medium', or 'low'
    impact_level            VARCHAR(16)     NOT NULL,

    -- Price before the event (24h before the event date)
    btc_price_before        DOUBLE PRECISION NOT NULL,

    -- Price after the event (24h after the event date)
    btc_price_after         DOUBLE PRECISION NOT NULL,

    -- Percentage change from before to after (signed)
    price_change_percent    DOUBLE PRECISION NOT NULL,

    -- Standard deviation of percentage returns over the window
    volatility              DOUBLE PRECISION NOT NULL,

    -- Derived direction: 'up', 'down', or 'neutral'
    direction               VARCHAR(16)     NOT NULL,

    -- Housekeeping
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- Natural key: an event happens once per day
    CONSTRAINT historical_event_impacts_name_date_unique
        UNIQUE (event_name, event_date)
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE historical_event_impacts
    ADD CONSTRAINT historical_event_impacts_impact_level_valid
    CHECK (impact_level IN ('high', 'medium', 'low'));

ALTER TABLE historical_event_impacts
    ADD CONSTRAINT historical_event_impacts_direction_valid
    CHECK (direction IN ('up', 'down', 'neutral'));

ALTER TABLE historical_event_impacts
    ADD CONSTRAINT historical_event_impacts_price_before_positive
    CHECK (btc_price_before > 0);

ALTER TABLE historical_event_impacts
    ADD CONSTRAINT historical_event_impacts_price_after_positive
    CHECK (btc_price_after > 0);

ALTER TABLE historical_event_impacts
    ADD CONSTRAINT historical_event_impacts_volatility_non_negative
    CHECK (volatility >= 0);

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
-- Index on event_name for "all reactions to event type X"
CREATE INDEX IF NOT EXISTS idx_historical_event_impacts_event_name
    ON historical_event_impacts (event_name);

-- Index on event_date for "all events in this date range"
CREATE INDEX IF NOT EXISTS idx_historical_event_impacts_event_date
    ON historical_event_impacts (event_date DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE historical_event_impacts IS
    'Historical event impact data — BTC reaction over the 48-hour window centered on each event (A5.1)';
COMMENT ON COLUMN historical_event_impacts.event_name IS
    'Event name (e.g. FOMC, CPI Release, NFP). Natural key part 1.';
COMMENT ON COLUMN historical_event_impacts.event_date IS
    'Calendar date the event occurred (UTC day). Natural key part 2.';
COMMENT ON COLUMN historical_event_impacts.impact_level IS
    'Classified significance: high, medium, or low';
COMMENT ON COLUMN historical_event_impacts.btc_price_before IS
    'BTC price 24 hours before the event date (must be positive)';
COMMENT ON COLUMN historical_event_impacts.btc_price_after IS
    'BTC price 24 hours after the event date (must be positive)';
COMMENT ON COLUMN historical_event_impacts.price_change_percent IS
    'Percentage change from btc_price_before to btc_price_after (signed)';
COMMENT ON COLUMN historical_event_impacts.volatility IS
    'Standard deviation of percentage returns over the window (non-negative)';
COMMENT ON COLUMN historical_event_impacts.direction IS
    'Derived direction of the price reaction: up, down, or neutral';
COMMENT ON COLUMN historical_event_impacts.created_at IS
    'When the row was first written (UTC)';