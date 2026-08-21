"""Infrastructure routes are available without an MLflow server."""

from fastapi.testclient import TestClient

from api.app import app


def test_liveness_does_not_require_dependencies(monkeypatch) -> None:
    """Health stays available when the model registry cannot be reached."""
    monkeypatch.setattr(
        "api.bootstrap.load_champion", lambda _settings: (_ for _ in ()).throw(RuntimeError())
    )
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/ready").status_code == 503


def test_readiness_reports_ready_once_the_model_is_loaded(monkeypatch) -> None:
    """Readiness succeeds once the startup model is available."""

    class Model:
        """Minimal startup model."""

    monkeypatch.setattr("api.bootstrap.load_champion", lambda _settings: Model())
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.json() == {"status": "ready", "checks": {"model": "ok"}}


def test_startup_reports_a_degraded_readiness_when_settings_are_invalid(monkeypatch) -> None:
    """A misconfigured environment fails startup without crashing the process."""
    monkeypatch.setattr(
        "api.bootstrap.get_settings", lambda: (_ for _ in ()).throw(RuntimeError("bad env"))
    )
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 503
