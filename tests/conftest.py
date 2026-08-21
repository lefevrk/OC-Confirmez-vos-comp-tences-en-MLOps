"""Shared test configuration for infrastructure settings."""

import os


def pytest_configure() -> None:
    """Provide isolated MLflow settings when tests run without a local .env file."""
    os.environ.setdefault("MLFLOW_TRACKING_URI", "https://mlflow.invalid")
    os.environ.setdefault("MLFLOW_TRACKING_USERNAME", "test")
    os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", "test")
