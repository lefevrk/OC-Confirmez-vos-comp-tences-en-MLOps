"""Operational liveness and readiness routes."""

from fastapi import APIRouter, Request, Response, status
from loguru import logger

from api.modules.health.schemas import HealthResponse, ReadinessChecks, ReadinessResponse

router = APIRouter(tags=["operations"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report process liveness without checking dependencies."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadinessResponse)
def ready(request: Request, response: Response) -> ReadinessResponse:
    """Report whether the startup-loaded model is available."""
    model_status = "ok" if request.app.state.model is not None else "error"

    if model_status == "ok":
        return ReadinessResponse(status="ready", checks=ReadinessChecks(model="ok"))

    logger.bind(model=model_status).warning("readiness_check_degraded")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="degraded", checks=ReadinessChecks(model=model_status))
