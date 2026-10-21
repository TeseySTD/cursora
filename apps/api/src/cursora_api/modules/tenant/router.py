"""HTTP layer of the tenant module: request/response mapping only, no business logic."""

from fastapi import APIRouter

router = APIRouter(prefix="/tenant", tags=["tenant"])
