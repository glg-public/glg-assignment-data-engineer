CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS ops;
CREATE SCHEMA IF NOT EXISTS mart;

CREATE TABLE raw.profile_snapshot (
    snapshot_date date NOT NULL,
    profile_id text NOT NULL,
    full_name text NOT NULL,
    company_id text,
    company_name text,
    job_title text,
    department text,
    is_active boolean NOT NULL,
    source_file text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (snapshot_date, profile_id)
);

CREATE TABLE ops.snapshot_ingestion (
    snapshot_date date PRIMARY KEY,
    source_file text NOT NULL,
    status text NOT NULL CHECK (status IN ('completed', 'failed')),
    row_count integer,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    error_message text
);

CREATE TABLE mart.current_profile (
    profile_id text PRIMARY KEY,
    full_name text NOT NULL,
    company_id text,
    company_name text,
    job_title text,
    department text,
    is_active boolean NOT NULL,
    snapshot_date date NOT NULL
);

CREATE VIEW mart.company_headcount AS
SELECT
    current_profile.company_id,
    current_profile.company_name,
    count(*)::integer AS active_profiles
FROM mart.current_profile
JOIN raw.profile_snapshot
    ON raw.profile_snapshot.company_id = current_profile.company_id
WHERE current_profile.is_active
GROUP BY current_profile.company_id, current_profile.company_name;
