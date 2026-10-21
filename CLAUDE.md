# CLAUDE.md

Guidance for AI coding assistants (and humans) working in this repo.

## Repo map

```
apps/
  api/            FastAPI modular monolith (uv package cursora-api)
    src/cursora_api/
      core/       config (pydantic-settings), db (async SQLAlchemy), logging
      health.py   GET /health, /health/db
      main.py     create_app() factory; api_router.py mounts module routers at /v1
      modules/    tenant/ sessions/ risk/ gate/ insights/ — one per bounded context:
                  router -> service -> repository -> models / schemas
        risk/     evaluator.py (pure RiskEvaluator), rules/, sensitivity.py, ml_port.py
    alembic/      async migrations (metadata imported from every module's models)
    scripts/export_openapi.py
  widget/         Shadow DOM widget -> single IIFE dist/widget.js (React, Tailwind, shadcn)
  admin/          Admin SPA (React Router, TanStack Query, shadcn)
packages/
  features/       cursora-features: feature extraction shared by api AND ml
  api-client/     committed openapi.json + generated @hey-api/openapi-ts client
ml/               cursora-ml: bot_generator, training, notebooks (pandas, scikit-learn)
infra/            compose/ (compose.yml, compose.dev.yml), docker/, nginx/
scripts/          cross-platform Node helpers used by package.json scripts
docs/             architecture.md, adr/
```

## Decisions

| Topic        | Decision                                                             |
| ------------ | -------------------------------------------------------------------- |
| Monorepo     | pnpm workspaces + uv workspace, one lockfile each                    |
| Task runner  | Root `package.json` scripts only (no Makefile/justfile)              |
| Backend      | FastAPI, SQLAlchemy 2.0 async (asyncpg), Alembic, pydantic-settings  |
| Database     | PostgreSQL (JSONB where useful). **No Redis.**                       |
| Gate         | Nginx `auth_request` -> `GET /v1/gate/check`, protected routes only  |
| Frontend     | React + Vite + TS + Tailwind + shadcn/ui (widget and admin)          |
| API contract | Code-first: FastAPI -> committed `openapi.json` -> hey-api TS client |
| ML           | scikit-learn; features from `cursora-features` (no train/serve skew) |
| Infra / CI   | Docker Compose, Nginx, GitHub Actions                                |

Rationale: [docs/adr/0001-monorepo-structure.md](docs/adr/0001-monorepo-structure.md).

## Conventions

- Code, comments, commits and docs in English.
- One module per bounded context; keep the router -> service -> repository layering. Modules
  talk to each other through services, not each other's repositories or tables.
- `RiskEvaluator` is pure: no I/O, no DB, no clock, no randomness. Inputs in, decision out.
  The ML score is an optional input via the `MlScorer` port.
- Feature extraction lives only in `packages/features`; the api and ml both import it.
  The api must not depend on pandas, scikit-learn or jupyter.
- No business logic in Nginx: it only forwards to `/v1/gate/check` and acts on the status.
- Fingerprints are stored and compared only as HMAC hashes. Never log, store or return
  raw fingerprints.
- Do not invent product requirements, schemas, thresholds, weights or status codes. Leave
  `TODO(team): ...` where a team decision is needed.
- API changes: run `pnpm api:openapi` and commit `packages/api-client`.
- DB changes: models in the module's `models.py`, then `pnpm db:revision "<message>"`.
- Widget CSS must stay inside the shadow root; portals target the shadow root
  (`usePortalContainer`).
- Python: ruff + mypy strict. TS: strict, ESLint flat config, Prettier.
- Branches `<type>/CAPTHCA-<n>-slug`, PR titles `CAPTHCA-<n>: summary`.

## Before finishing

Run `pnpm check` and make sure it passes.
