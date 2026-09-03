import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task

from profile_pipeline.snapshot import process_snapshot


@dag(
    dag_id="profile_snapshot",
    schedule="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=10)},
    tags=["case-study"],
)
def profile_snapshot_dag():
    @task
    def load_configured_snapshot() -> str:
        path = Path(os.environ["SNAPSHOT_FILE"])
        return process_snapshot(path)

    load_configured_snapshot()


profile_snapshot_dag()
