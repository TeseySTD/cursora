# syntax=docker/dockerfile:1
# Cursora API image. Build context: repository root.

FROM ghcr.io/astral-sh/uv:0.13.4 AS uv

# ---- build: resolve and install the locked dependencies into /app/.venv ----
FROM python:3.15-slim-trixie AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv
WORKDIR /src

# Workspace manifests first (better layer caching): all members must exist for uv to resolve.
COPY pyproject.toml uv.lock .python-version ./
COPY apps/api/pyproject.toml apps/api/
COPY packages/features/pyproject.toml packages/features/
COPY ml/pyproject.toml ml/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package cursora-api --no-install-workspace

# Then the sources: only api + features (ml is not part of the API image).
COPY apps/api apps/api
COPY packages/features packages/features
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package cursora-api --no-editable

# ---- runtime: venv + migrations only, no uv, no sources ----
FROM python:3.15-slim-trixie AS runtime
RUN useradd --system --uid 10001 --home-dir /app cursora
WORKDIR /app
COPY --from=build /app/.venv /app/.venv
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/alembic ./alembic
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1
USER cursora
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn cursora_api.main:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*' --root-path /api"]
