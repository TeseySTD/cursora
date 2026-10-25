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

A busy port makes the server exit instead of moving to another port. To use other ports, set
`UVICORN_PORT`, `ADMIN_DEV_PORT` and `WIDGET_DEV_PORT` in the shell (see `.env.example`).

Full stack in Docker: `pnpm docker:up`

| URL                                    | What                                   |
| -------------------------------------- | -------------------------------------- |
| http://localhost:8080/                 | Admin panel                            |
| http://localhost:8080/api/docs         | API                                    |
| http://localhost:8080/widget/widget.js | Widget bundle                          |
| http://localhost:8081/protected/       | Sample site, guarded by `auth_request` |
| http://localhost:8081/                 | Sample site, unprotected               |

Before pushing, run `pnpm check`.

## AI-assisted development

Instructions for AI coding agents live in [AGENTS.md](AGENTS.md) (Claude Code reads it through
`CLAUDE.md`); the business rules they follow are in
[docs/project-context.md](docs/project-context.md).

- **Claude Code**: shared permissions in `.claude/settings.json`, project skills in
  `.claude/skills/` (listed in AGENTS.md) and an optional
  [Playwright MCP](https://github.com/microsoft/playwright-mcp) server in `.mcp.json` (localhost
  only; approve it once). Personal settings go in `.claude/settings.local.json` and
  `CLAUDE.local.md`, which are git-ignored.
- **OpenSpec**: spec-driven changes with `/opsx:propose`, `/opsx:apply` and `/opsx:archive`.
  Install the team's version with `npm i -g @fission-ai/openspec@1.10.0` and opt out of its
  telemetry with `export OPENSPEC_TELEMETRY=0`. Only `openspec/config.yaml` is committed; specs
  and changes stay on your machine.
- **cubic**: AI review of every non-draft pull request against AGENTS.md and
  docs/project-context.md, configured in `cubic.yaml` (setup below).
- **Dependabot**: weekly, grouped dependency update PRs for npm (pnpm), uv, Docker, Docker Compose
  and GitHub Actions (`.github/dependabot.yml`).

### AI pull-request review (cubic)

[cubic](https://www.cubic.dev) is free for public repositories (fair-use limits) and needs no
secrets and no workflow file. One-time setup by the repository owner:

1. Sign in at <https://cubic.dev/sign-up> with GitHub and install the
   [cubic GitHub App](https://github.com/apps/cubic-dev-ai) for this repository only.
2. Merge `cubic.yaml` to `main`: cubic reads its configuration from the default branch only.

After that it reviews every non-draft PR; comment `@cubic-dev-ai review this PR` to re-run it.
Drafts, titles starting with `WIP` and PRs labelled `skip-review` are skipped. Its comments are
suggestions: the merge gate stays `ci-ok` plus one approval, so do not make its check required.
