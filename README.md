# Professional Profile Pipeline

This repository contains a small data application used for a Data Operations Engineer take-home exercise.

## What The Application Does

A fictional vendor periodically provides a complete **Snapshot** of its professional-profile data as a dated CSV. The pipeline validates and retains the source rows, models the current profile state in PostgreSQL, and publishes the results through a Flask web application.

Later Snapshots can show that a profile has changed company, job title, or department. The intended extended model preserves those changes as **Slowly Changing Dimension Type 2** history: the incoming CSV files are Snapshots, while the derived profile history is the SCD Type 2 model. An explicit `is_active=false` closes a current profile; absence from one Snapshot does not imply inactivity.

```text
CSV Snapshot -> Airflow -> PostgreSQL -> Flask
```

## Prerequisites

- Git
- Docker Desktop with Docker Compose
- macOS on Apple Silicon or Intel, or Windows using WSL2

No host Python or PostgreSQL installation is required.

## Start The Application

From the repository root:

```console
docker compose up --build
```

Initial image downloads and Airflow setup may take several minutes. When startup completes:

- Flask: http://localhost:5050
- Airflow: http://localhost:8080
- Airflow username and password: `airflow` / `airflow`

In Airflow, open the `profile_snapshot` DAG, enable it if needed, and trigger a run. The baseline DAG processes `profiles_2026-01-15.csv`.

## Inspect The Results

The Flask application provides:

- `/`: pipeline overview and Snapshot loads
- `/profiles`: searchable current active profiles
- `/companies`: active profile counts by company

## Run Checks

With PostgreSQL running:

```console
docker compose run --rm tests
```

## Generate Query-Plan Data

The checked-in Snapshots stay small enough to inspect manually. Generate a larger deterministic current-profile dataset when examining profile-search query plans:

```console
docker compose run --rm generate-performance-data
```

Generated profile IDs start with `PERF-`. Running the command again replaces prior generated rows.

## Reset Everything

```console
docker compose down --volumes
docker compose up --build
```

The first command permanently removes local case-study database and Airflow state.

## Troubleshooting

- Confirm Docker Desktop is running before invoking Docker Compose.
- Use `docker compose ps` to inspect service status.
- Use the Airflow task log to investigate pipeline failures.
- Use `docker compose logs web` to inspect Flask startup failures.

For the assignment requirements and submission guidance, see `CANDIDATE_INSTRUCTIONS.md`.
