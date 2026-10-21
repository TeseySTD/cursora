"""Application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from cursora_api.api_router import OPENAPI_TAGS, api_router
from cursora_api.core.config import Settings, get_settings
from cursora_api.core.db import create_engine, create_sessionmaker
from cursora_api.core.logging import configure_logging
from cursora_api.health import router as health_router


def _operation_id(route: APIRoute) -> str:
    # Stable, readable operationIds -> readable names in the generated TS client.
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}_{route.name}"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    engine = create_engine(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Cursora API",
        version="0.1.0",
        openapi_tags=OPENAPI_TAGS,
        generate_unique_id_function=_operation_id,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.engine = engine
    app.state.sessionmaker = create_sessionmaker(engine)

    app.include_router(health_router)
    app.include_router(api_router, prefix="/v1")
    return app
