---
name: cursora-new-signal
description: Add or change a behavioural or request signal end to end in Cursora — widget collection, the sessions API and its JSONB storage, feature extraction in packages/features, risk rules, and ML training — without train/serve skew or privacy leaks. Use whenever a task touches what the widget collects, the signal payload, cursora_features.extract_features, the feature vector, or the data the ML model is trained on.
---

# Adding or changing a signal

A signal crosses every layer, and this is the change the monorepo is built for: do it in one PR.
Read BR-5..BR-7 and BR-32..BR-40 in `docs/project-context.md` first.

## 0. Is the signal agreed?

The signal set is proposed, not final (BR-7, OQ-15): pointer/touch movement, clicks and pauses,
time on page, browser and device parameters (widget); IP, User-Agent and request rate (server or
Nginx). Anything else, or any change in how a listed signal is collected, needs a team decision —
ask, or leave `TODO(team): ... (OQ-15)`. Prefer an OpenSpec change (`/opsx:propose`) for new
signals.

## 1. Widget (`apps/widget`)

- Collect passively; listeners `passive: true` and removed on unmount; no console logging of
  signals or device data.
- Send only what the backend needs, to the Cursora API only. Never send a raw fingerprint for
  storage: the backend keeps HMAC hashes only (BR-32).
- Keep the bundle small (`pnpm size:widget`). See the `cursora-widget` skill.

## 2. API (`apps/api`, module `sessions`)

- Extend the request schema in `sessions/schemas.py`; store signals as JSONB linked to the
  session (BR-6) via `sessions/repository.py`; a new column means a migration
  (`cursora-db-migration`).
- Server-side request signals (IP, User-Agent, rate) come from the request or the headers Nginx
  sets (`X-Real-IP`, `X-Forwarded-For`, `X-Original-URI`) — never trust client-sent copies.
- Hash fingerprint material with HMAC before it is stored or compared; never log it.
- Contract changed -> `pnpm api:openapi` (`cursora-api-contract`).

## 3. Features (`packages/features`)

- `cursora_features.extract_features` is the single implementation for serving and training.
  Add the feature there, never in `apps/api` or `ml/`.
- Pure Python, no third-party dependencies, deterministic, no I/O. Missing or malformed input
  must not crash extraction (decide the fallback with the team if unclear).
- Unit-test it in `packages/features/tests` (`pnpm test:features`). Renaming or changing the
  meaning of a feature invalidates trained models: say so in the PR.

## 4. Risk engine (`apps/api`, module `risk`)

- Rules consume the feature vector; keep `evaluator.py` and `rules/` pure.
- Weights and thresholds are open (OQ-16, OQ-17): no invented numbers.

## 5. ML (`ml/`)

- Training reads features only through `cursora_features.extract_features`.
- Regenerate or extend the synthetic bot data (`cursora_ml.bot_generator`) if the new signal
  needs it, and keep `ml/data` and `ml/models` out of git.

## Checklist

- [ ] Signal agreed (or `TODO(team)` with OQ-15) and documented in `docs/project-context.md`
- [ ] Widget, schema, storage, feature, rules and training all updated in the same PR
- [ ] No raw fingerprint stored, logged or returned; HMAC only
- [ ] Tests at every layer; `pnpm check` passes
