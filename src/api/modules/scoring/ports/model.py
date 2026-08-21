"""Port describing an in-memory scorer."""

from typing import Any, Protocol


class ScoringModel(Protocol):
    """A model already loaded during application startup."""

    @property
    def version(self) -> str:
        """Return the immutable registered model version."""
        ...

    @property
    def threshold(self) -> float:
        """Return the immutable binary decision threshold."""
        ...

    def probability(self, features: dict[str, Any]) -> float:
        """Return the positive-class probability without external I/O."""
        ...
