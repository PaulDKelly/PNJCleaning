-- Safe to run multiple times.

CREATE TABLE IF NOT EXISTS job_engineers (
    id BIGSERIAL PRIMARY KEY,
    job_number TEXT NOT NULL,
    engineer_contact_name TEXT NOT NULL,
    -- Expected values: Lead, Contributing, Supervisor.
    engineer_role TEXT NOT NULL DEFAULT 'Contributing',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (job_number, engineer_contact_name)
);

CREATE INDEX IF NOT EXISTS idx_job_engineers_job_number
    ON job_engineers (job_number);

CREATE INDEX IF NOT EXISTS idx_job_engineers_engineer_contact_name
    ON job_engineers (engineer_contact_name);

ALTER TABLE IF EXISTS job_engineers
    ENABLE ROW LEVEL SECURITY;

NOTIFY pgrst, 'reload schema';
