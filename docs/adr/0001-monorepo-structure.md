# ADR 0001: Monorepo structure

- Status: accepted
- Date: 2026-10-21

## Context

Cursora has a Python backend, a Python ML stream, two React frontends (the embeddable
widget and the admin panel) and the infrastructure that wires them together. A team of
eight works on all of it in parallel, in short Agile iterations. The parts change together
often: an API change touches the backend, the TS client and the admin; a new signal
touches the widget, the feature extraction, the risk engine and the ML training.

## Decision

1. **One repository**, with **pnpm workspaces** for JS/TS and a **uv workspace** for
   Python. Each ecosystem has one lockfile (`pnpm-lock.yaml`, `uv.lock`) and its own native
   tooling.
2. **Shared feature extraction** in `packages/features` (`cursora-features`). The api and the
   ml training code both depend on it, so there is one implementation of "signals →
   features". This prevents train/serve skew: a model trained on features computed one way
   and served features computed another way. The package is pure Python with no heavy
   dependencies, so the api doesn't pull in pandas or scikit-learn.
3. **Code-first API contract.** FastAPI generates the OpenAPI document. It is committed as
   `packages/api-client/openapi.json`, so contract changes show up in PR diffs, and
   `pnpm api:check` (in CI) fails if it is stale. The TS client is generated from it by
   `@hey-api/openapi-ts` on install and before builds; it is not committed.
4. **Root `package.json` scripts as the only task runner.** Everyone already has Node and
   pnpm, the scripts work on Windows, macOS and Linux (non-trivial ones are Node scripts in
   `scripts/`), and there is no Make or just to install or learn.

## Consequences

- One clone, one `pnpm bootstrap`, one `pnpm check`, and cross-cutting changes land in a
  single PR.
- CI uses path filters so a PR only runs the jobs it affects. Changes to shared root files
  run everything.
- Contributors need both Node (pnpm) and uv installed.
- Python commands are wrapped by pnpm scripts (`uv run ...`), which adds a small layer of
  indirection.
- Alternatives considered: separate repos (contract drift, multi-PR changes), a
  schema-first contract such as TypeSpec (an extra language and toolchain for an MVP), and
  Make/just (not native on Windows, an extra tool).
