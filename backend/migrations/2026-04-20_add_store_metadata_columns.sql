-- Add store metadata fields used by the refreshed company/store import.
-- Safe to run multiple times.

ALTER TABLE IF EXISTS client_sites
    ADD COLUMN IF NOT EXISTS postcode TEXT,
    ADD COLUMN IF NOT EXISTS store_id_code TEXT,
    ADD COLUMN IF NOT EXISTS ac_number TEXT,
    ADD COLUMN IF NOT EXISTS frequency_number INTEGER,
    ADD COLUMN IF NOT EXISTS last_clean DATE;

CREATE INDEX IF NOT EXISTS idx_client_sites_store_id_code
    ON client_sites (store_id_code);

CREATE INDEX IF NOT EXISTS idx_client_sites_client_name_store_id_code
    ON client_sites (client_name, store_id_code);

NOTIFY pgrst, 'reload schema';
