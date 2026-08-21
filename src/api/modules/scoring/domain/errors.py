"""Business errors deliberately safe to return as HTTP details."""


class ScoringError(Exception):
    """Base class for scoring domain errors."""


class InvalidProbabilityError(ScoringError):
    """Raised when a scoring model returns a value outside the probability range."""
