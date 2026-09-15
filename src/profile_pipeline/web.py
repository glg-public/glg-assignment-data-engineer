import os
from pathlib import Path

from flask import Flask, abort, render_template, request
import psycopg2
from psycopg2.extras import RealDictCursor

from profile_pipeline.config import database_url


def query(sql: str, parameters: tuple = ()) -> list[dict]:
    with psycopg2.connect(database_url()) as connection:
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, parameters)
            return list(cursor.fetchall())


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def overview():
        loads = query(
            """
            SELECT snapshot_date, source_file, status, row_count, completed_at
            FROM ops.snapshot_ingestion
            ORDER BY snapshot_date DESC
            """
        )
        counts = query(
            """
            SELECT
                count(*) FILTER (WHERE is_active) AS active_profiles,
                count(*) FILTER (WHERE NOT is_active) AS inactive_profiles,
                count(DISTINCT company_id) FILTER (WHERE is_active) AS companies
            FROM mart.current_profile
            """
        )[0]
        latest_load = next((load for load in loads if load["status"] == "completed"), None)
        snapshot_dir = Path(os.environ.get("SNAPSHOT_DIR", "/app/data/snapshots"))
        available_files = sorted(path.name for path in snapshot_dir.glob("profiles_*.csv"))
        return render_template(
            "overview.html",
            loads=loads,
            counts=counts,
            latest_load=latest_load,
            available_files=available_files,
        )

    @app.get("/profiles")
    def profiles():
        search = request.args.get("q", "").strip()
        pattern = f"%{search}%"
        rows = query(
            """
            SELECT profile_id, full_name, company_name, job_title, department
            FROM mart.current_profile
            WHERE is_active
              AND (
                %s = '' OR full_name ILIKE %s OR company_name ILIKE %s
                OR job_title ILIKE %s OR department ILIKE %s
              )
            ORDER BY full_name, profile_id
            """,
            (search, pattern, pattern, pattern, pattern),
        )
        return render_template("profiles.html", profiles=rows, search=search)

    @app.get("/companies")
    def companies():
        rows = query(
            """
            SELECT cp.company_id, cp.company_name, count(*)::integer AS active_profiles
            FROM mart.current_profile cp
            JOIN raw.profile_snapshot raw
              ON raw.company_id = cp.company_id
            WHERE cp.is_active
            GROUP BY cp.company_id, cp.company_name
            ORDER BY active_profiles DESC, cp.company_name
            """
        )
        return render_template("companies.html", companies=rows)

    @app.get("/health")
    def health():
        try:
            query("SELECT 1 AS healthy")
        except psycopg2.Error:
            abort(503)
        return {"status": "ok"}

    return app
