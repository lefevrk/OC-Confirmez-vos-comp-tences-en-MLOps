"""FastAPI lifespan composition root."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from api.infra.config import get_settings
from api.infra.logging import configure_logging
from api.infra.mlflow_model import load_champion


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load all external serving dependencies before accepting traffic."""
    configure_logging()
    app.state.settings = None
    app.state.model = None
    app.state.startup_error = None

    try:
        app.state.settings = get_settings()
    except Exception as exc:
        app.state.startup_error = str(exc)
        logger.bind(error=str(exc)).error("startup_settings_invalid")
    else:
        configure_logging(level=app.state.settings.log_level)
        try:
            app.state.model = load_champion(app.state.settings)
        except Exception as exc:
            app.state.startup_error = str(exc)
            logger.bind(error=str(exc)).error("startup_model_load_failed")

    yield
