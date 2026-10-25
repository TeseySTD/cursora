---
name: cursora-db-migration
description: Create, review and apply PostgreSQL schema changes for the Cursora API with SQLAlchemy 2.0 async ORM models and Alembic (pnpm db:up, db:revision, db:migrate). Use whenever an ORM model in apps/api/src/cursora_api/modules/*/models.py is added or changed, a migration under apps/api/alembic/versions/ is needed, or migrations conflict after a rebase.
---

# Database migrations

Postgres 18 is the only datastore (JSONB for flexible signal data, no Redis). Alembic runs
async (`apps/api/alembic/env.py`) and reads the URL from `CURSORA_DATABASE_URL` via the app
settings — never put credentials in `alembic.ini`.

## Workflow

1. `pnpm db:up` (Postgres in Docker on `127.0.0.1:5432`) and `pnpm db:migrate` so the local
   database is at `head`.
2. Change models in the owning module's `models.py`: subclass `cursora_api.core.db.Base`,
   SQLAlchemy 2.0 typed style (`Mapped[...]`, `mapped_column(...)`), `JSONB` from
   `sqlalchemy.dialects.postgresql` for flexible payloads. Do not name constraints by hand:
   `NAMING_CONVENTION` in `core/db.py` keeps autogenerate diffs stable.
3. New module? Import its `models` in `apps/api/alembic/env.py`, otherwise autogenerate does
   not see its tables.
4. `pnpm db:revision "<imperative message>"` → `apps/api/alembic/versions/<YYYYMMDD>_<rev>_<slug>.py`.
5. Review the generated file line by line — autogenerate gets these wrong or misses them:
   - column/table renames (shows up as drop + add = data loss) → use `op.alter_column` /
     `op.rename_table`;
   - server defaults, `Enum` types (create/drop), check constraints, expression indexes;
   - data migrations (write them explicitly, keep them idempotent);
   - anything touching tables of another module (modules must not share tables).
6. Write a real `downgrade()`.
7. Apply and round-trip:

   ```sh
   pnpm db:migrate
   uv run --package cursora-api alembic -c apps/api/alembic.ini downgrade -1
   pnpm db:migrate
   ```

8. `pnpm test:api` with the database up (integration tests), then `pnpm check`.

## Rules

- Never edit a migration that is already on `main`; add a new one.
- Keep one head: after rebasing onto a `main` that gained migrations, check
  `uv run --package cursora-api alembic -c apps/api/alembic.ini heads`; if there are two,
  regenerate yours on top of the new head (or add an explicit merge revision if the team
  agrees).
- Fingerprints only as HMAC hashes — no column may hold a raw fingerprint.
- Do not invent tables or fields that the team has not agreed on (see
  `docs/project-context.md`); leave `TODO(team): ...` instead.
- CI runs `pnpm db:migrate` against a fresh Postgres before the API tests, so a broken
  migration fails the `python` job.
