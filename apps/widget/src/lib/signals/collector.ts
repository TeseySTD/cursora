import type { EnvironmentSignal, PointerType, Signal } from "./types";

export interface CollectorOptions {
  /**
   * Minimum time between two recorded pointer moves, in ms. pointermove fires at the display
   * refresh rate, which is more than the batches need.
   *
   * TODO(team): sampling rate for cursor movement.
   */
  moveIntervalMs?: number;
}

const DEFAULT_MOVE_INTERVAL_MS = 50;

/**
 * Starts listening for behavioural signals on the whole host page (not just the widget:
 * the visitor moves the cursor over the customer's site). Returns a function that stops it.
 *
 * Events from inside the widget's shadow root reach `document` retargeted to the host element,
 * with their real coordinates, so clicks on the checkbox are recorded too.
 */
export function startCollector(
  doc: Document,
  onSignal: (signal: Signal) => void,
  { moveIntervalMs = DEFAULT_MOVE_INTERVAL_MS }: CollectorOptions = {},
): () => void {
  const win = doc.defaultView;
  if (!win) return () => {};

  onSignal(readEnvironment(win));

  let lastMoveAt = -Infinity;
  const onPointerMove = (event: PointerEvent) => {
    const t = win.performance.now();
    if (t - lastMoveAt < moveIntervalMs) return;
    lastMoveAt = t;
    onSignal({
      type: "move",
      t,
      x: event.clientX,
      y: event.clientY,
      pointer: toPointerType(event.pointerType),
    });
  };

  const onClick = (event: MouseEvent) => {
    onSignal({
      type: "click",
      t: win.performance.now(),
      x: event.clientX,
      y: event.clientY,
      button: event.button,
      // `click` is a PointerEvent in current browsers; older ones fire a plain MouseEvent.
      pointer: "pointerType" in event ? toPointerType(event.pointerType) : "mouse",
    });
  };

  // Passive and capturing: never delay scrolling, and record events the page stops propagating.
  const listenerOptions = { capture: true, passive: true } as const;
  doc.addEventListener("pointermove", onPointerMove, listenerOptions);
  doc.addEventListener("click", onClick, listenerOptions);

  return () => {
    doc.removeEventListener("pointermove", onPointerMove, listenerOptions);
    doc.removeEventListener("click", onClick, listenerOptions);
  };
}

/** The API accepts only the standard pointer types; anything else is reported as none. */
function toPointerType(value: unknown): PointerType {
  return value === "mouse" || value === "touch" || value === "pen" ? value : "";
}

function readEnvironment(win: Window): EnvironmentSignal {
  const { navigator } = win;
  return {
    type: "env",
    t: win.performance.now(),
    viewport: { width: win.innerWidth, height: win.innerHeight },
    devicePixelRatio: win.devicePixelRatio,
    maxTouchPoints: navigator.maxTouchPoints,
    webdriver: navigator.webdriver,
    cookieEnabled: navigator.cookieEnabled,
  };
}
