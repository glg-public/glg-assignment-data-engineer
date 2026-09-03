import psycopg2

from profile_pipeline.config import database_url
from profile_pipeline.snapshot import process_snapshot, read_snapshot
from profile_pipeline.web import create_app


def scalar(cursor):
    row = cursor.fetchone()
    assert row is not None
    return row[0]


def test_snapshot_workflow(clean_database, first_snapshot):
    rows = read_snapshot(first_snapshot)
    assert len(rows) == 20

    process_snapshot(first_snapshot)

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM raw.profile_snapshot")
            assert scalar(cursor) == 20
            cursor.execute("SELECT count(*) FROM mart.current_profile")
            assert scalar(cursor) == 20


def test_published_data_is_visible(clean_database, first_snapshot):
    process_snapshot(first_snapshot)
    client = create_app().test_client()

    assert client.get("/").status_code == 200
    assert b"Avery Chen" in client.get("/profiles?q=Avery").data
    assert b"Northstar Analytics" in client.get("/companies").data
