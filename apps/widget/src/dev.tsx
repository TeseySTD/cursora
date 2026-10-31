// Dev harness entry (index.html). Module scripts have no document.currentScript, so mount explicitly.
import { consoleTransport } from "./lib/signals";
import { mountWidget } from "./mount";
import type { WidgetView } from "./Widget";

// Sample data for previewing every state; the real values will come from the API.
const VIEWS: Record<string, WidgetView> = {
  "Security check": { state: "verifying" },
  "Quick security check": { state: "checkbox" },
  "Checking your browser": { state: "loading" },
  "Access restored": { state: "verified" },
  "Verification failed": { state: "failed", attempt: 2, maxAttempts: 3 },
  "Temporarily blocked": { state: "blocked", retryInMinutes: 14 },
  Hidden: { state: "hidden" },
};

const slot = document.getElementById("cursora-slot");
const switcher = document.getElementById("dev-states");

if (slot) {
  const show = (view: WidgetView) => {
    widget.setView(view);
    for (const button of switcher?.querySelectorAll("button") ?? []) {
      button.setAttribute("aria-pressed", String(VIEWS[button.textContent] === view));
    }
  };

  // Fake flow so the buttons do something: checkbox -> loading -> verified, retry -> checkbox.
  const widget = mountWidget(slot, {
    siteKey: "dev-site-key",
    view: VIEWS["Quick security check"],
    signalTransport: consoleTransport,
    onCheck: () => {
      show(VIEWS["Checking your browser"]!);
      setTimeout(() => show(VIEWS["Access restored"]!), 1500);
    },
    onTryAgain: () => show(VIEWS["Quick security check"]!),
    onRetry: () => show(VIEWS["Quick security check"]!),
    onTryAnotherWay: () => console.debug("[cursora dev] try another way"),
    onContactSupport: () => console.debug("[cursora dev] contact support"),
  });

  for (const [label, view] of Object.entries(VIEWS)) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => show(view));
    switcher?.append(button);
  }
  show(VIEWS["Quick security check"]!);
}
