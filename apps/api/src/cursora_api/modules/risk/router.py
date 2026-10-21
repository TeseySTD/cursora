"""HTTP layer of the risk module: request/response mapping only, no business logic."""

from fastapi import APIRouter

router = APIRouter(prefix="/risk", tags=["risk"])
