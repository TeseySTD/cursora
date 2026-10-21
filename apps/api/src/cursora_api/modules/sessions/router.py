"""HTTP layer of the sessions module: request/response mapping only, no business logic."""

from fastapi import APIRouter

router = APIRouter(prefix="/sessions", tags=["sessions"])
