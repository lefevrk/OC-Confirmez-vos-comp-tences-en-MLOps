"""Shared test configuration: cheap environment defaults available to every test."""

import os


def pytest_configure() -> None:
    """Provide placeholder settings so Settings() can build without touching Docker.

    Real infrastructure — a migrated, ephemeral PostgreSQL instance — is
    provisioned lazily, only for tests under tests/integration/. See
    tests/integration/conftest.py.
    """
    os.environ.setdefault("MLFLOW_TRACKING_URI", "https://mlflow.invalid")
    os.environ.setdefault("MLFLOW_TRACKING_USERNAME", "test")
    os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", "test")
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://placeholder:placeholder@localhost:5432/placeholder"
    )
