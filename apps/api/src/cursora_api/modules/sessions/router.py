"""HTTP layer of the sessions module: request/response mapping only, no business logic."""

from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError

from cursora_api.core.config import SettingsDep
from cursora_api.core.db import SessionDep
from cursora_api.modules.sessions.repository import SessionRepository
from cursora_api.modules.sessions.schemas import SessionRequest, SessionResponse, SignalBatchIn
from cursora_api.modules.sessions.service import (
    BatchTooLargeError,
    RateLimitedError,
    SessionInvalidError,
    SessionService,
    SignalLimits,
    SignalService,
    SiteNotFoundError,
)
from cursora_api.modules.tenant.service import TenantService

# Holds the session id. Never log or return its value.
SESSION_COOKIE = "cursora_session"

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service(db: SessionDep, settings: SettingsDep) -> SessionService:
    return SessionService(
        SessionRepository(db),
        TenantService.for_db(db),
        ttl=timedelta(seconds=settings.session_ttl_s),
    )


SessionServiceDep = Annotated[SessionService, Depends(get_session_service)]


def get_signal_service(db: SessionDep, settings: SettingsDep) -> SignalService:
    limits = SignalLimits(
        max_signals=settings.signal_batch_max_signals,
        rate_max_batches=settings.signal_rate_max_batches,
        rate_window=timedelta(seconds=settings.signal_rate_window_s),
    )
    return SignalService(SessionRepository(db), limits=limits)


SignalServiceDep = Annotated[SignalService, Depends(get_signal_service)]
SessionCookie = Annotated[str | None, Cookie(alias=SESSION_COOKIE)]


@router.post(
    "",
    response_model=SessionResponse,
    responses={
        status.HTTP_200_OK: {"description": "The live session from the cookie was reused."},
        status.HTTP_201_CREATED: {
            "model": SessionResponse,
            "description": "A new session was created and set in the cookie.",
        },
        status.HTTP_404_NOT_FOUND: {"description": "No site has this site key."},
    },
)
async def ensure_session(
    body: SessionRequest,
    response: Response,
    service: SessionServiceDep,
    settings: SettingsDep,
    session_id: SessionCookie = None,
) -> SessionResponse:
    """Restore the visitor's session on the site from the cookie, or create a new one.

    Called by the widget when a page with it loads, with the site key from its script tag.

    - 200: the cookie holds a live session of this site. It is reused as is, state included.
    - 201: no cookie, or its session is unknown, expired or of another site. A new session in
      state ``new`` is created and its id is set in an HttpOnly cookie that expires with it.
    - 404: no site has this site key.
    """
    try:
        session, created = await service.get_or_create(session_id, body.site_key)
    except SiteNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown site key") from None
    if created:
        response.status_code = status.HTTP_201_CREATED
        response.set_cookie(
            SESSION_COOKIE,
            session.id,
            expires=session.expires_at,
            path="/",
            secure=settings.session_cookie_secure,
            httponly=True,
            samesite=settings.session_cookie_samesite,
        )
    return SessionResponse(state=session.state, expires_at=session.expires_at)


class _BodyTooLargeError(Exception):
    pass


async def _read_body(request: Request, max_bytes: int) -> bytes:
    """The request body, read no further than ``max_bytes``.

    FastAPI would read the whole body into memory before validating it, whatever its size, so
    the batch is read here instead and a bot cannot make the API buffer a huge JSON document.
    """
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > max_bytes:
        raise _BodyTooLargeError
    body = bytearray()
    async for chunk in request.stream():
        body += chunk
        if len(body) > max_bytes:
            raise _BodyTooLargeError
    return bytes(body)


def _inline_json_schema(model: type[BaseModel]) -> dict[str, Any]:
    """The JSON schema of ``model`` with every ``$ref`` resolved in place.

    Pydantic puts nested models under ``$defs``, which an OpenAPI document cannot resolve
    inside ``openapi_extra``. Inlining keeps the request body typed in the generated client.
    """
    schema = model.model_json_schema()
    defs: dict[str, Any] = schema.pop("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].removeprefix("#/$defs/")])
            resolved = {key: resolve(value) for key, value in node.items()}
            if "discriminator" in resolved:
                # The mapping points into $defs; the property name is enough for the variants.
                resolved["discriminator"] = {
                    "propertyName": resolved["discriminator"]["propertyName"]
                }
            return resolved
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    result: dict[str, Any] = resolve(schema)
    return result


@router.post(
    "/signals",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": _inline_json_schema(SignalBatchIn)}},
        }
    },
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "No session cookie, or its session is unknown or expired. The batch "
            "is not stored; open a new session instead of retrying it."
        },
        status.HTTP_413_CONTENT_TOO_LARGE: {
            "description": "The batch is larger or has more signals than allowed. Not stored."
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "The batch is not valid JSON of the expected shape. Not stored."
        },
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "description": "The session sent too many batches. Not stored; see Retry-After."
        },
    },
)
async def ingest_signals(
    request: Request,
    service: SignalServiceDep,
    settings: SettingsDep,
    session_id: SessionCookie = None,
) -> Response:
    """Store a batch of behavioural signals for the visitor's session.

    The widget sends batches while the visitor is on the page; the browser attaches the
    session cookie. Batches that are too large or too frequent are counted on the session as a
    request signal for the Risk Engine.
    """
    try:
        session = await service.require_live_session(session_id)
    except SessionInvalidError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No live session") from None

    try:
        await service.check_rate(session)
    except RateLimitedError:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many signal batches",
            headers={"Retry-After": str(settings.signal_rate_window_s)},
        ) from None

    try:
        body = await _read_body(request, settings.signal_batch_max_bytes)
    except _BodyTooLargeError:
        await service.record_rejected(session)
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Signal batch too large") from None

    try:
        batch = SignalBatchIn.model_validate_json(body)
    except ValidationError as error:
        # The same 422 body FastAPI gives for any invalid request body.
        errors = [
            {**detail, "loc": ("body", *detail["loc"])}
            for detail in error.errors(include_url=False)
        ]
        raise RequestValidationError(errors, body=body) from None

    try:
        await service.store(session, batch)
    except BatchTooLargeError:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Too many signals") from None
    return Response(status_code=status.HTTP_204_NO_CONTENT)
