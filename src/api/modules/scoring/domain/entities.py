"""Small, framework-independent scoring objects."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Prediction:
    """A completed scoring decision."""

    prediction_id: str
    probability: float
    decision: int
    model_version: str
    inference_latency_ms: float


@dataclass(frozen=True)
class PredictionEvent:
    """One scoring attempt's outcome, persisted whether it succeeded or not.

    ``probability``, ``decision`` and ``inference_latency_ms`` are only ever
    unset when the model itself never returned a value (an unexpected crash);
    an out-of-range probability still records what the model returned.
    """

    prediction_id: str
    model_version: str
    status: Literal["success", "error"]
    probability: float | None
    decision: int | None
    inference_latency_ms: float | None
    error_code: str | None
