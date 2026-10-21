<!-- PR title: "CAPTHCA-<n>: <short summary>"  (branch: <type>/CAPTHCA-<n>-<slug>) -->

## What

<!-- What does this PR change, and why? -->

Jira: CAPTHCA-

## How to test

<!-- Steps a reviewer can follow, or "covered by tests". -->

## Checklist

- [ ] `pnpm check` passes locally
- [ ] API changed → ran `pnpm api:openapi` and committed `packages/api-client`
- [ ] DB models changed → added an Alembic migration (`pnpm db:revision "<message>"`)
- [ ] No raw fingerprints stored, logged or returned (HMAC hashes only)
- [ ] Docs / `.env.example` updated if behaviour or settings changed
