"""Pydantic request/response schemas of the sessions module."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from cursora_api.modules.sessions.models import SessionState
from cursora_api.modules.tenant.service import SITE_KEY_MAX_LENGTH


class SessionRequest(BaseModel):
    """What the widget sends when a page with it loads."""

    model_config = ConfigDict(extra="forbid")

    site_key: str = Field(min_length=1, max_length=SITE_KEY_MAX_LENGTH)


class SessionResponse(BaseModel):
    """The visitor's current session. The id itself is only in the HttpOnly cookie."""

    state: SessionState
    expires_at: datetime


# Signal batches. Every model forbids unknown fields, so a batch can never smuggle in typed
# text, form values or other identifiers (CAPTHCA-17 AC3): it is rejected with 422 instead.

type FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]
# Milliseconds since the page started loading (performance.now() in the widget).
type PageTime = Annotated[float, Field(ge=0, allow_inf_nan=False)]
# "" is what browsers report for clicks without a pointer: keyboard activation, element.click().
type PointerType = Literal["mouse", "touch", "pen", ""]


class _Signal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    t: PageTime


class MoveSignal(_Signal):
    """A sampled pointer (cursor or touch) position."""

    type: Literal["move"]
    x: FiniteFloat
    y: FiniteFloat
    pointer: PointerType


class ClickSignal(_Signal):
    type: Literal["click"]
    x: FiniteFloat
    y: FiniteFloat
    button: int = Field(ge=0, le=31)
    pointer: PointerType


class Viewport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width: int = Field(ge=0)
    height: int = Field(ge=0)


class EnvironmentSignal(_Signal):
    """Coarse browser parameters, recorded once per page.

    Deliberately not a fingerprint: language, timezone, screen size and other high-entropy
    attributes are left out until fingerprints are collected as HMAC hashes (BR-32).
    """

    type: Literal["env"]
    viewport: Viewport
    # camelCase: the browser's own property names, as the widget sends them.
    devicePixelRatio: float = Field(gt=0, allow_inf_nan=False)
    maxTouchPoints: int = Field(ge=0)
    webdriver: bool
    cookieEnabled: bool


type Signal = Annotated[MoveSignal | ClickSignal | EnvironmentSignal, Field(discriminator="type")]


class SignalBatchIn(BaseModel):
    """One batch of behavioural signals from the widget.

    A batch may have no signals: it still carries the time on page (CAPTHCA-17 AC5).
    """

    model_config = ConfigDict(extra="forbid")

    t: PageTime = Field(description="Time on page when the batch was sent, in ms.")
    signals: list[Signal]
