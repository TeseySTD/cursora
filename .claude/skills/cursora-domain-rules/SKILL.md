---
name: cursora-domain-rules
description: Cursora business rules for bot protection — verification sessions and their statuses, the allow/challenge/block decision, checkbox and interactive CAPTCHA, verdicts, the Nginx gate, per-site sensitivity, statistics, fingerprints and the role of ML — with what is decided versus still open. Use before implementing, changing or reviewing product behaviour in the sessions, risk, gate, tenant or insights modules, the widget flow, the admin settings or statistics, or the ML scoring.
---

# Cursora domain rules

The full, cited rule set is `docs/project-context.md` (BR-n business rules, FR-n/NFR-n
requirements, OQ-n open questions). This skill is the working summary; when in doubt, read the
cited section there. Statuses in that document: **Decided** and **Repo** items are settled;
**Proposed** and **Open** items are not.

Synced with `docs/project-context.md` on 2026-11-02. The concrete values below (attempts, block
durations, rate limits, token lifetime, retention periods) are copies; if they differ from the
document, the document wins: use its value and update this skill and the date.

## Golden rule

Never settle an open point in code. No invented thresholds, weights, score ranges, lifetimes,
attempt limits, HTTP status codes or schema fields. Write `TODO(team): <question> (OQ-<n>)`,
keep the code working without the value (configurable or clearly stubbed), and tell the user.

## Vocabulary (use these exact values)

| Concept                    | Values                                                               | Status                         |
| -------------------------- | -------------------------------------------------------------------- | ------------------------------ |
| Session status             | `new`, `challenge_required`, `verified`, `blocked`                   | Decided                        |
| Initial decision (risk)    | `allow`, `challenge`, `block` (`Decision` in `evaluator.py`)         | Decided                        |
| Final verdict (after task) | `human`, `suspicious`, `bot`                                         | Decided                        |
| Decision -> status mapping | allow -> verified, challenge -> challenge_required, block -> blocked | Proposed (DA-2, OQ-18)         |
| Sensitivity                | one integer per site, 0-100; higher = stricter                       | Decided; mapping/default OQ-17 |

## Sessions and signals

- The backend owns the verification session: the widget calls the session endpoint, the browser
  sends the cookie, the backend reuses a valid session or creates a `new` one and sets the
  cookie. The widget never generates (and preferably never reads) `session_id` (BR-1..BR-3).
- A new session never inherits an old status. Sessions are short-lived (`expires_at`) and bound
  to one site; lifetimes are open (BR-4, OQ-7).
- `session_id` only links requests; it is not a risk signal and not proof by itself (BR-5).
- Behavioural signals are stored as JSONB linked to the session (BR-6). The signal list is
  proposed, not final (BR-7, OQ-15) — see the `cursora-new-signal` skill before adding one.

## Risk evaluation

- System-first: rules alone must produce a decision; the ML score is an optional extra input via
  the `MlScorer` port, and a missing or untrained model must not stop decisions (BR-8, BR-36).
- `RiskEvaluator` is pure (no I/O, DB, clock, randomness); the service loads site settings and
  the optional ML score before calling it.
- Rules are internal; administrators never see or edit individual rules (BR-11). The rule set,
  weights and how they combine are open (BR-12, OQ-16).
- Sensitivity shifts the allow/challenge/block thresholds; the mapping is open (BR-27, OQ-17).

## Challenges

- Graduated: invisible assessment -> checkbox -> (still suspicious) one interactive task ->
  final assessment (BR-13). The checkbox appears only when the server decides so (BR-10).
- The MVP has exactly one interactive task: draw a line without touching the shapes (BR-15,
  BR-16). A second type, random selection and "Try another way" are backlog, not MVP.
- Accessibility: the same task with the keyboard or on-screen arrow buttons (they move an object
  along the route), with a generous time limit (BR-41, WCAG 2.5.7). Start, finish and gaps are
  at least 44x44 CSS px, never under 24 (BR-17, WCAG 2.5.8).
- Pass/fail of the task is deterministic (correctness and completion time). Not touching the
  shapes is part of correctness; speed, pauses and corrections are features for the risk
  engine/ML, not pass conditions (BR-17). There is no minimum time; solving too fast is only a
  feature. A touch means the line enters a shape, with no extra tolerance.
- Time limit: 2 minutes with a pointer to start with (later tuned to 99% of humans in the
  dataset), ten times that with the keyboard (BR-17, BR-41).
- `human` passes, `suspicious` gets another attempt, `bot` is blocked temporarily. A session has
  5 attempts; a failed attempt is a wrong answer, a time-out or asking for a new task without
  answering. Once they are used up the visitor sees "try again later or contact the site
  owner" (BR-18).
- Every block (`bot`, a `block` decision, used-up attempts) lasts 15 minutes and applies to the
  session only, never to the IP. More than 4 new sessions from one IP in a minute, or more than
  100 from one /24 in 5 minutes, lead to a challenge, not a block (BR-19).

## Integration: tokens like reCAPTCHA (decided 2026-10-25, ADR 0002)

- Site owners register sites and get a public site key (in the widget) and a secret key (for
  their backend). Any number of customer sites; Cursora runs no proxy in front of them.
- After `allow` or `human` the widget puts a short-lived verification token into the form; the
  site's backend sends it with the secret key to the Cursora verify API; each token is accepted
  once and lives 5 minutes, and the widget refreshes an expired token (BR-25, BR-26). A
  checkbox pass also yields a token.
- The token is an opaque random value (not a JWT), stored only as a hash with the site, the
  session, the expiry time and when it was used. The verify API is reCAPTCHA/Turnstile
  compatible: `secret` + `response` in; `success`, `challenge_ts`, `hostname`, `error-codes`
  (`timeout-or-duplicate`) out (BR-25).
- Only actions are protected (e.g. `POST /login`), never page views; search crawlers are not
  affected and scraping protection is outside the MVP (BR-42).
- If the Cursora API is unreachable, customers are advised to let visitors through after one
  retry (fail-open), logging and alerting on every such pass. Each verify call times out after
  3 seconds; retry only network or internal errors. The site's backend calls verify even with an
  empty token, and a missing token is rejected while the API answers (BR-43).

## Old Nginx gate (not an integration path)

- The repo still has an Nginx `auth_request` -> `GET /v1/gate/check` gate from the earlier
  design (BR-20..BR-23). Nginx is only a reverse proxy without business logic, so do not build
  features on the gate. Do not remove it in a separate clean-up either: it is replaced as part
  of implementing token verification, so protected actions always keep a server-side check
  (OQ-1, ADR 0002).

## Sites, admin and statistics

- A site has a domain, allowed origins, a public site key (`data-site-key`) and a secret key for
  token verification (BR-26); while the gate exists, also the address Nginx proxies to and the
  protected routes (method + path). Administrators never see or edit individual rules; besides
  these settings they set only the sensitivity. Attempts, block duration and request limit are
  not admin settings (BR-28).
- Project roles ADMIN and DEVELOPER; details open (BR-29, OQ-27).
- Statistics are aggregate (traffic, CAPTCHA outcomes, risk scores, blocks); a per-site
  dashboard is proposed and the metrics are open (BR-30, OQ-28). Label any false-positive figure
  as a proxy metric (BR-31).

## Privacy

- Fingerprints only as HMAC hashes, exact match only; never log, store or return raw
  fingerprints (BR-32). A changed fingerprint raises risk, it does not auto-trust (BR-33).
- Reputation per (site, fingerprint hash) is a soft signal, never an automatic allow or block
  (BR-34). A reputation record is deleted 30 days after its last activity.
- Keyed hashes are pseudonymisation, not anonymisation: never call stored data anonymous. No
  consent banner for visitors (BR-35).
- The raw IP is kept only while its session lives; risk assessments keep only a /24 (IPv4) or
  /48 (IPv6) prefix. Sessions are deleted after `expires_at`, raw signals are kept 30 days,
  individual risk assessments 14 months, daily aggregates without a limit. Signals and risk
  assessments keep `session_id` without a foreign key; a daily clean-up enforces the periods
  (BR-44).

## Before you finish

- Does the change match a Decided rule? Cite it (BR-n) in the PR description.
- Does it depend on an Open question? Leave `TODO(team) ... (OQ-n)` and say so in the PR.
- If the team decided something new in the chat or a meeting, update `docs/project-context.md`
  in the same PR, and this skill (with its sync date) if a rule or value above changed.
