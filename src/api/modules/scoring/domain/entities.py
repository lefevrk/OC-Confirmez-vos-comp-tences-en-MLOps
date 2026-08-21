"""Small, framework-independent scoring objects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Prediction:
    """A completed scoring decision."""

    prediction_id: str
    probability: float
    decision: int
    model_version: str
    inference_latency_ms: float
