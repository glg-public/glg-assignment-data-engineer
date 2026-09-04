# Candidate Instructions

Read `README.md` first for the application overview, data semantics, setup, operation, and troubleshooting instructions.

Your assignment is to implement the Requested Changes below.

The repository may not initially behave exactly as documented. Use service and Airflow task logs when startup or output is unexpected.

## Requested Changes

### 1. Repair Known Defects

Diagnose and repair these six observed problems:

1. The Flask application is not available at the documented address after the stack starts.
2. The `profile_snapshot` DAG fails when it attempts to read its configured source file.
3. A profile explicitly marked inactive can remain in current-profile results and company headcount.
4. Rerunning an already completed Snapshot can fail instead of completing safely.
5. Company headcount can exceed the number of current active profiles belonging to that company.
6. Snapshot processing can report success even when a data-quality check reports invalid output.

Fix the underlying causes rather than suppressing symptoms or removing validation.

### 2. Process Available Snapshots

Alter the DAG so one run discovers and processes all unprocessed dated Snapshot files in chronological order.

- Completed files must be skipped safely on later runs.
- A failed file must remain retryable.
- Files dated after a failed file must not be processed during that run.

### 3. Optimize Profile Search

Improve the current-profile search query used by `/profiles` without changing its results or ordering.

You may rewrite SQL, add indexes, or alter the schema. Use PostgreSQL's execution plan to understand and demonstrate the improvement rather than relying only on elapsed time.

Use the deterministic larger dataset described in `README.md` for query-plan analysis.

### 4. Preserve Profile History

Evolve the current-state model into an SCD Type 2 profile-history model.

- Preserve changes to company, job title, and department.
- Keep display-name changes from creating new employment-history versions.
- Use inclusive `valid_from` and exclusive `valid_to` dates.
- A current version has `valid_to = NULL`.
- Each active profile has exactly one current version; inactive profiles have none.
- Keep `mart.current_profile` available as the current-state interface used by existing application pages.

Example: a change first seen in the `2026-02-01` Snapshot closes the old version with `valid_to = 2026-02-01` and starts the new version with `valid_from = 2026-02-01`.

### 5. Show Profile History

Add a profile detail page at `/profiles/<profile_id>` and link profile-search results to it.

Display:

- The profile's latest display name.
- Company, job title, and department for each version.
- The effective period for each version in chronological order.

Inactive profiles should remain available through their history page even though they are excluded from current-profile search and company headcount.

## Validation

Run the checks documented in `README.md`. They provide useful feedback but are not exhaustive. Also inspect Airflow task status and logs, Flask output, database behavior on reruns, and PostgreSQL query plans.

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
