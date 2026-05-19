-- Safe to run multiple times.

CREATE TABLE IF NOT EXISTS job_contributions (
    id BIGSERIAL PRIMARY KEY,
    job_number TEXT NOT NULL,
    engineer_contact_name TEXT NOT NULL,
    engineer_role TEXT NOT NULL DEFAULT 'Contributing',
    note TEXT,
    media_path TEXT,
    media_type TEXT,
    original_filename TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_contributions_job_number
    ON job_contributions (job_number);

CREATE INDEX IF NOT EXISTS idx_job_contributions_engineer_contact_name
    ON job_contributions (engineer_contact_name);

ALTER TABLE IF EXISTS job_contributions
    DISABLE ROW LEVEL SECURITY;

NOTIFY pgrst, 'reload schema';
