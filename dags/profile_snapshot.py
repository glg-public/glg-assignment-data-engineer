import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task

from profile_pipeline.snapshot import process_available_snapshots


logger = logging.getLogger(__name__)


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
    def load_available_snapshots() -> dict[str, str]:
        path = Path(os.environ["SNAPSHOT_SOURCE"])
        logger.info("Configured Snapshot source: %s", path)
        result = process_available_snapshots(path)
        logger.info("Snapshot processing results: %s", result)
        return result

    load_available_snapshots()


profile_snapshot_dag()
