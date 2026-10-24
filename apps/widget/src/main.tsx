// IIFE entry: runs synchronously when the host page loads <script src=".../widget.js" data-site-key="...">.
import { mountWidget } from "./mount";

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
    mountWidget(script, { siteKey, apiBaseUrl }, "afterend");
  } else {
    console.error("[cursora] <script> tag is missing the data-site-key attribute");
  }
}
