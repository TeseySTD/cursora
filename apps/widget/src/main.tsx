// IIFE entry: runs synchronously when the host page loads <script src=".../widget.js" data-site-key="...">.
import { mountWidget } from "./mount";
import { createSessionLink } from "./lib/session";
import { createApiTransport } from "./lib/signals";

const script = document.currentScript;

if (script instanceof HTMLScriptElement) {
  const siteKey = script.dataset.siteKey;
  if (siteKey) {
    // The API sits next to the widget on the Cursora host: /widget/widget.js -> /api
    // (infra/nginx/conf.d/10-cursora.conf).
    // TODO(team): on a customer's domain this request is cross-site: it needs CORS with
    // credentials, and the session cookie becomes a third-party cookie that the customer's
    // Nginx (auth_request) never receives. Decide how the cookie reaches the customer's domain
    // (open question in CAPTHCA-16).
    const apiBaseUrl = new URL("../api", script.src).href;
    // TODO(team): mount position — right after the <script> tag, or into an explicit container?
    // One session request at a time, shared with the signal transport: batches wait for it, a
    // batch rejected for a lost session (401) opens a new one instead of being retried
    // (CAPTHCA-17 AC4), and an unknown site key stops collection for good.
    const session = createSessionLink(apiBaseUrl, siteKey, {
      onUnknownSite: () => widget.stopSignals(),
    });
    const widget = mountWidget(
      script,
      {
        siteKey,
        view: { state: "hidden" },
        signalTransport: createApiTransport(apiBaseUrl, session),
      },
      "afterend",
    );
    // TODO(team): fail-open or fail-closed when no session can be opened? For now the widget
    // stays hidden (fail-open), and there is no request timeout.
    void session.open().then((opened) => {
      if (opened?.state === "challenge_required") widget.setView({ state: "checkbox" });
    });
  } else {
    console.error("[cursora] <script> tag is missing the data-site-key attribute");
  }
}
