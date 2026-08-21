FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --extra api --no-install-project --no-dev

ENV PATH="/app/.venv/bin:$PATH"

RUN groupadd --system api \
    && useradd --system --gid api --home-dir /app --no-create-home api \
    && chown --recursive api:api /app

USER api

EXPOSE 8000

CMD ["python", "--version"]
