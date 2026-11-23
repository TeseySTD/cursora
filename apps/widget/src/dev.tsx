// Dev harness entry (index.html). Module scripts have no document.currentScript, so mount explicitly.
import { createSessionLink } from "./lib/session";
import { consoleTransport, createApiTransport, type SignalTransport } from "./lib/signals";
import { mountWidget } from "./mount";
import type { WidgetView } from "./Widget";

// With ?siteKey=<key> (from `pnpm api:create-site`), the harness opens a real session and sends
// signals to the API through the dev proxy (`pnpm dev:api` must run). Without it, signal batches
// are only summarised in the console.
const siteKey = new URLSearchParams(location.search).get("siteKey");
const apiBaseUrl = new URL("/api", location.href).href;

function devSignalTransport(): SignalTransport {
  if (!siteKey) return consoleTransport;
  const session = createSessionLink(apiBaseUrl, siteKey, {
    // The harness keeps running for its demo states; only the signals stop.
    onUnknownSite: () => console.error("[cursora dev] unknown site key: signals are not sent"),
  });
  void session.open();
  return createApiTransport(apiBaseUrl, session);
}

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
  let pendingTransition: ReturnType<typeof setTimeout> | undefined;

  const show = (view: WidgetView) => {
    clearTimeout(pendingTransition);
    widget.setView(view);
    for (const button of switcher?.querySelectorAll("button") ?? []) {
      button.setAttribute("aria-pressed", String(VIEWS[button.textContent] === view));
    }
  };

  const showAfter = (view: WidgetView, delayMs: number) => {
    clearTimeout(pendingTransition);
    pendingTransition = setTimeout(() => show(view), delayMs);
  };

  // Fake flow standing in for the API: on page load "Security check" while signals are collected,
  // then the checkbox; checkbox -> loading -> verified; try again / retry -> checkbox.
  const widget = mountWidget(slot, {
    siteKey: siteKey ?? "dev-site-key",
    view: VIEWS["Security check"],
    signalTransport: devSignalTransport(),
    onCheck: () => {
      show(VIEWS["Checking your browser"]!);
      showAfter(VIEWS["Access restored"]!, 1500);
    },
    onTryAgain: () => show(VIEWS["Quick security check"]!),
    onRetry: () => show(VIEWS["Quick security check"]!),
    onTryAnotherWay: () => console.debug("[cursora dev] try another way"),
    onContactSupport: () => console.debug("[cursora dev] contact support"),
  });

  // The widget makes the rest of the page inert while it is modal (failed, blocked); keep the
  // dev switcher usable so the states can still be switched.
  if (switcher) {
    new MutationObserver(() => switcher.removeAttribute("inert")).observe(switcher, {
      attributes: true,
      attributeFilter: ["inert"],
    });
  }

  for (const [label, view] of Object.entries(VIEWS)) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => show(view));
    switcher?.append(button);
  }
  show(VIEWS["Security check"]!);
  showAfter(VIEWS["Quick security check"]!, 3000);
}
