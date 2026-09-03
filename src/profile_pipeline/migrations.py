import hashlib
import os
from pathlib import Path

import psycopg2

from profile_pipeline.config import database_url


def run_migrations() -> None:
    migrations_dir = Path(os.environ.get("MIGRATIONS_DIR", "/app/migrations"))
    files = sorted(migrations_dir.glob("*.sql"))
    if not files:
        raise RuntimeError(f"No migrations found in {migrations_dir}")

    with psycopg2.connect(database_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext('profile_pipeline_migrations'))")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS public.schema_migration (
                    filename text PRIMARY KEY,
                    checksum text,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
            cursor.execute(
                "ALTER TABLE public.schema_migration ADD COLUMN IF NOT EXISTS checksum text"
            )
            cursor.execute("SELECT filename, checksum FROM public.schema_migration")
            applied = dict(cursor.fetchall())

            for path in files:
                sql = path.read_text()
                checksum = hashlib.sha256(sql.encode()).hexdigest()
                if path.name in applied:
                    if applied[path.name] not in (None, checksum):
                        raise RuntimeError(f"Applied migration changed: {path.name}")
                    if applied[path.name] is None:
                        raise RuntimeError(
                            f"Applied migration has no checksum: {path.name}; reset the database"
                        )
                    continue
                cursor.execute(sql)
                cursor.execute(
                    "INSERT INTO public.schema_migration (filename, checksum) VALUES (%s, %s)",
                    (path.name, checksum),
                )


if __name__ == "__main__":
    run_migrations()
