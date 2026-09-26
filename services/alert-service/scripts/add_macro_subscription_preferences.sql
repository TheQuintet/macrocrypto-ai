-- Run against an existing alert-service database when macro_event_subscriptions
-- was created before timing / notify / one_time columns existed.

ALTER TABLE macro_event_subscriptions
    ADD COLUMN IF NOT EXISTS timing VARCHAR(8) NOT NULL DEFAULT '1d',
    ADD COLUMN IF NOT EXISTS one_time BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS notify_in_app BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS notify_email BOOLEAN NOT NULL DEFAULT FALSE;
