-- Safe to run multiple times.

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO system_settings (key, value)
VALUES ('report_notification_recipients', '[]')
ON CONFLICT (key) DO NOTHING;

NOTIFY pgrst, 'reload schema';
