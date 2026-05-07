-- Add subcontractor proxies for client-appointed reporting / invoicing.
-- Safe to run multiple times.

CREATE TABLE IF NOT EXISTS sub_contractors (
    id BIGSERIAL PRIMARY KEY,
    client_name TEXT NOT NULL REFERENCES clients(client_name) ON DELETE CASCADE,
    sub_contractor_name TEXT NOT NULL,
    company TEXT,
    address TEXT,
    contact_name TEXT,
    email TEXT,
    phone TEXT,
    archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sub_contractors_client_name
    ON sub_contractors (client_name);

CREATE INDEX IF NOT EXISTS idx_sub_contractors_client_name_archived
    ON sub_contractors (client_name, archived);

ALTER TABLE IF EXISTS jobs
    ADD COLUMN IF NOT EXISTS proxy_sub_contractor_id BIGINT,
    ADD COLUMN IF NOT EXISTS proxy_sub_contractor_name TEXT;

NOTIFY pgrst, 'reload schema';
