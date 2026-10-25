---
name: cursora-domain-rules
description: Cursora business rules for bot protection — verification sessions and their statuses, the allow/challenge/block decision, checkbox and interactive CAPTCHA, verdicts, the Nginx gate, per-site sensitivity, statistics, fingerprints and the role of ML — with what is decided versus still open. Use before implementing, changing or reviewing product behaviour in the sessions, risk, gate, tenant or insights modules, the widget flow, the admin settings or statistics, or the ML scoring.
---

# Cursora domain rules

The full, cited rule set is `docs/project-context.md` (BR-n business rules, FR-n/NFR-n
requirements, OQ-n open questions). This skill is the working summary; when in doubt, read the
cited section there. Statuses in that document: **Decided** and **Repo** items are settled;
**Proposed** and **Open** items are not.

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
- The MVP has exactly one interactive CAPTCHA type; which one is open (BR-15, BR-16, OQ-22).
  A second type, random selection and "Try another way" are backlog, not MVP.
- Pass/fail of the task is deterministic (correctness and completion time); speed, pauses,
  corrections and trajectory are features for the risk engine/ML, not pass conditions (BR-17).
- `human` passes, `suspicious` gets another attempt, `bot` is blocked temporarily; attempt limit
  and block duration/scope are open (BR-18, BR-19, OQ-21, OQ-23).

## Gate (Nginx)

- Only configured protected routes are checked; everything else is forwarded (BR-20).
- Nginx `auth_request` -> `GET /v1/gate/check` -> the session status decides: `verified` forward,
  `challenge_required` challenge, `blocked` block (BR-21). Nginx holds no business logic (BR-22).
- HTTP codes, challenge UX (OQ-12), treatment of `new`/no cookie (Proposed: challenge, OQ-9) and
  behaviour when the API is unreachable (OQ-11) are open — keep the existing `TODO(team)`.
- The verification-token path (secret API key, customer-side verification) is open (OQ-1).

## Sites, admin and statistics

- A site has a domain, allowed origins, an origin backend address and a public site key
  (`data-site-key`) (BR-26). Administrators change only the sensitivity (BR-28).
- Project roles ADMIN and DEVELOPER; details open (BR-29, OQ-27).
- Statistics are per site and aggregate (traffic, CAPTCHA outcomes, risk scores, blocks);
  metrics are open (BR-30, OQ-28). Label any false-positive figure as a proxy metric (BR-31).

## Privacy

- Fingerprints only as HMAC hashes, exact match only; never log, store or return raw
  fingerprints (BR-32). A changed fingerprint raises risk, it does not auto-trust (BR-33).
- Reputation per (site, fingerprint hash) is a soft signal, never an automatic allow or block
  (BR-34). Behavioural data must be anonymised; retention and consent are open (BR-35, OQ-32).

## Before you finish

- Does the change match a Decided rule? Cite it (BR-n) in the PR description.
- Does it depend on an Open question? Leave `TODO(team) ... (OQ-n)` and say so in the PR.
- If the team decided something new in the chat or a meeting, update `docs/project-context.md`
  in the same PR.
