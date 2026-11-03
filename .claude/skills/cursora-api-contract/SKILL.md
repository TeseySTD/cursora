---
name: cursora-api-contract
description: Keep the Cursora API contract in sync — export the FastAPI OpenAPI schema to packages/api-client/openapi.json, regenerate the @hey-api/openapi-ts TypeScript client and call it from the admin app. Use after changing any FastAPI route, schema, tag or operationId, when `pnpm api:check` or the CI `contract` job fails, or when frontend code needs a new or changed API call.
---

# API contract (code-first)

```text
FastAPI (apps/api) --pnpm api:openapi--> packages/api-client/openapi.json (committed)
                   --openapi-ts--> packages/api-client/src/generated/ (git-ignored)
                   --> @cursora/api-client (used by apps/admin)
```

## After a backend change

1. `pnpm api:openapi` — runs `apps/api/scripts/export_openapi.py` (sorted keys, stable output,
   independent of your `.env`) and regenerates the client.
2. Commit `packages/api-client/openapi.json` together with the backend change.
3. `pnpm api:check` must print "API contract is up to date." (CI job `contract` runs it).

## Rules

- Never edit `openapi.json` by hand and never commit `packages/api-client/src/generated/`
  (it is regenerated on `pnpm install`, build, typecheck and test).
- operationIds are `<tag>_<route function name>` and become the TS function names. Renaming a
  route function or tag is a breaking change for the admin — update the callers in the same PR.
- Contract changes need both sides to agree (CODEOWNERS: backend and frontend owners of
  `packages/api-client/`). Removing or renaming fields is breaking; adding optional fields is
  not.

## Using the client in the admin

- Import from `@cursora/api-client`; the base URL is configured once in
  `apps/admin/src/lib/api.ts` (`VITE_API_BASE_URL`, default `/api`, proxied to FastAPI by the
  Vite dev server and by Nginx in Docker).
- Fetch through TanStack Query (`useQuery` / `useMutation`) — the app already provides a
  `QueryClient` in `apps/admin/src/App.tsx`.
- Tests stub `fetch` (see `apps/admin/tests/app.test.tsx`) and call `configureApiClient(...)`.
