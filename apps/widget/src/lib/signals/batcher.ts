import type { SignalTransport } from "./transport";
import type { Signal } from "./types";

export interface BatcherOptions {
  /** TODO(team): how often batches are sent. */
  flushIntervalMs?: number;
  /** Send early once this many signals are buffered. TODO(team): batch size limit. */
  maxBatchSize?: number;
}

export interface Batcher {
  push(signal: Signal): void;
  /**
   * Sends the buffered signals now, even none: the batch still carries the time on page, which
   * is all there is from a visitor who does not move the pointer.
   */
  flush(options?: { keepalive?: boolean }): void;
  /** Sends what is left and stops the timer and page listeners. */
  stop(): void;
}

const DEFAULT_FLUSH_INTERVAL_MS = 2000;
const DEFAULT_MAX_BATCH_SIZE = 100;

/**
 * Buffers signals and sends them in batches: on a timer, when the buffer is full, and when the
 * page is hidden (the last chance on mobile, where unload events often never fire).
 *
 * The timer skips an empty buffer, so an idle page sends nothing; the other occasions always
 * send, so the time on page reaches the API even without any movement.
 *
 * A batch the transport fails to send is dropped.
 * TODO(team): retry policy for failed batches.
 */
export function createBatcher(
  doc: Document,
  transport: SignalTransport,
  {
    flushIntervalMs = DEFAULT_FLUSH_INTERVAL_MS,
    maxBatchSize = DEFAULT_MAX_BATCH_SIZE,
  }: BatcherOptions = {},
): Batcher {
  const now = () => doc.defaultView?.performance.now() ?? 0;
  let buffer: Signal[] = [];

  const send = ({ keepalive = false } = {}) => {
    const signals = buffer;
    buffer = [];
    transport.send({ t: now(), signals }, { keepalive }).catch((error: unknown) => {
      console.error("[cursora] could not send signals", error);
    });
  };

  const timer = setInterval(() => {
    if (buffer.length > 0) send();
  }, flushIntervalMs);
  const onVisibilityChange = () => {
    if (doc.visibilityState === "hidden") send({ keepalive: true });
  };
  const onPageHide = () => send({ keepalive: true });
  doc.addEventListener("visibilitychange", onVisibilityChange);
  doc.defaultView?.addEventListener("pagehide", onPageHide);

  let stopped = false;
  return {
    push(signal) {
      if (stopped) return;
      buffer.push(signal);
      if (buffer.length >= maxBatchSize) send();
    },
    flush: send,
    stop() {
      if (stopped) return;
      stopped = true;
      clearInterval(timer);
      doc.removeEventListener("visibilitychange", onVisibilityChange);
      doc.defaultView?.removeEventListener("pagehide", onPageHide);
      send();
    },
  };
}
