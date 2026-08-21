"""Unit tests for the self-registering module exception handler base class."""

import asyncio
import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.common.error_handling import BaseModuleErrorHandler


class DummyError(Exception):
    """A throwaway domain error, local to this test module."""


class DummyHandler(BaseModuleErrorHandler):
    """A throwaway handler exercising the base class without touching real modules."""

    base_exception = DummyError
    status_map = {DummyError: (418, "teapot")}


def test_register_all_wires_a_mapped_domain_error_to_its_status_and_detail(monkeypatch) -> None:
    """A subclass registered via register_all translates its mapped error end to end."""
    monkeypatch.setattr(BaseModuleErrorHandler, "_registry", [DummyHandler])
    app = FastAPI()

    @app.get("/boom")
    def boom() -> None:
        raise DummyError

    BaseModuleErrorHandler.register_all(app)

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 418
    assert response.json() == {"detail": "teapot"}


def test_handle_falls_back_to_a_generic_500_for_an_unmapped_exception() -> None:
    """An exception subclassing base_exception but missing from status_map still resolves."""

    class UnmappedError(DummyError):
        """A DummyError subtype the handler was never told about."""

    response = asyncio.run(DummyHandler.handle(None, UnmappedError()))  # type: ignore[arg-type]

    assert response.status_code == 500
    assert json.loads(bytes(response.body)) == {"detail": "internal server error"}
