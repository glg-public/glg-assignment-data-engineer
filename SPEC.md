# Data Engineering Take-Home Specification

## 1. Objective

Build a compact, self-contained application that demonstrates a realistic professional-profile data flow:

```text
dated CSV Snapshots -> Airflow ETL -> PostgreSQL -> Flask UI
```

The project has three deliverable states:

1. **Baseline Application**: a correct application that processes one configured Snapshot and presents current data.
2. **Reference Application**: a private implementation of all four Requested Changes.
3. **Candidate Exercise**: a fresh repository derived from the baseline, containing the four candidate-facing Requested Changes and six Seeded Defects.

The system assesses practical Python, SQL, ETL, data modeling, orchestration, idempotency, data quality, debugging, and communication skills. Airflow-specific knowledge is not a prerequisite.

## 2. Candidate Experience

A candidate must be able to:

1. Clone a private repository.
2. Start the stack with Docker Desktop and documented `docker compose` commands.
3. Use Airflow to trigger and inspect the pipeline.
4. Use Flask to inspect modeled results.
5. Implement four Requested Changes and repair defects encountered while doing so.
6. Run `docker compose run --rm tests` for visible feedback.
7. Push code commits without preparing a separate report.
8. Explain changes, validation, assumptions, and unfinished work in the panel.

Candidates receive three calendar days, with flexible extensions for scheduling and accommodations. The exercise is not timed. Roughly one hour of work should produce useful evidence, but complete implementation and repair are not required within that period.

## 3. Platform Contract

The repository must support:

- Docker Desktop on Apple Silicon macOS.
- Docker Desktop on Intel macOS.
- Docker Desktop on Windows using WSL2.
- Host commands that use `docker compose` and do not require Bash, Make, host Python, or a native PostgreSQL client.
- Multi-architecture, version-pinned container images.
- A clean reset using `docker compose down --volumes`, followed by `docker compose up --build`.

No GLG access, cloud account, credential, paid service, or proprietary data may be required. Minimum CPU, memory, and disk requirements will be documented after measuring the completed stack.

## 4. Domain Model

### 4.1 Source Snapshot

A fictional vendor periodically provides a CSV containing its complete view of professional profiles on a date. Files follow this convention:

```text
profiles_YYYY-MM-DD.csv
```

The filename is the authoritative Snapshot date. Every row contains:

| Column | Meaning | Rules |
|---|---|---|
| `profile_id` | Stable vendor profile identifier | Required; unique within a Snapshot |
| `full_name` | Current display name | Required |
| `company_id` | Stable vendor company identifier | Required for active profiles |
| `company_name` | Current company display name | Required for active profiles |
| `job_title` | Current job title | Required for active profiles |
| `department` | Current department | Required for active profiles |
| `is_active` | Explicit profile activity state | Required; only recognized Boolean representations accepted |

One Snapshot cannot contain duplicate `profile_id` values. An empty Snapshot is invalid.

### 4.2 Snapshot Interpretation

- A new active `profile_id` creates a profile and its first current Profile Version.
- A change to `company_id`, `job_title`, or `department` closes the current Profile Version and creates another.
- A change only to `full_name` or `company_name` updates display data without creating a Profile Version.
- `is_active=false` closes the current Profile Version.
- A later active row creates a new current Profile Version, even if it matches an older closed version.
- Absence from a Snapshot is ambiguous and causes no profile-state change.

The source CSVs are Snapshots. The derived historical table is the SCD Type 2 model.

### 4.3 Version Periods

Profile Versions use half-open date periods:

- `valid_from` is inclusive.
- `valid_to` is exclusive.
- A current version has `valid_to = NULL`.
- An active profile has exactly one current version.
- An inactive profile has no current version but retains closed history.

For example, a change observed in the `2026-02-01` Snapshot closes the previous version with `valid_to = 2026-02-01` and starts the new version with `valid_from = 2026-02-01`.

## 5. Data Fixtures

Ship three small, deterministic Snapshots containing 20-30 profiles in total. Across the files, include:

- Profiles that never change.
- New profiles after the first Snapshot.
- Company, title, and department changes.
- Display-name-only changes.
- Explicit inactivation.
- Reactivation.
- A profile temporarily absent and later present again.

The fixtures must be readable enough to verify behavior manually. A separate deterministic generator supplies enough rows for PostgreSQL query-plan analysis without bloating the checked-in CSVs.

## 6. Architecture

### 6.1 Services

Docker Compose provides:

- PostgreSQL for application data.
- Airflow webserver and scheduler, with only the additional services required by the selected supported executor.
- Flask web application.
- Test runner profile or service.

Airflow metadata and application data must use separate databases or schemas so their ownership is clear.

### 6.2 Database Schemas

Use these logical schemas and relations:

| Relation | State | Purpose |
|---|---|---|
| `raw.profile_snapshot` | All | Immutable landed rows with Snapshot provenance |
| `ops.snapshot_ingestion` | All | File status, row count, timestamps, and failure information |
| `mart.current_profile` table | Baseline | Current profile state consumed by Flask |
| `mart.profile` | Reference | Stable profile identity and latest display name |
| `mart.company` | Reference | Stable company identity and latest display name |
| `mart.profile_version` | Reference | SCD Type 2 company, title, and department state |
| `mart.current_profile` view | Reference | Compatibility projection over Reference tables |
| `mart.company_headcount` | All | Current active profile count grouped by company |

`raw.profile_snapshot` enforces uniqueness on `(snapshot_date, profile_id)`.

Database changes use ordered, versioned SQL migration files invoked through Python. Do not introduce an ORM migration framework.

### 6.3 Airflow DAG

The DAG:

- Has a daily schedule.
- Supports manual triggering.
- Has `catchup=False`.
- Produces useful task logs and actionable failure messages.
- Keeps orchestration code small enough for a candidate unfamiliar with Airflow to follow.

The Baseline DAG processes one configured Snapshot correctly. The Reference DAG discovers files matching the naming convention, excludes completed files, sorts the remainder by date, and processes them in chronological order.

Each Snapshot is one transaction covering raw insertion, model changes, quality checks, and ingestion completion. A failure rolls back all changes for that Snapshot and stops later files from processing. A completed Snapshot is immutable and skipped by later runs.

### 6.4 Flask Application

Use server-rendered Jinja templates and minimal JavaScript. The application is read-only and visually usable on desktop and mobile, but UI design is secondary to data-engineering behavior.

Baseline routes:

| Route | Behavior |
|---|---|
| `/` | Overview, available Snapshot information, and latest successful load |
| `/profiles` | Searchable current active profiles |
| `/companies` | Current active profile count by company |

Reference route:

| Route | Behavior |
|---|---|
| `/profiles/<profile_id>` | Profile display data and chronological Profile Version history |

Profile search is case-insensitive across full name, job title, department, and company name, and sorts by full name. Inactive profiles are absent from current search and headcount but remain accessible through history when directly addressed.

## 7. Data Quality

The working application checks:

- Required source columns exist.
- A Snapshot contains at least one row.
- `profile_id` is unique within a Snapshot.
- `is_active` values are recognized and parsed explicitly.
- Active rows contain required company, title, and department values.
- Modeled references are valid.
- Every active profile has exactly one current Profile Version and every inactive profile has none.
- Loaded and modeled volumes satisfy documented invariants.

A failed check must fail processing, not merely log an error. Checks required to accept a Snapshot execute before its transaction is committed.

## 8. Requested Changes

Candidate instructions describe these behaviors without prescribing exact files or code structure.

### RC1: Process Available Snapshots

Alter the DAG so one run discovers and processes all unprocessed dated Snapshot files in chronological order. Completed files must be skipped safely, a failed file must remain retryable, and later files must not process after a failure.

### RC2: Preserve Profile History

Evolve the current-state model to preserve company, job-title, and department changes as SCD Type 2 Profile Versions using the semantics in this specification. Preserve stable profile and company entities and retain `mart.current_profile` as a compatible current-state interface.

Candidate-facing wording should describe the required historical behavior and may identify it as SCD Type 2; recall of terminology is not itself the test.

### RC3: Optimize Profile Search

Improve the correct-but-slow current-profile search query. Results and ordering must remain unchanged. Candidates may rewrite SQL, add indexes, or alter schema. Improvement is judged from the PostgreSQL execution plan over deterministic generated data, not a machine-specific elapsed-time threshold.

### RC4: Show Profile History

Add the profile detail route and link current-profile search rows to it. The page displays the latest profile name and the profile's versions in chronological order, including company, title, department, and effective period.

## 9. Seeded Defects

Introduce defects only after Baseline and Reference acceptance tests pass. The Candidate Exercise contains exactly six, but candidate instructions state only that the existing application may contain defects relevant to completing the Requested Changes.

| ID | Seeded Defect | Intended symptom | Competency signal |
|---|---|---|---|
| SD1 | Flask's documented host port maps to the wrong container port | Candidate cannot reach the documented UI | Docker configuration and basic diagnosis |
| SD2 | DAG reads from an incorrect Snapshot path | Pipeline cannot locate input | Logs, configuration tracing, and path reasoning |
| SD3 | CSV loader parses non-empty Boolean strings by truthiness | `false` profiles remain active | Python data parsing and correctness |
| SD4 | Raw loading is non-idempotent | Rerun duplicates rows or fails uniqueness | Idempotency and transaction reasoning |
| SD5 | Company-headcount query joins at the wrong grain | Inflated company totals | SQL grain and cardinality |
| SD6 | The transactional processing step logs a data-quality failure but does not raise it | Green DAG with invalid data | Failure semantics and operational judgment |

Seeded Defects should be independent where practical. Fixing one must not reveal an answer list or automatically repair most others.

## 10. Testing

### 10.1 Baseline Acceptance

Automated tests must prove:

- The stack starts on supported architectures.
- One configured Snapshot loads successfully.
- Raw and current outputs match fixture expectations.
- A rerun does not duplicate or alter completed data.
- Invalid input fails clearly and rolls back.
- Baseline Flask routes render expected data.

### 10.2 Reference Acceptance

Automated tests must additionally prove:

- Unprocessed files are discovered and processed chronologically.
- Failure prevents later Snapshot processing.
- All Snapshot interpretation and Profile Version period rules hold.
- Display-name changes do not create Profile Versions.
- Explicit inactivation and reactivation behave correctly.
- Temporary absence does not close a version.
- `mart.current_profile` remains compatible.
- Search results are unchanged by optimization and its PostgreSQL plan is materially improved.
- Profile-history pages render correct chronological versions.

### 10.3 Candidate-Visible Tests

`docker compose run --rm tests` provides smoke checks for startup, rerun safety, and core model invariants. These tests are diagnostic aids and must not map one-to-one to Seeded Defects.

### 10.4 Private Verification

Authoritative behavioral tests live outside the Candidate Exercise because candidates may edit any repository file. Private checks cover every Requested Change and Seeded Defect by behavior, allowing alternative implementations that preserve required invariants.

## 11. Candidate README

The Candidate Exercise README includes:

- Plain-language description of periodic vendor Snapshots and derived SCD Type 2 history.
- Architecture and data-flow diagram.
- Prerequisites and supported platforms.
- Startup, Airflow trigger, test, reset, and submission commands.
- The four Requested Changes.
- Notice that existing defects may need repair, without count or locations.
- Statement that candidates may edit any file but should avoid unnecessary rewrites.
- Statement that AI use is permitted but every submitted change must be explainable.
- Three-calendar-day return window, untimed-work framing, and extension route.
- Environment-support contact and support boundary.

Do not require a `NOTES.md` or other written report.

## 12. Interviewer Guide

Create a private document not present in the Candidate Exercise or reachable Git history. It is a practical briefing, not a scoring rubric.

It must include:

1. A one-page explanation of the scenario, architecture, and expected data flow.
2. A concise glossary for Snapshot, Profile Version, SCD Type 2, idempotency, join fan-out, DAG dependency, and silent success.
3. Baseline and Reference table shapes and expected fixture states.
4. Each Requested Change's purpose, likely files, expected behavior, acceptable alternatives, and common misunderstandings.
5. Each Seeded Defect's symptom, root cause, expected repair behavior, likely candidate changes, and ways to verify it.
6. A compact SCD Type 2 before-and-after example with expected dates.
7. A pre-panel procedure: inspect the diff and commits, optionally start the stack, run private checks, inspect Airflow, and inspect Flask.
8. A walkthrough sequence: overall approach, one Requested Change, one Seeded Defect, SCD Type 2 behavior, validation, and unfinished work.
9. Productive primary questions and follow-ups, including what technically strong or concerning answers may reveal.
10. Guidance for recognizing valid alternative implementations rather than matching a canonical diff.
11. Reminder that inability to explain material submitted code is concerning even when the code works.
12. No numerical scores, competency grades, completion tally, or automatic rejection based on partial completion.

When a candidate misses a Seeded Defect, an interviewer may present its symptom hypothetically and ask how the candidate would investigate it. Do not disclose the full defect list during the interview.

## 13. Candidate Exercise Production

1. Build and test the Baseline Application.
2. Implement and test all Requested Changes to create the private Reference Application.
3. Produce the Candidate Exercise from Baseline source, add Requested Change instructions, then introduce each Seeded Defect separately.
4. Run private verification to prove each defect is present and each expected repair is behaviorally testable.
5. Create candidate repositories from a clean history containing no Reference Application, private tests, defect catalog, or Interviewer Guide.
6. Trial the exercise with at least one engineer who did not build it on both Windows and macOS before use.

## 14. Support Policy

Provide help for Docker installation, repository access, and genuinely unsupported platform behavior. Do not diagnose the intentionally incorrect port, paths, application code, SQL, or other repository defects. Record substantive hints given to a candidate so interviewers have context.

## 15. Acceptance Criteria

The project is ready for candidates when:

- Baseline and Reference acceptance suites pass from clean checkouts.
- Startup, tests, and reset work on supported Windows and macOS environments.
- Fixtures deterministically demonstrate all domain cases.
- Every Seeded Defect has an observable symptom and independent private verification.
- The Candidate Exercise history contains no private implementation or explanatory material.
- Candidate instructions are sufficient without revealing defect locations or count.
- The Flask UI makes correct and incorrect output visually inspectable without diagnosing it for the candidate.
- An interviewer unfamiliar with the project can use the private guide to understand a submission and ask informed follow-up questions.

## 16. Deferred Operational Decisions

These do not block implementation design:

- Exact process and owner for provisioning fresh private GitHub repositories.
- Minimum Docker resource figures, to be measured from the working stack.
- Final accessibility and accommodation wording approved for candidate communications.
