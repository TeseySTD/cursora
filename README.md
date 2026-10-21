# Cursora

Cursora is a bot-protection service for websites. A small JavaScript widget collects
signals in the browser, a FastAPI backend scores them with a deterministic risk engine
(optionally assisted by an ML model) and answers allow / challenge / block. Nginx asks it
via `auth_request` before forwarding requests to the protected routes of a site.

See [docs/architecture.md](docs/architecture.md) for the components and request flow.

## Quick start

Prerequisites: Node.js 24 (see `.nvmrc`, ≥ 22.18 works), [uv](https://docs.astral.sh/uv/),
Docker. Details in [CONTRIBUTING.md](CONTRIBUTING.md).

```sh
corepack enable     # activates the pinned pnpm version
pnpm bootstrap      # pnpm install + uv sync (Python is downloaded by uv)
pnpm db:up          # Postgres in Docker on localhost:5432
pnpm db:migrate     # alembic upgrade head
pnpm dev            # api + admin + widget dev servers
```

| URL                        | What                                    |
| -------------------------- | --------------------------------------- |
| http://localhost:8000/docs | API (Swagger UI)                        |
| http://localhost:5173      | Admin panel (proxies `/api` to the API) |
| http://localhost:5174      | Widget test harness                     |

Full stack in Docker: `pnpm docker:up`

| URL                                    | What                                   |
| -------------------------------------- | -------------------------------------- |
| http://localhost:8080/                 | Admin panel                            |
| http://localhost:8080/api/docs         | API                                    |
| http://localhost:8080/widget/widget.js | Widget bundle                          |
| http://localhost:8081/protected/       | Sample site, guarded by `auth_request` |
| http://localhost:8081/                 | Sample site, unprotected               |

Before pushing, run `pnpm check`.
