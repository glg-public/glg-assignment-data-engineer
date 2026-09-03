import os

import psycopg2

from profile_pipeline.config import database_url


def generate_profiles(count: int) -> None:
    if count < 1:
        raise ValueError("Profile count must be positive")

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM mart.current_profile WHERE profile_id LIKE 'PERF-%%'")
            cursor.execute(
                """
                INSERT INTO mart.current_profile (
                    profile_id, full_name, company_id, company_name,
                    job_title, department, is_active, snapshot_date
                )
                SELECT
                    'PERF-' || value,
                    'Generated Profile ' || lpad(value::text, 6, '0'),
                    'PERF-C' || (value %% 500),
                    'Generated Company ' || (value %% 500),
                    CASE WHEN value %% 997 = 0 THEN 'Specialist Cartographer'
                         ELSE 'Generated Analyst ' || (value %% 40) END,
                    'Generated Department ' || (value %% 20),
                    true,
                    DATE '2026-01-15'
                FROM generate_series(1, %s) AS value
                """,
                (count,),
            )


if __name__ == "__main__":
    generate_profiles(int(os.environ.get("PERFORMANCE_PROFILE_COUNT", "100000")))
