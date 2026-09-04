from pathlib import Path

import psycopg2
import pytest

from profile_pipeline.config import database_url
from profile_pipeline.migrations import run_migrations


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    run_migrations()


@pytest.fixture()
def clean_database():
    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE raw.profile_snapshot, ops.snapshot_ingestion, mart.current_profile"
            )
    yield


@pytest.fixture()
def first_snapshot() -> Path:
    return Path("/app/data/snapshots/profiles_2026-01-15.csv")


@pytest.fixture()
def snapshot_directory() -> Path:
    return Path("/app/data/snapshots")
