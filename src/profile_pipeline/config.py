import os


def database_url() -> str:
    return os.environ.get(
        "APP_DATABASE_URL",
        "postgresql://case_study:case_study@localhost:5432/profile_data",
    )
