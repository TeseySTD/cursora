# ADR 0002: Token verification as the site integration

- Status: accepted
- Date: 2026-11-02 (team decision of 2026-10-25, confirmed on 2026-11-02)

## Context

Cursora serves any number of customer sites. The 2026-09-14 design protected a site with an
Nginx gate: Nginx in front of the site's backend sends an `auth_request` subrequest to
`GET /v1/gate/check` for each protected route and forwards the request only when the visitor's
session is `verified`. The repository still has that gate: a stub endpoint that always allows
and a sample site config in `infra/nginx/conf.d/20-protected-origin.conf`.

With many customer sites the gate does not scale. Either every customer runs and configures
its own Nginx and closes direct access to its backend, or Cursora runs a proxy in front of
every customer site, taking over their DNS, TLS and all of their traffic, so that a Cursora
outage takes whole sites down. The session cookie also belongs to the Cursora API's domain, so
a gate on the customer's domain does not receive it unless the API is served under that domain
too.

On 2026-10-25 the team decided to integrate the way reCAPTCHA does. On 2026-11-02 the team
added that the gate must not be removed as a clean-up task, because without a server-side
check a bot submits the form directly, past the widget, and that moving verification to the
customer's backend needs an ADR, Jira epics and specs. This is that ADR.

## Decision

1. Each site has a public site key, used by the widget, and a secret key, used by the site's
   backend.
2. After a pass (`allow`, a checkbox pass, or `human` after the interactive task) the widget
   puts a short-lived verification token into the form. A token lives 5 minutes, as in
   Cloudflare Turnstile, and the widget refreshes an expired token itself. The token is an
   opaque random value, not a JWT; Cursora stores only its hash with the site, the session,
   the expiry time and when it was used.
3. The site's backend sends the token and its secret key to the Cursora verify API and
   accepts the protected action only if the token is valid. Each token is accepted once. The
   verify API is compatible with reCAPTCHA and Turnstile: it takes `secret` and `response` and
   returns `success`, `challenge_ts`, `hostname` and `error-codes` (`timeout-or-duplicate` for
   an expired or reused token), so existing client libraries work with only the URL changed.
4. Only actions are protected, such as form submissions (`POST /login`), never page views.
5. If the verify API is unreachable, customers are advised to let the action through after
   one retry (fail-open), and to log and alert on every such pass, as Friendly Captcha's SDKs
   do. Each verify call times out after 3 seconds, and only network or internal errors are
   retried, never a rejected or used token. The site's backend calls the verify API even with
   an empty token: while the API answers, a missing token is rejected and the site asks the
   visitor to reload the page, so a bot cannot pass by not loading the widget.
6. Cursora runs no proxy in front of customer sites. Its Nginx is only a reverse proxy for
   Cursora's own services.
7. The gate code is not removed as a separate clean-up. It is replaced as part of
   implementing this decision, so that protected actions are never left without a
   server-side check.

## Consequences

- A new customer site is a database record on Cursora's side and a few lines of code in the
  customer's backend, with no infrastructure per customer.
- Protection holds only if the customer's backend verifies the token. Cursora cannot enforce
  that, so the integration guide has to say it plainly.
- Fail-open trades security for availability: while the verify API is unreachable, a bot that
  posts the form directly is let through. The team accepted this (BR-43); the log and alert on
  every such pass make an outage visible. A missing token is still rejected whenever the API
  answers.
- Cursora sees widget and verify calls, but not requests that skip the widget, so statistics
  cannot count those (OQ-28 in `docs/project-context.md`).
- The Jira epics and specs built on the gate (proxy enforcement of protected routes) need
  revising, together with the site settings that only the gate uses: the address Nginx
  proxies to and the protected routes.
- Still open: which API module issues and verifies tokens.
- Alternatives considered: an Nginx gate run by each customer (infrastructure per customer, the
  cookie domain, closing direct access to the backend), a proxy run by Cursora in front of all
  customer sites (DNS, TLS and all traffic through Cursora, one outage for every site), and both
  the gate and tokens (the most work).
