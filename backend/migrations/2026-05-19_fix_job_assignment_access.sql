-- Safe to run multiple times.
-- The backend reads/writes these tables through the Supabase REST client.
-- Without policies, enabled RLS can make contributor/supervisor assignments invisible.

ALTER TABLE IF EXISTS job_engineers
    DISABLE ROW LEVEL SECURITY;

ALTER TABLE IF EXISTS job_contributions
    DISABLE ROW LEVEL SECURITY;

NOTIFY pgrst, 'reload schema';
