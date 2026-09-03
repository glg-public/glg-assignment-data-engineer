---
status: accepted
---
# Build verified application states before seeding the exercise

We will maintain three distinct application states: a working Baseline Application before the Requested Changes, a private Reference Application implementing all four Requested Changes, and a separately produced Candidate Exercise derived from the baseline with six Seeded Defects. This gives every Requested Change and Seeded Defect objective expected behavior and prevents uncertainty over whether failures are intentional or accidental.

The application will run through Docker Compose on Windows and macOS. Airflow will orchestrate an ETL pipeline that reads one complete professional-profile Snapshot CSV per date, using a stable source `profile_id`, loads and models it in PostgreSQL, and serves results through a small read-only Flask application. The model will preserve selected attribute changes as SCD Type 2 Profile Versions, and the system will include an analytical query whose design can be improved.

The four Requested Changes are to process all dated Snapshots chronologically, preserve company/title/department changes as SCD Type 2 Profile Versions, optimize a separate correct-but-slow profile-search query without changing its results, and expose profile history in Flask. The six Seeded Defects will range from simple startup configuration, such as an incorrect port, to pipeline, idempotency, data-correctness, and query-design faults. Candidates will be told that the existing application may contain defects they must address, but not their count. The exercise is take-home work rather than a timed test; roughly one hour should produce useful evidence, but complete implementation and repair are not guaranteed or required in that time.

The Flask UI will show modeled profiles, profile history, company summaries, available Snapshot dates, and the last successful load. Airflow remains the interface for task status and diagnostic logs.

Before those Requested Changes, the Baseline Application will correctly load one configured Snapshot into a current-profile model and show current profiles and company totals in Flask. Test fixtures will include three small, human-readable Snapshots with unchanged, changed, new, inactive, and temporarily absent profiles; an explicit inactive marker closes a current Profile Version, while absence alone does not.

The Candidate Exercise will provide clear extension points and incomplete tests for the Requested Changes, but no partial SCD Type 2 implementation. Its Seeded Defects affect behavior inherited from the Baseline Application: an incorrect Flask port mapping, an incorrect DAG input path, incorrect parsing of the CSV inactive value, duplicate raw rows on rerun, join fan-out in company totals, and a transactional processing step that logs a data-quality failure without raising it, causing the Airflow run to report success.

Profile Versions use half-open periods: `valid_from` is inclusive, `valid_to` is exclusive, and the current version has no `valid_to`. Explicit inactivation closes the current version; later reactivation creates a new version even when tracked attributes match a previously closed version. Company headcount means active current profiles grouped by company, not historical point-in-time headcount.

The Reference model separates stable `profile` and `company` entities from employment-state Profile Versions. Name changes update those entities without creating a version. The Baseline `current_profile` table becomes a compatibility view when the Reference schema is introduced. Schema changes use plain versioned SQL migrations invoked by Python rather than ORM migrations.

Each Snapshot CSV has one row per profile and contains `profile_id`, `full_name`, `company_id`, `company_name`, `job_title`, `department`, and `is_active`; its date comes from a filename such as `profiles_2026-01-15.csv`. Duplicate profile IDs fail validation. One DAG run discovers unprocessed files, processes them chronologically, and records completed files in an ingestion-control table. Processing stops at the first failed Snapshot because later Profile Versions depend on earlier state.

Each Snapshot is processed in one database transaction covering raw insertion, modeling, quality checks, and ingestion completion. Failures roll back the Snapshot so it remains eligible for rerun; completed Snapshots are immutable and raw rows are unique by Snapshot date and profile ID. Required columns, Boolean values, active-profile fields, references, current-version uniqueness, duplicate IDs, and nonzero volume are checked.

The candidate README will explicitly frame the periodic files as the vendor's complete view at a point in time and the derived Profile Versions as the SCD Type 2 model. It will state how new, changed, inactive, and temporarily absent profiles are interpreted so candidates understand the application's intended domain behavior.

The Baseline UI provides an overview, searchable current profiles, and current company headcount. The Requested UI change adds a profile-history detail route. Search matches current active profiles case-insensitively across name, title, department, and company; optimization may use SQL, indexes, or schema changes but must preserve results and demonstrate a better PostgreSQL plan. The daily DAG supports manual runs, disables catchup, and the documented reset uses standard Docker Compose volume removal and rebuild commands.

The private Interviewer Guide will explain the architecture, expected behavior, Requested Changes, Seeded Defects, likely code changes, and useful follow-up probes. It will not assign scores or be included in the Candidate Exercise or its reachable Git history.

## Considered Options

- A vendor API was rejected in favor of files on disk because API behavior adds setup and debugging complexity not central to the intended ETL assessment.
- A notebook or Streamlit UI was rejected in favor of Flask because Flask remains Python-based while allowing a meaningful requested application change.
- Seeding defects while initially building the application was rejected because it makes intentional faults difficult to distinguish from unfinished behavior.

## Consequences

- Baseline and Reference behavior and automated checks must be complete before defects are introduced.
- Candidate distributions must be created without exposing the Reference Application or private guide through Git history.
- Docker images, commands, paths, and documentation must work with Docker Desktop on both Windows and macOS.
- UI complexity must remain secondary to data-engineering work.
- Candidates may change any repository file, but instructions will discourage unnecessary rewrites.
- Candidate-visible tests will cover startup, rerun safety, and core model invariants without mapping one-to-one to the six Seeded Defects.
- Private behavioral acceptance tests will remain outside candidate repositories because candidates may modify visible tests.
- Each candidate will receive a fresh private GitHub repository and submit code commits only; no written report is required.
- Host instructions will use `docker compose` without Bash-only scripts and support Docker Desktop on Apple Silicon macOS, Intel macOS, and Windows with WSL2.
- Candidate verification will run as `docker compose run --rm tests` without host Python or platform-specific tools.
- Performance work will use deterministic generated data and compare PostgreSQL plans while preserving exact results, not enforce a machine-dependent runtime threshold.
- Candidates receive three calendar days with flexible extensions, but no execution timer.
- Support covers Docker installation and unsupported-platform issues, not diagnosis of repository defects; substantive hints are retained for panel context.
