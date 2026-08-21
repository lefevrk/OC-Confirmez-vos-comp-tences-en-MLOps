"""Self-registering base class translating module domain errors into HTTP responses."""

from __future__ import annotations

from typing import ClassVar

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class BaseModuleErrorHandler:
    """Base class for module-level exception handlers registered with FastAPI.

    Subclasses declare a ``base_exception`` (the module's domain error
    hierarchy) and a ``status_map`` (exception type -> (status code, detail)),
    and are auto-registered via ``register_all``.
    """

    _registry: ClassVar[list[type[BaseModuleErrorHandler]]] = []
    base_exception: ClassVar[type[Exception]]
    status_map: ClassVar[dict[type[Exception], tuple[int, str]]]

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Add each new subclass to the global handler registry."""
        super().__init_subclass__(**kwargs)
        BaseModuleErrorHandler._registry.append(cls)

    @classmethod
    async def handle(cls, request: Request, exc: Exception) -> JSONResponse:
        """Convert a domain exception into a JSON error response."""
        status_code, detail = cls.status_map.get(
            type(exc), (status.HTTP_500_INTERNAL_SERVER_ERROR, "internal server error")
        )
        return JSONResponse(status_code=status_code, content={"detail": detail})

    @classmethod
    def register_all(cls, app: FastAPI) -> None:
        """Register every discovered handler subclass on the FastAPI application."""
        for handler_cls in cls._registry:
            app.add_exception_handler(handler_cls.base_exception, handler_cls.handle)
