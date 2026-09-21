-- ============================================================
-- Migration 009: Create export_history table
-- ============================================================
-- Stores one row per export request an analyst or system process
-- has made. Records what was requested (export_type, data_types,
-- timeframe) and the outcome (status, file_name, file_size,
-- downloaded_at).
--
-- Populated by the export pipeline (A2.2 through A2.6); read by
-- the export history API (a later branch). Rows are created when
-- the request arrives (status='pending'), updated when the file
-- is generated (status='completed', file_name + file_size set),
-- and updated again when the caller downloads the file
-- (downloaded_at set).
--
-- Design notes:
--   - user_id is a VARCHAR(64) opaque identifier, NOT a foreign
--     key. The auth system lives in a different service; there
--     is no `users` table in this database to reference. It is
--     nullable because system-triggered exports have no user.
--   - data_types is JSONB so the array is indexable and the DB
--     can enforce valid JSON at insert time. Default is an empty
--     JSON array.
--   - file_size and downloaded_at are nullable because they are
--     populated at different stages of the export lifecycle.
--
-- Owner: AI Service
-- ============================================================

CREATE TABLE IF NOT EXISTS export_history (
    id                  BIGSERIAL       PRIMARY KEY,

    -- Opaque user identifier (nullable — system-triggered exports
    -- have no user)
    user_id             VARCHAR(64),

    -- Export format: 'csv', 'png', or 'pdf'
    export_type         VARCHAR(8)      NOT NULL,

    -- JSON array of data types included in the export
    -- (e.g. ["btc_price", "correlations", "regimes", "events"])
    data_types          JSONB           NOT NULL DEFAULT '[]'::jsonb,

    -- Timeframe of the exported data: '30d', '90d', '1y', or '5y'
    timeframe           VARCHAR(8)      NOT NULL,

    -- Generated filename (set when the file is created)
    file_name           VARCHAR(255)    NOT NULL,

    -- File size in bytes (set when the file is created)
    file_size           BIGINT,

    -- Lifecycle status: 'pending', 'completed', or 'failed'
    status              VARCHAR(16)     NOT NULL DEFAULT 'pending',

    -- When the export was requested
    created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    -- When the file was last downloaded (nullable)
    downloaded_at       TIMESTAMPTZ
);

-- ------------------------------------------------------------
-- CHECK constraints
-- ------------------------------------------------------------
ALTER TABLE export_history
    ADD CONSTRAINT export_history_export_type_valid
    CHECK (export_type IN ('csv', 'png', 'pdf'));

ALTER TABLE export_history
    ADD CONSTRAINT export_history_timeframe_valid
    CHECK (timeframe IN ('30d', '90d', '1y', '5y'));

ALTER TABLE export_history
    ADD CONSTRAINT export_history_status_valid
    CHECK (status IN ('pending', 'completed', 'failed'));

-- ------------------------------------------------------------
-- Indexes
-- ------------------------------------------------------------
-- Single-column index for "all my exports"
CREATE INDEX IF NOT EXISTS idx_export_history_user_id
    ON export_history (user_id);

-- Single-column index for "most recent exports across all users"
CREATE INDEX IF NOT EXISTS idx_export_history_created_at
    ON export_history (created_at DESC);

-- Composite index for "my most recent exports"
CREATE INDEX IF NOT EXISTS idx_export_history_user_created
    ON export_history (user_id, created_at DESC);

-- ------------------------------------------------------------
-- Documentation
-- ------------------------------------------------------------
COMMENT ON TABLE export_history IS
    'Export request history — what was requested and how it turned out (A2.1)';
COMMENT ON COLUMN export_history.user_id IS
    'Opaque user identifier from the auth service. NULL for system-triggered exports.';
COMMENT ON COLUMN export_history.export_type IS
    'Export format: csv, png, or pdf';
COMMENT ON COLUMN export_history.data_types IS
    'JSON array of data types included (e.g. ["btc_price", "correlations"])';
COMMENT ON COLUMN export_history.timeframe IS
    'Timeframe of the exported data: 30d, 90d, 1y, or 5y';
COMMENT ON COLUMN export_history.file_name IS
    'Generated filename (set when the file is created)';
COMMENT ON COLUMN export_history.file_size IS
    'File size in bytes (set when the file is created)';
COMMENT ON COLUMN export_history.status IS
    'Lifecycle status: pending, completed, or failed';
COMMENT ON COLUMN export_history.created_at IS
    'When the export was requested (UTC)';
COMMENT ON COLUMN export_history.downloaded_at IS
    'When the file was last downloaded (UTC), or NULL';