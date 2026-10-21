"""Aggregates every module's router; mounted under /v1 by the app factory."""

from fastapi import APIRouter

from cursora_api.modules.gate.router import router as gate_router
from cursora_api.modules.insights.router import router as insights_router
from cursora_api.modules.risk.router import router as risk_router
from cursora_api.modules.sessions.router import router as sessions_router
from cursora_api.modules.tenant.router import router as tenant_router

api_router = APIRouter()
api_router.include_router(tenant_router)
api_router.include_router(sessions_router)
api_router.include_router(risk_router)
api_router.include_router(gate_router)
api_router.include_router(insights_router)

# Shown in /docs so the module structure is visible even before modules have endpoints.
OPENAPI_TAGS = [
    {"name": "system", "description": "Liveness and readiness probes."},
    {"name": "tenant", "description": "Sites, site keys and per-site settings."},
    {"name": "sessions", "description": "Widget sessions and collected signals."},
    {"name": "risk", "description": "Risk Engine: features -> score -> decision."},
    {"name": "gate", "description": "Nginx auth_request endpoint for protected routes."},
    {"name": "insights", "description": "Aggregate statistics for the admin panel."},
]
