import csv
import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

from profile_pipeline.config import database_url


REQUIRED_COLUMNS = {
    "profile_id",
    "full_name",
    "company_id",
    "company_name",
    "job_title",
    "department",
    "is_active",
}
SNAPSHOT_FILENAME = re.compile(r"^profiles_(\d{4}-\d{2}-\d{2})\.csv$")
TRUE_VALUES = {"true", "1", "yes"}
FALSE_VALUES = {"false", "0", "no"}
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProfileRow:
    profile_id: str
    full_name: str
    company_id: str | None
    company_name: str | None
    job_title: str | None
    department: str | None
    is_active: bool


def parse_snapshot_date(path: Path) -> date:
    match = SNAPSHOT_FILENAME.match(path.name)
    if not match:
        raise ValueError(f"Invalid Snapshot filename: {path.name}")
    return date.fromisoformat(match.group(1))


def parse_boolean(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in TRUE_VALUES | FALSE_VALUES:
        raise ValueError(f"Unrecognized is_active value: {value!r}")
    return bool(normalized)


def read_snapshot(path: Path) -> list[ProfileRow]:
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        rows: list[ProfileRow] = []
        seen: set[str] = set()
        for line_number, source_row in enumerate(reader, start=2):
            profile_id = source_row["profile_id"].strip()
            full_name = source_row["full_name"].strip()
            if not profile_id or not full_name:
                raise ValueError(f"Line {line_number}: profile_id and full_name are required")
            if profile_id in seen:
                raise ValueError(f"Line {line_number}: duplicate profile_id {profile_id}")
            seen.add(profile_id)

            is_active = parse_boolean(source_row["is_active"])
            tracked = {
                name: source_row[name].strip()
                for name in ("company_id", "company_name", "job_title", "department")
            }
            if is_active and any(not value for value in tracked.values()):
                raise ValueError(
                    f"Line {line_number}: active profile {profile_id} has empty role fields"
                )

            rows.append(
                ProfileRow(
                    profile_id=profile_id,
                    full_name=full_name,
                    company_id=tracked["company_id"] or None,
                    company_name=tracked["company_name"] or None,
                    job_title=tracked["job_title"] or None,
                    department=tracked["department"] or None,
                    is_active=is_active,
                )
            )

    if not rows:
        raise ValueError("Snapshot contains no profile rows")
    return rows


def process_available_snapshots(path: Path) -> dict[str, str]:
    return {path.name: process_snapshot(path)}


def process_snapshot(path: Path) -> str:
    snapshot_date = parse_snapshot_date(path)
    logger.info("Starting Snapshot %s from %s", snapshot_date, path)

    try:
        with psycopg2.connect(database_url()) as connection:
            with connection.cursor() as cursor:
                logger.info("Waiting for ingestion lock")
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(hashtext('profile_snapshot_ingestion'))"
                )
                cursor.execute(
                    "SELECT status FROM ops.snapshot_ingestion WHERE snapshot_date = %s",
                    (snapshot_date,),
                )
                existing = cursor.fetchone()
                if existing and existing[0] == "completed":
                    logger.info("Reloading completed Snapshot %s", snapshot_date)

                cursor.execute(
                    "SELECT max(snapshot_date) FROM ops.snapshot_ingestion WHERE status = 'completed'"
                )
                latest_result = cursor.fetchone()
                latest_completed = latest_result[0] if latest_result else None
                if latest_completed and snapshot_date < latest_completed:
                    raise ValueError(
                        f"Snapshot {snapshot_date} is older than completed Snapshot {latest_completed}"
                    )

                rows = read_snapshot(path)
                active_count = sum(row.is_active for row in rows)
                logger.info(
                    "Validated %s rows: %s active, %s inactive",
                    len(rows),
                    active_count,
                    len(rows) - active_count,
                )

                cursor.execute(
                    "DELETE FROM ops.snapshot_ingestion WHERE snapshot_date = %s",
                    (snapshot_date,),
                )

                raw_values = [
                    (
                        snapshot_date,
                        row.profile_id,
                        row.full_name,
                        row.company_id,
                        row.company_name,
                        row.job_title,
                        row.department,
                        row.is_active,
                        path.name,
                    )
                    for row in rows
                ]
                execute_values(
                    cursor,
                    """
                    INSERT INTO raw.profile_snapshot (
                        snapshot_date, profile_id, full_name, company_id,
                        company_name, job_title, department, is_active, source_file
                    ) VALUES %s
                    """,
                    raw_values,
                )
                logger.info("Loaded %s raw rows", len(rows))

                execute_values(
                    cursor,
                    """
                    INSERT INTO mart.current_profile (
                        profile_id, full_name, company_id, company_name,
                        job_title, department, is_active, snapshot_date
                    ) VALUES %s
                    ON CONFLICT (profile_id) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        company_id = EXCLUDED.company_id,
                        company_name = EXCLUDED.company_name,
                        job_title = EXCLUDED.job_title,
                        department = EXCLUDED.department,
                        is_active = EXCLUDED.is_active,
                        snapshot_date = EXCLUDED.snapshot_date
                    """,
                    [
                        (
                            row.profile_id,
                            row.full_name,
                            row.company_id,
                            row.company_name,
                            row.job_title,
                            row.department,
                            row.is_active,
                            snapshot_date,
                        )
                        for row in rows
                    ],
                )
                logger.info("Published %s current profiles", len(rows))

                cursor.execute(
                    """
                    SELECT count(*)
                    FROM mart.current_profile
                    WHERE is_active AND (
                        company_id IS NULL OR company_name IS NULL
                        OR job_title IS NULL OR department IS NULL
                    )
                    """,
                )
                quality_result = cursor.fetchone()
                if quality_result is None:
                    raise RuntimeError("Data-quality query returned no result")
                if quality_result[0]:
                    raise ValueError("Active modeled profiles have empty role fields")

                cursor.execute(
                    "SELECT coalesce(sum(active_profiles), 0) FROM mart.company_headcount"
                )
                headcount_result = cursor.fetchone()
                published_headcount = headcount_result[0] if headcount_result else 0
                cursor.execute(
                    "SELECT count(*) FROM mart.current_profile WHERE is_active"
                )
                expected_result = cursor.fetchone()
                expected_headcount = expected_result[0] if expected_result else 0
                if published_headcount != expected_headcount:
                    logger.error(
                        "Data-quality check failed: published headcount=%s, expected=%s",
                        published_headcount,
                        expected_headcount,
                    )

                cursor.execute(
                    "SELECT count(*) FROM raw.profile_snapshot WHERE snapshot_date = %s",
                    (snapshot_date,),
                )
                raw_count_result = cursor.fetchone()
                if raw_count_result is None or raw_count_result[0] != len(rows):
                    raise ValueError("Raw row count does not match the source Snapshot")

                cursor.execute(
                    "SELECT count(*) FROM mart.current_profile WHERE snapshot_date = %s",
                    (snapshot_date,),
                )
                modeled_count_result = cursor.fetchone()
                if modeled_count_result is None or modeled_count_result[0] != len(rows):
                    raise ValueError("Modeled row count does not match the source Snapshot")
                logger.info(
                    "Data-quality checks passed: raw rows=%s, modeled rows=%s",
                    raw_count_result[0],
                    modeled_count_result[0],
                )

                cursor.execute(
                    """
                    INSERT INTO ops.snapshot_ingestion (
                        snapshot_date, source_file, status, row_count, completed_at
                    ) VALUES (%s, %s, 'completed', %s, now())
                    """,
                    (snapshot_date, path.name, len(rows)),
                )
                logger.info("Marked Snapshot %s completed", snapshot_date)
        logger.info("Committed Snapshot %s", snapshot_date)
        return "completed"
    except Exception as error:
        logger.exception("Snapshot %s failed: %s", snapshot_date, error)
        try:
            _record_failure(snapshot_date, path.name, str(error))
        except Exception:
            logger.exception("Could not record failed Snapshot %s", snapshot_date)
        raise


def _record_failure(snapshot_date: date, source_file: str, message: str) -> None:
    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext('profile_snapshot_ingestion'))"
            )
            cursor.execute(
                """
                INSERT INTO ops.snapshot_ingestion (
                    snapshot_date, source_file, status, completed_at, error_message
                ) VALUES (%s, %s, 'failed', now(), %s)
                ON CONFLICT (snapshot_date) DO UPDATE SET
                    source_file = EXCLUDED.source_file,
                    status = 'failed',
                    completed_at = now(),
                    error_message = EXCLUDED.error_message
                WHERE ops.snapshot_ingestion.status <> 'completed'
                """,
                (snapshot_date, source_file, message[:1000]),
            )
