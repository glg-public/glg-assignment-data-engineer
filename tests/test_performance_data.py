import psycopg2

from profile_pipeline.config import database_url
from profile_pipeline.generate_performance_data import generate_profiles


def test_performance_data_generation_is_deterministic(clean_database):
    generate_profiles(100)
    generate_profiles(100)

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM mart.current_profile")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 100
            cursor.execute(
                "SELECT count(*) FROM mart.current_profile WHERE job_title = 'Specialist Cartographer'"
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 0
