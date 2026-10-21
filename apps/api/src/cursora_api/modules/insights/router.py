"""HTTP layer of the insights module: request/response mapping only, no business logic."""

from fastapi import APIRouter

router = APIRouter(prefix="/insights", tags=["insights"])
