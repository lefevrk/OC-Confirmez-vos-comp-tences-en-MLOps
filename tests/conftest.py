"""Shared test configuration: isolated settings and a real, ephemeral PostgreSQL."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from testcontainers.community.postgres import PostgresContainer

REPO_ROOT = Path(__file__).resolve().parent.parent

_postgres_container: PostgresContainer | None = None


def pytest_configure() -> None:
    """Provide isolated MLflow settings and a real, migrated PostgreSQL instance.

    A container per test session — not a mock or SQLite — so the adapter and
    the Alembic migration it depends on are both exercised for real.
    """
    os.environ.setdefault("MLFLOW_TRACKING_URI", "https://mlflow.invalid")
    os.environ.setdefault("MLFLOW_TRACKING_USERNAME", "test")
    os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", "test")

    global _postgres_container
    _postgres_container = PostgresContainer("postgres:16-alpine")
    _postgres_container.start()
    database_url = _postgres_container.get_connection_url()
    os.environ["DATABASE_URL"] = database_url

    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def pytest_unconfigure() -> None:
    """Stop the ephemeral PostgreSQL instance once the whole test session ends."""
    if _postgres_container is not None:
        _postgres_container.stop()
