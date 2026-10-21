"""HTTP layer of the gate module: request/response mapping only, no business logic."""

from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/gate", tags=["gate"])


@router.get(
    "/check",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def check() -> Response:
    """Nginx ``auth_request`` target for protected routes.

    Nginx treats 2xx as "let the request through" and 401/403 as "deny".
    This stub always allows.

    TODO(team): decide the response codes (and any headers) for the
    ``challenge_required`` and ``blocked`` outcomes, and how Nginx maps them
    (error_page / redirect to the challenge). Until then: always 204.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)
