# Data Engineering Take-Home: Project Brief

## Purpose

Build a self-contained data pipeline that can later become a debugging exercise for Data Operations Engineer candidates.

Candidates will receive a Git repository, start the system locally with Docker Compose, diagnose seeded faults, fix as many as they can, and explain their investigation and decisions in a follow-up panel. The exercise should test practical data-engineering judgment rather than familiarity with GLG systems.

The first delivery is a fully working Baseline Application. A private Reference Application will then implement the Requested Changes before Seeded Defects are introduced into a separate Candidate Exercise.

## Candidate Experience

The eventual exercise should let a candidate:

1. Clone the repository and run one documented Docker Compose command.
2. Open a local Airflow UI and trigger or inspect a pipeline.
3. Observe incorrect behavior through logs, task status, tests, and output data.
4. Implement four Requested Changes while diagnosing and repairing defects encountered across Python, SQL, orchestration, and data quality.
5. Run an automated verification command before submitting.
6. Explain every submitted change, including AI-assisted code, during the panel.

The repository must require no GLG network access, cloud account, or paid service. It should run on a typical candidate laptop with Docker Desktop and Git.

## Proposed Scenario

A fictional vendor provides a complete CSV Snapshot of professional profiles each day. Each row has a stable profile identifier and contains a person, current employer, and current role attributes. An Airflow pipeline ingests the files, retains the raw input, models it in PostgreSQL, and publishes queryable output through a read-only Flask application.

This scenario resembles the team's third-party ingestion work while using only synthetic data and generic business concepts.

## Working Application

The baseline repository will contain:

- Docker Compose services for Airflow, PostgreSQL, and Flask.
- Three small, deterministic Snapshots containing unchanged, changed, new, inactive, and temporarily absent profiles, plus separate generated data for query-performance work.
- A scheduled Airflow DAG that ingests dated Snapshot files and records ingestion metadata.
- Raw landing tables that preserve source payloads and snapshot provenance.
- SQL/Python transformations into modeled person and employment tables with explicit grain and keys.
- A small published output, such as current professional profiles and employee counts by company.
- Data-quality checks for schema, uniqueness, referential integrity, expected volume, and freshness.
- Safe re-runs that do not duplicate or corrupt data.
- Useful task logs and failure messages.
- Automated tests and a single verification command.
- A concise README covering prerequisites, startup, execution, verification, reset, and troubleshooting.

The candidate README must explain the source and model in plain language:

> A fictional vendor periodically provides a complete Snapshot of its professional-profile data. The pipeline compares each dated Snapshot with the currently stored profile state. New profiles are added; changes to company, job title, or department create a new historical version; and explicit inactivation closes the current version. A profile missing from one Snapshot is not assumed inactive. The incoming CSV files are Snapshots; the derived profile history is the SCD Type 2 model.

The initial database shape is:

- `raw.profile_snapshot` for landed Snapshot rows and provenance.
- `ops.snapshot_ingestion` for processing state.
- `mart.current_profile` for Baseline current-state output.
- `mart.profile` and `mart.company` for stable entities in the Reference Application.
- `mart.profile_version` for Reference Application history.
- `mart.company_headcount` for current active counts by company.

When the Reference Application introduces the entity and version tables, `mart.current_profile` becomes a compatibility view so existing consumers continue to work. Database changes use plain versioned SQL migrations invoked by Python rather than an ORM migration framework.

## Skills Assessed

| Area | Evidence in the exercise |
|---|---|
| Python | File ingestion, validation, error handling, and maintainable pipeline code |
| SQL | Joins, windowing/deduplication, grain, correctness, and query performance |
| ETL/ELT | Raw-to-modeled flow, full snapshots, incremental processing, and backfills |
| Data modeling | Stable keys, person/employment grain, current state, and retained history |
| Airflow | Dependencies, retries, scheduling, parameters, and task failure semantics |
| Reliability | Idempotency, partial failure, reruns, and checkpoint behavior |
| Data quality | Detection of silent success, missing data, duplicates, and broken relationships |
| Debugging | Reading code and logs, forming hypotheses, and verifying repairs |
| Communication | Explaining investigation, tradeoffs, limitations, and submitted code |

Airflow experience itself is not a hiring gate. The repository and task should provide enough context for a capable Python/data engineer to reason through unfamiliar orchestration code.

## Requested Changes

The Candidate Exercise will ask candidates to:

1. Alter the DAG to discover and process all dated Snapshot files chronologically.
2. Preserve changes to company, title, and department as SCD Type 2 Profile Versions.
3. Optimize a correct-but-slow profile-search query without changing its results.
4. Extend Flask to show profile history.

The Baseline Application will correctly process one configured Snapshot into a current-profile model and show current profiles and company totals in Flask. It is intentionally limited, not defective.

## Fault Design Principles

The Candidate Exercise will contain six Seeded Defects. Candidates will be told only that the existing application may contain defects relevant to completing the Requested Changes.

Each fault should:

- Represent a plausible production failure, not a syntax puzzle or obscure framework fact.
- Test a distinct behavior or line of reasoning.
- Have an observable symptom and an objective acceptance test.
- Be repairable without external access or unstated domain knowledge.
- Permit reasonable alternative fixes when the underlying behavior is corrected.
- Avoid cascading so heavily that one fix automatically resolves most other faults.
- Support a useful panel discussion about how the candidate found and validated it.

The mix should include both obvious task failures and silent-success/data-correctness failures. At least one task should involve SQL performance, but it must remain small enough to run reliably on a laptop.

The six planned Seeded Defects are:

1. Flask's documented host port maps incorrectly.
2. The Airflow DAG uses an incorrect input path.
3. The CSV loader interprets the string `false` as true.
4. Rerunning the raw load duplicates rows.
5. The company-total query has join fan-out.
6. A failed data-quality check is logged but not raised, so processing reports success.

The SCD Type 2 change itself will not be partially implemented or deliberately broken. The Candidate Exercise will instead provide clear extension points and incomplete tests.

## Data Semantics

- `profile_id` is a stable source identifier.
- Each Snapshot has one row per profile with `profile_id`, `full_name`, `company_id`, `company_name`, `job_title`, `department`, and `is_active`.
- The Snapshot date comes from its filename, such as `profiles_2026-01-15.csv`.
- Duplicate `profile_id` values within a Snapshot fail validation.
- Tracked versioned attributes are company, title, and department.
- A company-name or full-name change alone does not create a new Profile Version.
- `valid_from` is inclusive; `valid_to` is exclusive and null for the current Profile Version.
- An explicit inactive value closes the current version; absence from one Snapshot does not.
- Reactivation creates a new current Profile Version even when attributes match a previously closed version.
- Company headcount counts active current profiles grouped by company; historical point-in-time headcount is out of scope.
- One DAG run discovers unprocessed Snapshots, processes them chronologically, and stops at the first failure.
- An ingestion-control table records completed Snapshots so reruns skip them safely.
- Each Snapshot is atomic: raw insertion, modeling, quality checks, and completion commit together or roll back together.
- Completed Snapshot data is immutable, and `(snapshot_date, profile_id)` is unique in raw storage.
- Empty Snapshots fail processing.

Working quality checks cover required columns, unique profile IDs, recognized Boolean values, required tracked attributes for active profiles, referential integrity, exactly one current Profile Version per active profile and none per inactive profile, and nonzero volume.

## Application Interface

The Baseline Flask application provides:

- `/` for an overview and latest successful load.
- `/profiles` for searchable current profiles.
- `/companies` for current active headcount by company.

Requested Change 4 adds `/profiles/<profile_id>` for chronological profile history and links current-profile rows to it. Inactive profiles retain history but are excluded from current profiles and company headcount.

Profile search covers current active profiles by case-insensitive full name, job title, department, or company name and sorts by name. Candidates may rewrite SQL, add indexes, or alter schema when optimizing it, provided results remain unchanged and they explain the plan difference.

The Airflow DAG has a daily schedule, supports manual runs, and disables catchup. A clean reset uses `docker compose down --volumes` followed by `docker compose up --build`.

## Deliverables

### Phase 1: Baseline and Reference Applications

- Runnable repository and Docker Compose environment.
- Complete pipeline and deterministic data fixtures.
- Private implementation of all four Requested Changes.
- Automated behavioral and data-quality tests.
- Maintainer documentation proving the expected end-to-end result.

### Phase 2: Assessment Package

- Candidate distribution containing seeded faults without solution-revealing Git history.
- Candidate-facing instructions, scope, expected time, and submission process.
- Private maintainer fault catalog with symptoms, intended diagnosis, valid fixes, and verification steps.
- Automated evaluator and panel walkthrough guide.
- Trial-run feedback from at least one engineer who did not build the exercise.

## Success Criteria

The project succeeds when:

- A new user can start it from a clean checkout using only documented commands.
- The working baseline produces deterministic, correct outputs and passes all checks.
- Resetting and rerunning the environment is reliable.
- Each later seeded fault is independently detectable and verifiable.
- The exercise differentiates practical debugging and data judgment without depending on proprietary knowledge.
- A reviewer can evaluate behavior consistently while still allowing multiple sound implementations.
- The panel can use the submission to discuss process, ownership, and depth rather than merely count fixes.

## Constraints and Non-Goals

- Use synthetic data only; include no GLG code, credentials, schemas, or production details.
- Keep laptop resource use and image download size reasonable.
- Pin dependencies and container images for reproducibility.
- Do not require candidates to build infrastructure or learn a cloud platform.
- Do not turn the exercise into algorithm trivia, a dashboard task, or an ML exercise.
- Do not require every candidate to find every fault for their submission to be useful.
- Keep the private working baseline and answer material out of the candidate repository's reachable history.
- Treat a missing profile in one complete Snapshot as ambiguous; only an explicit inactive marker closes its current Profile Version.
- Treat roughly one hour as enough to produce useful evidence, not as a completion requirement or time limit.
- Allow candidates to edit any repository file while discouraging unnecessary rewrites.
- Support Docker Desktop on Apple Silicon macOS, Intel macOS, and Windows with WSL2 using host commands that do not require Bash.
- Give each candidate a fresh private GitHub repository and request code commits only; discuss assumptions, validation, and unfinished work in the panel.
- Expose smoke tests for startup, rerun safety, and core model invariants without revealing a one-to-one Seeded Defect checklist.
- Run candidate checks through `docker compose run --rm tests`; keep authoritative behavioral tests outside candidate repositories.
- Assess query improvement by preserved results and a better PostgreSQL plan, not a machine-dependent runtime threshold.
- Give candidates three calendar days to return the repository, with flexible scheduling and accommodation extensions; do not impose an execution timer.
- Provide support for Docker installation and unsupported-platform issues, but do not diagnose repository configuration or application defects. Record substantive hints for panel context.

## Decisions Needed Before the Specification

1. Exact repository provisioning process and access ownership.
2. Minimum Docker resource assumptions after measuring the completed stack.
3. Required accessibility or accommodation language for the take-home instructions.
