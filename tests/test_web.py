from profile_pipeline.snapshot import process_snapshot
from profile_pipeline.web import create_app


def test_baseline_pages_render_loaded_data(clean_database, first_snapshot):
    process_snapshot(first_snapshot)
    client = create_app().test_client()

    overview = client.get("/")
    profiles = client.get("/profiles?q=Northstar")
    companies = client.get("/companies")

    assert overview.status_code == 200
    assert b"20" in overview.data
    assert b"profiles_2026-02-15.csv" in overview.data
    assert b"Latest successful load" in overview.data
    assert profiles.status_code == 200
    assert b"Avery Chen" in profiles.data
    assert b"Jordan Okafor" not in profiles.data
    assert companies.status_code == 200
    assert b"Northstar Analytics" in companies.data


def test_health_checks_database(clean_database):
    response = create_app().test_client().get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}
