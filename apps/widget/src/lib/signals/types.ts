/**
 * Raw behavioural signals the widget collects on the host page.
 *
 * `t` is milliseconds since the page started loading (`performance.now()`), so time on page
 * and the pauses between events can be derived from the timestamps alone.
 *
 * The API accepts exactly this shape (`SignalBatchIn` in the sessions module) and rejects any
 * other field, so the widget can never send typed text or form values.
 * TODO(team): the final signal list (OQ-15).
 */
export type Signal = PointerMoveSignal | ClickSignal | EnvironmentSignal;

/**
 * The input device. "" when there is none: a click from the keyboard or from `element.click()`.
 */
export type PointerType = "mouse" | "touch" | "pen" | "";

export interface PointerMoveSignal {
  type: "move";
  t: number;
  x: number;
  y: number;
  pointer: PointerType;
}

export interface ClickSignal {
  type: "click";
  t: number;
  x: number;
  y: number;
  button: number;
  pointer: PointerType;
}

/**
 * Coarse browser parameters, recorded once when collection starts.
 *
 * Deliberately not a fingerprint: language, timezone, screen size and other high-entropy
 * attributes stay out until fingerprints are sent only as HMAC hashes (BR-32).
 */
export interface EnvironmentSignal {
  type: "env";
  t: number;
  viewport: { width: number; height: number };
  devicePixelRatio: number;
  maxTouchPoints: number;
  webdriver: boolean;
  cookieEnabled: boolean;
}

export interface SignalBatch {
  /** Time on page when the batch was sent, so even an empty batch says how long it has been. */
  t: number;
  signals: Signal[];
}
