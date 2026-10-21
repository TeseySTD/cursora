// IIFE entry: runs synchronously when the host page loads <script src=".../widget.js" data-site-key="...">.
import { mountWidget } from "./mount";

const script = document.currentScript;

if (script instanceof HTMLScriptElement) {
  const siteKey = script.dataset.siteKey;
  if (siteKey) {
    // TODO(team): mount position — right after the <script> tag, or into an explicit container?
    mountWidget(script, { siteKey }, "afterend");
  } else {
    console.error("[cursora] <script> tag is missing the data-site-key attribute");
  }
}
