-- Bring the live Supabase schema up to the current callout-capable app code.
-- Safe to run multiple times.

ALTER TABLE IF EXISTS jobs
    ADD COLUMN IF NOT EXISTS job_type TEXT NOT NULL DEFAULT 'Extraction';

ALTER TABLE IF EXISTS extraction_reports
    ADD COLUMN IF NOT EXISTS job_type TEXT NOT NULL DEFAULT 'Extraction',
    ADD COLUMN IF NOT EXISTS issue_description TEXT,
    ADD COLUMN IF NOT EXISTS work_done TEXT,
    ADD COLUMN IF NOT EXISTS recommendations TEXT,
    ADD COLUMN IF NOT EXISTS sketch_photo_path TEXT;

-- Promote any fallback callout markers created while the schema was behind.
UPDATE jobs
SET job_type = 'Breakdown/Callout',
    notes = NULLIF(regexp_replace(COALESCE(notes, ''), '^\[CALL OUT\]\s*', ''), '')
WHERE COALESCE(notes, '') LIKE '[CALL OUT]%';

UPDATE extraction_reports
SET job_type = 'Breakdown/Callout',
    issue_description = COALESCE(issue_description, remedial_requirements),
    recommendations = COALESCE(recommendations, risk_improvements),
    work_done = COALESCE(
        work_done,
        NULLIF(
            regexp_replace(
                COALESCE(sketch_details, ''),
                '^\[CALL OUT\]\s*(Work done:\s*)?',
                ''
            ),
            ''
        )
    )
WHERE COALESCE(sketch_details, '') LIKE '[CALL OUT]%';

NOTIFY pgrst, 'reload schema';
