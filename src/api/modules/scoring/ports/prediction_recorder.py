"""Port for durable prediction-event recording."""

from typing import Any, Protocol

from api.modules.scoring.domain.entities import PredictionEvent


class PredictionRecorder(Protocol):
    """Persists a scoring attempt's outcome and the features that produced it."""

    def record(self, event: PredictionEvent, features: dict[str, Any]) -> None:
        """Persist one prediction event, successful or not."""
        ...
