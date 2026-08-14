# Image API — seule image exigée par le brief.
# Pas de modèle embarqué (fetch réseau depuis le MLflow Registry au démarrage,
# voir src/api/bootstrap.py) et pas de dépendances d'entraînement/notebooks.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --extra api --no-install-project --no-dev

COPY src/api ./src/api
COPY configs ./configs
RUN uv sync --extra api --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN groupadd --system api \
    && useradd --system --gid api --home-dir /app --no-create-home api \
    && chown --recursive api:api /app

USER api

# Hugging Face Spaces (Docker SDK) exposes a single port.
EXPOSE 7860

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860"]
