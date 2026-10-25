---
name: cursora-api-module
description: Add or change backend features in the Cursora FastAPI modular monolith (apps/api) — endpoints, Pydantic schemas, services, repositories, ORM models or a new bounded-context module — following the router -> service -> repository layering, module boundaries, async SQLAlchemy sessions, settings and test layout. Use for any change under apps/api/src/cursora_api/ or apps/api/tests/.
---

# Backend work in `apps/api`

Read the relevant part of `docs/project-context.md` first (business rules, open questions).

## Module layout

Each bounded context is a package `apps/api/src/cursora_api/modules/<module>/`:

| File            | Responsibility                                                                          |
| --------------- | --------------------------------------------------------------------------------------- |
| `router.py`     | HTTP only: request/response mapping, status codes. No business logic, no DB access.     |
| `schemas.py`    | Pydantic v2 request/response models — they become the public contract (`openapi.json`). |
| `service.py`    | Use cases and business logic; orchestrates repositories and other modules' services.    |
| `repository.py` | Persistence only: SQLAlchemy 2.0 queries on an `AsyncSession`.                          |
| `models.py`     | ORM tables, subclasses of `cursora_api.core.db.Base`.                                   |

Modules: `tenant` (sites, site keys, per-site settings), `sessions` (widget sessions and
signals), `risk` (`evaluator.py`, `rules/`, `sensitivity.py`, `ml_port.py`), `gate` (Nginx
`auth_request` target `GET /v1/gate/check`), `insights` (aggregate statistics).

## Rules

- Modules talk to each other only through services (`from cursora_api.modules.x import
service`), never through another module's repository, models or tables.
- `risk/evaluator.py` and `risk/rules/` stay pure: no I/O, DB, network, clock or randomness.
  The service loads site settings / the optional ML score (`MlScorer` port) and passes them in.
- Fingerprints are stored and compared only as HMAC hashes; never log, store or return raw
  fingerprints.
- Postgres is the only datastore (JSONB for flexible signal data). No Redis, no new stores.
- The api must not depend on pandas, scikit-learn or jupyter; feature extraction comes from
  `cursora_features` (`packages/features`).
- Undecided product rules, thresholds, weights or status codes: leave `TODO(team): ...`
  instead of inventing values.
- Async all the way: `async def` endpoints, `SessionDep` from `core/db.py` (one
  `AsyncSession` per request), `expire_on_commit=False` is already set.
- Settings live in `core/config.py` (`CURSORA_` env prefix, pydantic-settings). Add every new
  setting to `.env.example` with its default.
- Python 3.14, ruff (line length 100) and `mypy --strict` must pass: full type hints, no
  `Any` leaks, no `# type: ignore` without a reason.
- The generic `fastapi` skill recommends SQLModel, ty, Asyncer and `fastapi dev`. Here the
  choices are SQLAlchemy 2.0 async, mypy, plain asyncio and `pnpm dev:api` with the
  `create_app()` factory; its other FastAPI advice (Annotated dependencies, return types,
  router-level prefix and tags) applies.

## Adding an endpoint

1. Schemas in `schemas.py`.
2. Route in `router.py`. The router already has its prefix and tag; the function name becomes
   the OpenAPI operationId `<tag>_<function name>` (see `_operation_id` in `main.py`), which is
   the function name in the generated TS client — choose it deliberately; renaming it breaks
   the client.
3. Logic in `service.py`, queries in `repository.py`, tables in `models.py` (+ migration, see
   the `cursora-db-migration` skill).
4. Tests:
   - unit: `apps/api/tests/unit/`, use the `client` fixture (`httpx.AsyncClient` over
     `ASGITransport`) from `tests/conftest.py`; pytest-asyncio runs in auto mode.
   - DB: `apps/api/tests/integration/` with `pytestmark = pytest.mark.integration`; they need
     `pnpm db:up` and are skipped without a database unless `REQUIRE_DB=1` (CI sets it).
   - `tests/unit/test_app_factory.py` asserts the exact set of paths and operationIds — update
     it when you add or rename endpoints.
5. `pnpm api:openapi` and commit `packages/api-client/openapi.json` (`cursora-api-contract`).
6. `pnpm check`.

## Adding a module (new bounded context — agree with the team first)

1. Create the package with `__init__.py` (one-line docstring) and the five files above.
2. Register the router in `api_router.py` and add its tag to `OPENAPI_TAGS`.
3. Import its `models` in `apps/api/alembic/env.py` so autogenerate sees the tables.
4. Add it to `MODULES` in `tests/unit/test_app_factory.py`.
5. Update the repo map in `AGENTS.md`, `docs/architecture.md` and `.github/CODEOWNERS`.

## Useful commands

- `pnpm dev:api` — uvicorn with reload on <http://localhost:8000/docs>.
- `pnpm test:api`, `pnpm lint:py`, `pnpm typecheck:py`, `pnpm format`.
