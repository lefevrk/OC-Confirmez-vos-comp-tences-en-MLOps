"""Integration tests for the POST /predictions endpoint."""

from fastapi.testclient import TestClient
import pytest

from api.app import app
import api.infra.config as config_module
from api.modules.scoring.presentation.schemas import PredictionRequest


def valid_payload() -> dict[str, float | int | str]:
    """Build a payload containing every required model feature."""
    categorical_values = {
        "organization_type": "Bank",
        "code_gender": "F",
        "occupation_type": "Accountants",
        "name_family_status": "Married",
        "name_education_type": "Higher education",
    }
    integer_fields = {"days_birth", "days_id_publish"}

    return {
        field_name: categorical_values.get(field_name, -1 if field_name in integer_fields else 1.0)
        for field_name, field in PredictionRequest.model_fields.items()
        if field.is_required()
    }


class DeterministicModel:
    """A startup model returning a fixed, valid probability."""

    version = "3"
    threshold = 0.5

    def probability(self, _features: dict[str, float | int | str]) -> float:
        """Return a fixed positive-class probability."""
        return 0.8


@pytest.fixture(autouse=True)
def _model_loaded(monkeypatch) -> None:
    monkeypatch.setattr("api.bootstrap.load_champion", lambda _settings: DeterministicModel())


def test_prediction_is_unavailable_when_startup_model_loading_fails(monkeypatch) -> None:
    """Reject predictions when no model was loaded during application startup."""
    monkeypatch.setattr(
        "api.bootstrap.load_champion", lambda _settings: (_ for _ in ()).throw(RuntimeError())
    )
    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 503
    assert response.json() == {"detail": "model unavailable"}


def test_prediction_succeeds_without_a_token_when_authentication_is_disabled() -> None:
    """API_TOKEN empty (the default) leaves the endpoint open, for local development."""
    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["probability"] == 0.8
    assert body["decision"] == 1
    assert body["model_version"] == "3"
    assert body["prediction_id"]


def test_prediction_rejects_a_malformed_payload() -> None:
    """A payload missing a required field is rejected before scoring runs."""
    payload = valid_payload()
    del payload["payment_credit_ratio"]
    with TestClient(app) as client:
        response = client.post("/predictions", json=payload)
    assert response.status_code == 422


@pytest.fixture
def _token_required(monkeypatch):
    monkeypatch.setattr(config_module, "_settings", None)
    monkeypatch.setenv("API_TOKEN", "s3cret")
    yield "s3cret"
    monkeypatch.setattr(config_module, "_settings", None)


def test_prediction_requires_a_token_once_one_is_configured(_token_required) -> None:
    """A configured API_TOKEN turns the endpoint closed by default."""
    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 401


def test_prediction_rejects_an_incorrect_token(_token_required) -> None:
    """A wrong Bearer token is rejected, not silently ignored."""
    with TestClient(app) as client:
        response = client.post(
            "/predictions",
            json=valid_payload(),
            headers={"Authorization": "Bearer wrong-token"},
        )
    assert response.status_code == 401


def test_prediction_succeeds_with_the_correct_token(_token_required) -> None:
    """The right Bearer token grants access to the endpoint."""
    with TestClient(app) as client:
        response = client.post(
            "/predictions",
            json=valid_payload(),
            headers={"Authorization": f"Bearer {_token_required}"},
        )
    assert response.status_code == 200


def test_prediction_rejects_an_invalid_model_probability(monkeypatch) -> None:
    """A model returning a value outside [0, 1] fails loudly rather than deciding anyway."""

    class BrokenModel(DeterministicModel):
        """A misbehaving model returning an out-of-range probability."""

        def probability(self, _features: dict[str, float | int | str]) -> float:
            return 1.5

    monkeypatch.setattr("api.bootstrap.load_champion", lambda _settings: BrokenModel())
    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 500
    assert response.json() == {"detail": "prediction failed"}


def test_prediction_returns_a_generic_500_on_an_unexpected_model_error(monkeypatch) -> None:
    """An unforeseen model crash is logged and answered, not left to propagate raw."""

    class CrashingModel(DeterministicModel):
        """A model raising an error scoring never anticipates."""

        def probability(self, _features: dict[str, float | int | str]) -> float:
            raise RuntimeError("boom")

    monkeypatch.setattr("api.bootstrap.load_champion", lambda _settings: CrashingModel())
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}
