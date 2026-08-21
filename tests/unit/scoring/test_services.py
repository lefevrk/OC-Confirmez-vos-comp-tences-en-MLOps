"""Unit tests for dependency-free scoring behavior."""

from typing import Any

from loguru import logger
import pytest

from api.modules.scoring.domain.errors import InvalidProbabilityError
from api.modules.scoring.services.predict import predict


class FakeModel:
    """Deterministic in-memory scoring model."""

    version = "3"
    threshold = 0.7

    def __init__(self, probability: float = 0.8) -> None:
        """Store the probability this fake model always returns."""
        self._probability = probability

    def probability(self, features: dict[str, Any]) -> float:
        """Return the configured probability."""
        del features
        return self._probability


def test_predict_applies_the_model_threshold() -> None:
    """The use case produces both probability and decision."""
    result = predict(FakeModel(probability=0.8), {"feature": 1.0})
    assert result.prediction_id
    assert result.probability == 0.8
    assert result.decision == 1
    assert result.model_version == "3"
    assert result.inference_latency_ms >= 0


def test_predict_rejects_a_probability_outside_the_valid_range() -> None:
    """A model returning a value outside [0, 1] is a hard failure, not a silent decision."""
    with pytest.raises(InvalidProbabilityError):
        predict(FakeModel(probability=1.5), {"feature": 1.0})


def test_predict_logs_the_completed_scoring_event() -> None:
    """A successful prediction emits a bound, structured log record."""
    records: list[str] = []
    sink_id = logger.add(lambda message: records.append(message.record["message"]), level="INFO")
    try:
        predict(FakeModel(probability=0.8), {"feature": 1.0})
    finally:
        logger.remove(sink_id)

    assert "scoring_completed" in records


def test_predict_binds_the_same_prediction_id_across_its_log_lines() -> None:
    """The started and completed events correlate to the same returned prediction_id."""
    prediction_ids: list[str] = []
    sink_id = logger.add(
        lambda message: prediction_ids.append(message.record["extra"]["prediction_id"]),
        level="DEBUG",
    )
    try:
        result = predict(FakeModel(probability=0.8), {"feature": 1.0})
    finally:
        logger.remove(sink_id)

    assert set(prediction_ids) == {result.prediction_id}


def test_predict_gives_identical_inputs_the_same_fingerprint_but_different_ids() -> None:
    """input_hash is deterministic for a given payload; prediction_id never is."""
    model = FakeModel(probability=0.8)
    features = {"feature": 1.0}
    fingerprints: list[str] = []
    sink_id = logger.add(
        lambda message: fingerprints.append(message.record["extra"]["input_hash"]),
        level="INFO",
    )
    try:
        first = predict(model, features)
        second = predict(model, features)
    finally:
        logger.remove(sink_id)

    assert first.prediction_id != second.prediction_id
    assert fingerprints == [fingerprints[0], fingerprints[0]]
