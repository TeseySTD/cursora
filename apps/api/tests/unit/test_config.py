import pytest
from pydantic import ValidationError

from cursora_api.core.config import Settings


def test_samesite_none_requires_secure() -> None:
    with pytest.raises(ValidationError, match="requires session_cookie_secure"):
        Settings(env="test", session_cookie_samesite="none", session_cookie_secure=False)


def test_samesite_none_with_secure_is_allowed() -> None:
    settings = Settings(env="test", session_cookie_samesite="none", session_cookie_secure=True)
    assert settings.session_cookie_samesite == "none"
