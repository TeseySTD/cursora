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
  /** Sends the buffered signals now, if any. */
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
  let buffer: Signal[] = [];

  const flush = ({ keepalive = false } = {}) => {
    if (buffer.length === 0) return;
    const signals = buffer;
    buffer = [];
    transport.send({ signals }, { keepalive }).catch((error: unknown) => {
      console.error("[cursora] could not send signals", error);
    });
  };

  const timer = setInterval(flush, flushIntervalMs);
  const onVisibilityChange = () => {
    if (doc.visibilityState === "hidden") flush({ keepalive: true });
  };
  const onPageHide = () => flush({ keepalive: true });
  doc.addEventListener("visibilitychange", onVisibilityChange);
  doc.defaultView?.addEventListener("pagehide", onPageHide);

  return {
    push(signal) {
      buffer.push(signal);
      if (buffer.length >= maxBatchSize) flush();
    },
    flush,
    stop() {
      clearInterval(timer);
      doc.removeEventListener("visibilitychange", onVisibilityChange);
      doc.defaultView?.removeEventListener("pagehide", onPageHide);
      flush();
    },
  };
}
