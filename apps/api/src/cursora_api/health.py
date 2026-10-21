"""Liveness and database health endpoints (mounted at the root, not under /v1)."""

import logging
from typing import Literal

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from cursora_api.core.db import SessionDep

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok", "unavailable"]


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe: the process is up. Does not touch the database."""
    return HealthResponse(status="ok")


@router.get(
    "/db",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthResponse}},
)
async def health_db(session: SessionDep, response: Response) -> HealthResponse:
    """Readiness of the database: runs ``SELECT 1``."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError, OSError:
        logger.exception("database health check failed")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(status="unavailable")
    return HealthResponse(status="ok")
