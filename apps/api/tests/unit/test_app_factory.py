from fastapi import FastAPI

from cursora_api.core.config import Settings
from cursora_api.main import create_app

MODULES = {"tenant", "sessions", "risk", "gate", "insights"}


def test_create_app_returns_configured_app(settings: Settings) -> None:
    app = create_app(settings)
    assert isinstance(app, FastAPI)
    assert app.state.settings is settings
    assert {"/health", "/health/db", "/v1/gate/check"} <= set(app.openapi()["paths"])


def test_every_module_is_documented(app: FastAPI) -> None:
    tags = {tag["name"] for tag in app.openapi()["tags"]}
    assert tags >= MODULES


def test_operation_ids_are_stable(app: FastAPI) -> None:
    ids = {op["operationId"] for path in app.openapi()["paths"].values() for op in path.values()}
    assert ids == {"system_health", "system_health_db", "gate_check"}
