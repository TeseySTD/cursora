---
name: cursora-git-workflow
description: Cursora team conventions for branches, commits and pull requests — Jira keys like CAPTHCA-12, branch names like feat/CAPTHCA-12-site-settings, Conventional Commits, PR titles that start with the Jira key, the PR template checklist, pnpm check and CODEOWNERS review. Use when creating a branch, writing a commit message, preparing, titling or describing a pull request, or deciding whether a change is ready to merge.
---

# Cursora git workflow

Every change is tied to a Jira issue `CAPTHCA-<n>`. Never invent the number: if the user has
not given one, ask for it (or leave `CAPTHCA-<n>` as a visible placeholder for them to fill in).

## Branch

- Branch from an up-to-date `main`: `<type>/CAPTHCA-<n>-<short-slug>`, e.g.
  `feat/CAPTHCA-12-site-settings`.
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`.
- Never commit directly to `main`, never force-push `main` or someone else's branch.

## Commits

- English, [Conventional Commits](https://www.conventionalcommits.org/):
  `<type>(<scope>): <imperative summary>` — e.g. `feat(api): add sites repository`.
- Standard types: `feat`, `fix`, `docs`, `chore`, `ci`, `build`, `refactor`, `test`, `perf`.
- Scopes follow the area touched, as in the existing history: `api`, `widget`, `admin`,
  `api-client`, `features`, `ml`, `infra`, `dev`, `github`, `python`. Omit the scope for
  repo-wide changes.
- Small, focused commits. Do not mix formatting-only changes with behaviour changes.
- Only commit or push when the user asks you to.

## Before opening a PR

1. `pnpm check` passes (format:check + lint + typecheck + test + api:check).
2. API changed → `pnpm api:openapi`, commit `packages/api-client/openapi.json`
   (never `packages/api-client/src/generated/`). See the `cursora-api-contract` skill.
3. ORM models changed → Alembic migration via `pnpm db:revision "<message>"`. See
   `cursora-db-migration`.
4. No raw fingerprints stored, logged or returned (HMAC hashes only).
5. Docs and `.env.example` updated if behaviour or settings changed.
6. If the change was planned with OpenSpec, the change is validated
   (`openspec validate <change>`); specs stay local (they are git-ignored).

## Pull request

- Title: `CAPTHCA-<n>: <short summary>`.
- Body: fill in `.github/pull_request_template.md` — **What** (what and why, plus
  `Jira: CAPTHCA-<n>`), **How to test** (steps or "covered by tests"), and tick only the
  checklist items that are actually true.
- CODEOWNERS (`.github/CODEOWNERS`) are requested automatically; at least one approval and a
  green `ci-ok` check are required to merge. The AI PR reviewer comments automatically; treat
  its findings as suggestions to verify, not as approval.
- Keep PRs small and single-purpose; cross-cutting changes (API + client + admin) are fine in
  one PR when they belong together.

## Dependabot PRs

Dependabot PRs have no Jira key; they are reviewed like any other PR. Do not rename their
branches.
