"""Prediction use case with no FastAPI or MLflow dependency."""

import hashlib
import json
from time import perf_counter
from typing import Any
import uuid

from loguru import logger

from api.modules.scoring.domain.entities import Prediction
from api.modules.scoring.domain.errors import InvalidProbabilityError
from api.modules.scoring.ports.model import ScoringModel


def _fingerprint(features: dict[str, Any]) -> str:
    """Return a short, one-way fingerprint of a feature payload — never the values."""
    raw = json.dumps(features, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def predict(model: ScoringModel, features: dict[str, Any]) -> Prediction:
    """Score a validated payload using the already-loaded model."""
    prediction_id = str(uuid.uuid4())
    bound = logger.bind(
        prediction_id=prediction_id,
        input_hash=_fingerprint(features),
        feature_count=len(features),
    )
    bound.debug("scoring_started")
    started = perf_counter()
    probability = model.probability(features)
    inference_latency_ms = (perf_counter() - started) * 1_000

    if not 0 <= probability <= 1:
        bound.bind(probability=probability).warning("invalid_probability_returned")
        raise InvalidProbabilityError("The model must return a probability between 0 and 1")

    prediction = Prediction(
        prediction_id=prediction_id,
        probability=probability,
        decision=int(probability >= model.threshold),
        model_version=model.version,
        inference_latency_ms=inference_latency_ms,
    )
    bound.bind(
        probability=prediction.probability,
        decision=prediction.decision,
        model_version=prediction.model_version,
        inference_latency_ms=round(inference_latency_ms, 2),
    ).info("scoring_completed")
    return prediction
