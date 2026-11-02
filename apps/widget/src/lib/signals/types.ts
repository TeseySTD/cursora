/**
 * Raw behavioural signals the widget collects on the host page.
 *
 * `t` is milliseconds since the page started loading (`performance.now()`), so time on page
 * and the pauses between events can be derived from the timestamps alone.
 *
 * TODO(team): this is the widget-side shape only. The payload the API accepts (and that
 * `packages/features` extracts from) is not defined yet (OQ-15); map to it in the transport.
 */
export type Signal = PointerMoveSignal | ClickSignal | EnvironmentSignal;

export interface PointerMoveSignal {
  type: "move";
  t: number;
  x: number;
  y: number;
  /** "mouse", "touch" or "pen". */
  pointer: string;
}

export interface ClickSignal {
  type: "click";
  t: number;
  x: number;
  y: number;
  button: number;
  pointer: string;
}

/** Browser and device parameters, recorded once when collection starts. */
export interface EnvironmentSignal {
  type: "env";
  t: number;
  language: string;
  languages: readonly string[];
  timezone: string;
  screen: { width: number; height: number; colorDepth: number };
  viewport: { width: number; height: number };
  devicePixelRatio: number;
  hardwareConcurrency: number;
  maxTouchPoints: number;
  cookieEnabled: boolean;
  webdriver: boolean;
}

export interface SignalBatch {
  signals: Signal[];
}
