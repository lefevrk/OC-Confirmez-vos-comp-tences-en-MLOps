"""FastAPI application entry point."""

from fastapi import FastAPI

from api.bootstrap import lifespan
from api.modules.health.router import router as health_router

app = FastAPI(title="Credit scoring API", lifespan=lifespan)
app.include_router(health_router)
