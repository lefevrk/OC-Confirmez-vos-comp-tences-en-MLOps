"""Integration-only test configuration: a real, ephemeral, migrated PostgreSQL instance.

Only tests under tests/integration/ pay for this — tests/conftest.py provides a
placeholder DATABASE_URL for everything else so Settings() can build without Docker.
"""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from testcontainers.community.postgres import PostgresContainer

REPO_ROOT = Path(__file__).resolve().parents[2]

_postgres_container: PostgresContainer | None = None


def pytest_configure() -> None:
    """Start a real, migrated PostgreSQL container before any integration test runs."""
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
