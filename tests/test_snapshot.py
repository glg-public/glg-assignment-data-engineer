from pathlib import Path

import psycopg2
import pytest

from profile_pipeline.config import database_url
from profile_pipeline.snapshot import parse_boolean, process_snapshot, read_snapshot


def scalar(cursor):
    row = cursor.fetchone()
    assert row is not None
    return row[0]


@pytest.mark.parametrize("value", ["true", "TRUE", "1", "yes"])
def test_parse_boolean_true(value):
    assert parse_boolean(value) is True


@pytest.mark.parametrize("value", ["false", "FALSE", "0", "no"])
def test_parse_boolean_false(value):
    assert parse_boolean(value) is False


def test_parse_boolean_rejects_unknown_value():
    with pytest.raises(ValueError, match="Unrecognized"):
        parse_boolean("sometimes")


def test_read_snapshot_rejects_duplicate_profile(tmp_path: Path):
    path = tmp_path / "profiles_2026-01-15.csv"
    path.write_text(
        "profile_id,full_name,company_id,company_name,job_title,department,is_active\n"
        "P1,One,C1,Company,Engineer,Tech,true\n"
        "P1,One Again,C1,Company,Engineer,Tech,true\n"
    )

    with pytest.raises(ValueError, match="duplicate profile_id P1"):
        read_snapshot(path)


def test_process_snapshot_loads_current_state(clean_database, first_snapshot):
    assert process_snapshot(first_snapshot) == "completed"

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM raw.profile_snapshot")
            assert scalar(cursor) == 20
            cursor.execute("SELECT count(*) FROM mart.current_profile WHERE is_active")
            assert scalar(cursor) == 20
            cursor.execute(
                "SELECT active_profiles FROM mart.company_headcount WHERE company_id = 'C001'"
            )
            assert scalar(cursor) == 2
            cursor.execute(
                """
                SELECT full_name, company_name, job_title, department, is_active
                FROM mart.current_profile
                WHERE profile_id = 'P001'
                """
            )
            assert cursor.fetchone() == (
                "Avery Chen",
                "Northstar Analytics",
                "Data Engineer",
                "Engineering",
                True,
            )
            cursor.execute(
                """
                SELECT profile_id, full_name, company_id, company_name,
                       job_title, department, is_active
                FROM raw.profile_snapshot
                ORDER BY profile_id
                """
            )
            raw_rows = cursor.fetchall()
            cursor.execute(
                """
                SELECT profile_id, full_name, company_id, company_name,
                       job_title, department, is_active
                FROM mart.current_profile
                ORDER BY profile_id
                """
            )
            assert cursor.fetchall() == raw_rows


def test_process_snapshot_is_idempotent(clean_database, first_snapshot):
    assert process_snapshot(first_snapshot) == "completed"
    assert process_snapshot(first_snapshot) == "skipped"

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM raw.profile_snapshot")
            assert scalar(cursor) == 20
            cursor.execute("SELECT count(*) FROM ops.snapshot_ingestion")
            assert scalar(cursor) == 1


def test_completed_snapshot_is_skipped_before_reading_file(
    clean_database, first_snapshot, tmp_path
):
    assert process_snapshot(first_snapshot) == "completed"
    unreadable_copy = tmp_path / first_snapshot.name
    unreadable_copy.write_text("not,a,valid,snapshot\n")

    assert process_snapshot(unreadable_copy) == "skipped"

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status, row_count FROM ops.snapshot_ingestion WHERE snapshot_date = '2026-01-15'"
            )
            assert cursor.fetchone() == ("completed", 20)


def test_database_failure_rolls_back_modeled_data(clean_database, first_snapshot):
    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw.profile_snapshot (
                    snapshot_date, profile_id, full_name, company_id, company_name,
                    job_title, department, is_active, source_file
                ) VALUES (
                    '2026-01-15', 'P001', 'Existing', 'C001', 'Existing Company',
                    'Existing Title', 'Existing Department', true, 'existing.csv'
                )
                """
            )

    with pytest.raises(psycopg2.errors.UniqueViolation):
        process_snapshot(first_snapshot)

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM mart.current_profile")
            assert scalar(cursor) == 0
            cursor.execute(
                "SELECT status FROM ops.snapshot_ingestion WHERE snapshot_date = '2026-01-15'"
            )
            assert scalar(cursor) == "failed"


def test_older_snapshot_cannot_overwrite_newer_state(clean_database):
    newer = Path("/app/data/snapshots/profiles_2026-02-15.csv")
    older = Path("/app/data/snapshots/profiles_2026-01-15.csv")
    assert process_snapshot(newer) == "completed"

    with pytest.raises(ValueError, match="older than completed Snapshot"):
        process_snapshot(older)

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT snapshot_date FROM mart.current_profile WHERE profile_id = 'P001'"
            )
            assert scalar(cursor).isoformat() == "2026-02-15"


def test_invalid_snapshot_records_failure_without_partial_data(clean_database, tmp_path):
    path = tmp_path / "profiles_2026-03-01.csv"
    path.write_text(
        "profile_id,full_name,company_id,company_name,job_title,department,is_active\n"
        "P1,Invalid Profile,C1,Company,Engineer,Tech,sometimes\n"
    )

    with pytest.raises(ValueError, match="Unrecognized"):
        process_snapshot(path)

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM raw.profile_snapshot")
            assert scalar(cursor) == 0
            cursor.execute(
                "SELECT status FROM ops.snapshot_ingestion WHERE snapshot_date = '2026-03-01'"
            )
            assert scalar(cursor) == "failed"
