"""Response schemas for operational endpoints."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness response."""

    status: Literal["ok"]


class ReadinessChecks(BaseModel):
    """Dependency states used to explain readiness failures."""

    model: Literal["ok", "error"]


class ReadinessResponse(BaseModel):
    """Readiness response."""

    status: Literal["ready", "degraded"]
    checks: ReadinessChecks
