CREATE TABLE mart.profile_history (
    profile_id text NOT NULL,
    company_id text NOT NULL,
    company_name text NOT NULL,
    job_title text NOT NULL,
    department text NOT NULL,
    valid_from date NOT NULL,
    valid_to date,
    PRIMARY KEY (profile_id, valid_from),
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE UNIQUE INDEX one_current_history_row_per_profile
ON mart.profile_history (profile_id)
WHERE valid_to IS NULL;
