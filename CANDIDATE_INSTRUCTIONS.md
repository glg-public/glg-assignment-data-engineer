# Candidate Instructions

Read `README.md` first for the application overview, data semantics, setup, operation, and troubleshooting instructions.

> **Case study guidance:** Spend approximately 60-90 minutes. We do not expect every Requested Change to be completed. Prioritize as you see fit and be ready to explain your decisions. Do not spend time making the system production-ready.

Your assignment is to work through the seeded defects and implement as many of the required changes as time allows.

- Start the stack and inspect the service and Airflow task logs.
- Work through the items below in order where practical.
- Partial completion is expected. Be ready to explain your decisions and unfinished work.

## Seeded Defects

Diagnose and repair these four known problems. The investigation starting points are clues, not necessarily the causes or the complete fixes.

### SD1. Flask application address

- **Problem:** The Flask application is not available at the documented address after the stack starts.
- **Start investigating:** Application configuration in `.env`.
- **Expected outcome:** Flask is available at the address documented in `README.md`.

### SD2. Snapshot rerun safety

- **Problem:** Rerunning an already completed Snapshot can fail instead of completing safely.
- **Start investigating:** Ingestion status and rerun handling.
- **Expected outcome:** A completed Snapshot can be encountered again without causing an unnecessary failure.

### SD3. Inactive profiles in current results

- **Problem:** A profile explicitly marked inactive can remain in current-profile results and company headcount.
- **Start investigating:** CSV parsing and current-profile loading.
- **Expected outcome:** Explicitly inactive profiles are excluded from current-profile search and company headcount.

### SD4. Company headcount grain

- **Problem:** Company headcount can exceed the number of current active profiles belonging to that company.
- **Start investigating:** `mart.company_headcount` SQL and join grain.
- **Expected outcome:** Each company count represents its current active profiles without duplicate counting.

### Defect guidance

- Fix `SD2` before testing `RC1`; otherwise the already completed first Snapshot can prevent later files from being reached.
- Fix the underlying causes rather than suppressing symptoms or removing validation.

## Required Changes

### RC1. Process all available Snapshots

Alter the DAG so one run discovers and processes all unprocessed dated Snapshot files in chronological order.

- Completed files are skipped safely on later runs.
- A failed file remains retryable.
- Files dated after a failed file are not processed during that run.

### RC2. Optimize profile search

Improve the current-profile search query used by `/profiles` without changing its results or ordering.

Complete the performance investigation in these steps:

1. **Load the performance test data.** From the repository root, run:

   ```console
   docker compose run --rm generate-performance-data
   ```

   This creates a deterministic larger current-profile dataset. Generated profile IDs start with `PERF-`. Running the command again replaces prior generated rows.

2. **Start PostgreSQL.** From the repository root, open an interactive PostgreSQL session:

   ```console
   docker compose exec postgres psql -U case_study -d profile_data
   ```

   `postgres` is the Compose service, `case_study` is the database user, and `profile_data` is the application database.

3. **Capture a baseline.** At the `profile_data=#` prompt, run the search query below before making changes. Capture the execution time and query plan.

4. **Make the optimization.** You may rewrite SQL, add indexes, or alter the schema. Preserve the search results and ordering.

5. **Run the same test after the change.** Use the same dataset and the same `Specialist` query. At the PostgreSQL prompt, run the search query again and capture the execution time and query plan using the same method as the baseline.

6. **Demonstrate the improvement.** Compare the before-and-after measurements and be ready to explain what changed, why it improved the query, and any trade-offs.

Use this search query for both comparisons:

```sql
SELECT profile_id, full_name, company_name, job_title, department
FROM mart.current_profile
WHERE is_active
  AND (
    'Specialist' = ''
    OR full_name ILIKE '%Specialist%'
    OR company_name ILIKE '%Specialist%'
    OR job_title ILIKE '%Specialist%'
    OR department ILIKE '%Specialist%'
  )
ORDER BY full_name, profile_id;
```

Exit the PostgreSQL session with `\q` when finished.

### RC3. Preserve profile history

Evolve the current-state model into an SCD Type 2 profile-history model.

- Preserve changes to company, job title, and department.
- Keep display-name changes from creating new employment-history versions.
- Use inclusive `valid_from` and exclusive `valid_to` dates.
- A current version has `valid_to = NULL`.
- Each active profile has exactly one current version; inactive profiles have none.
- Keep `mart.current_profile` available as the current-state interface used by existing application pages.
- Use the provided `mart.profile_history` table shell for the historical rows.

Example: a change first seen in the `2026-02-01` Snapshot closes the old version with `valid_to = 2026-02-01` and starts the new version with `valid_from = 2026-02-01`.

### RC4. Show profile history

Add a profile detail page at `/profiles/<profile_id>` and link profile-search results to it.

Display:

- The profile's latest display name.
- Company, job title, and department for each version.
- The effective period for each version in chronological order.

Inactive profiles should remain available through their history page even though they are excluded from current-profile search and company headcount.

## Validation

Run the checks documented in `README.md`. They provide useful feedback but are not exhaustive.

- Inspect Airflow task status and logs.
- Inspect Flask output.
- Test database behavior on reruns.
- Verify behavior when processing multiple Snapshots, including a failed file.
- Compare profile-search performance before and after the optimization.
- Verify current-profile, headcount, and history behavior for active and inactive profiles.

## Scope

- You may change any file in the repository.
- Prefer focused changes over an unnecessary rewrite.
- Partial completion is acceptable and still useful for the follow-up discussion.
- AI tools are permitted, but you must be able to explain every change you make.
- Do not include credentials, proprietary data, or external paid services.

## Follow-Up Interview

Keep your changes on your machine; you do not need to upload or submit them.

During the follow-up interview, be prepared to share your screen and walk through the running application, code changes, logs, validation, assumptions, and unfinished work.

Complete what you reasonably can before the scheduled follow-up interview. Contact the recruiting team if scheduling or an accommodation requires more time.

## Support

Contact the provided hiring-team representative if you cannot access the repository, install or run Docker Desktop, or believe your platform is unsupported. Application configuration, pipeline behavior, SQL, and code diagnosis are part of the exercise.
