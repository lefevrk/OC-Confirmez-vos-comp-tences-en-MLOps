"""Unit tests for environment-backed settings."""

from pydantic import ValidationError
import pytest

import api.infra.config as config_module
from api.infra.config import Settings, get_settings


def test_settings_requires_mlflow_credentials() -> None:
    """Startup must fail fast when MLflow connection details are missing."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]


def test_settings_defaults_disable_authentication_and_debug_logging() -> None:
    """Local development stays open by default: no token, INFO-level logging."""
    settings = Settings(
        _env_file=None,  # type: ignore[call-arg]
        mlflow_tracking_uri="https://mlflow.example",
        mlflow_tracking_username="username",
        mlflow_tracking_password="password",
    )
    assert settings.api_token == ""
    assert settings.log_level == "INFO"
    assert settings.model_name == "credit_scoring"
    assert settings.model_alias == "champion"


def test_get_settings_caches_a_single_instance(monkeypatch) -> None:
    """The process-wide settings are only built once."""
    monkeypatch.setattr(config_module, "_settings", None)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "https://mlflow.example")
    monkeypatch.setenv("MLFLOW_TRACKING_USERNAME", "username")
    monkeypatch.setenv("MLFLOW_TRACKING_PASSWORD", "password")

    first = get_settings()
    second = get_settings()

    assert first is second
