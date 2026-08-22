"""Integration tests for the POST /predictions endpoint."""

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete, select
from tests.payloads import valid_payload

from api.app import app
import api.infra.config as config_module
from api.infra.config import get_settings
from api.infra.postgres.models import PredictionEventRecord
from api.infra.postgres.tracking import PostgresPredictionRecorder
from api.modules.scoring.presentation.schemas import PredictionRequest


class DeterministicModel:
    """A startup model returning a fixed, valid probability."""

    version = "3"
    threshold = 0.5

    def probability(self, _features: dict[str, float | int | str]) -> float:
        """Return a fixed positive-class probability."""
        return 0.8


class FakeRecorder:
    """A prediction recorder connected without touching real storage."""

    def record(self, _event: object, _features: dict[str, float | int | str]) -> None:
        """Accept the event without persisting it."""


class FailingRecorder(FakeRecorder):
    """A recorder simulating a storage failure while handling a request."""

    def record(self, _event: object, _features: dict[str, float | int | str]) -> None:
        """Simulate a write failure after the model has already scored."""
        raise RuntimeError("storage unavailable")


@pytest.fixture(autouse=True)
def _model_loaded(monkeypatch) -> None:
    monkeypatch.setattr("api.bootstrap.load_champion", lambda _settings: DeterministicModel())


@pytest.fixture(autouse=True)
def _recorder_connected(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.bootstrap.connect_prediction_recorder", lambda _settings: FakeRecorder()
    )


def test_prediction_is_unavailable_when_startup_model_loading_fails(monkeypatch) -> None:
    """Reject predictions when no model was loaded during application startup."""
    monkeypatch.setattr(
        "api.bootstrap.load_champion", lambda _settings: (_ for _ in ()).throw(RuntimeError())
    )
    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 503
    assert response.json() == {"detail": "model unavailable"}


def test_prediction_is_unavailable_when_startup_postgres_connection_fails(monkeypatch) -> None:
    """Reject predictions when the database was not connected during application startup."""
    monkeypatch.setattr(
        "api.bootstrap.connect_prediction_recorder",
        lambda _settings: (_ for _ in ()).throw(RuntimeError()),
    )
    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 503
    assert response.json() == {"detail": "storage unavailable"}


def test_prediction_returns_a_generic_500_when_persistence_fails(monkeypatch) -> None:
    """A recorder available at startup can still fail mid-request; that must not be silent."""
    monkeypatch.setattr(
        "api.bootstrap.connect_prediction_recorder", lambda _settings: FailingRecorder()
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 500
    assert response.json() == {"detail": "internal server error"}


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


def test_prediction_persists_to_a_real_database(monkeypatch) -> None:
    """A successful prediction is readable back from the real, migrated PostgreSQL instance."""
    recorder = PostgresPredictionRecorder(
        get_settings().database_url, model_name="credit_scoring", model_alias="champion"
    )
    monkeypatch.setattr("api.bootstrap.connect_prediction_recorder", lambda _settings: recorder)

    with TestClient(app) as client:
        response = client.post("/predictions", json=valid_payload())
    assert response.status_code == 200
    prediction_id = response.json()["prediction_id"]

    with recorder.engine.connect() as connection:
        row = connection.execute(
            select(PredictionEventRecord).where(
                PredictionEventRecord.prediction_id == prediction_id
            )
        ).one()
    with recorder.engine.begin() as connection:
        connection.execute(delete(PredictionEventRecord))

    assert row.prediction_id == prediction_id
    assert row.probability == pytest.approx(0.8)
    assert row.decision == 1
    assert row.model_version == "3"
    assert row.inference_latency_ms is not None
    assert row.features == PredictionRequest.model_validate(valid_payload()).model_features()


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
