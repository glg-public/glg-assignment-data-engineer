import json
import os
from urllib.request import urlopen


def read_json(url: str) -> dict:
    with urlopen(url, timeout=5) as response:
        return json.load(response)


def test_flask_service_is_healthy():
    assert read_json(os.environ["WEB_HEALTH_URL"]) == {"status": "ok"}


def test_airflow_service_is_healthy():
    health = read_json(os.environ["AIRFLOW_HEALTH_URL"])
    assert health["metadatabase"]["status"] == "healthy"
    assert health["scheduler"]["status"] == "healthy"
