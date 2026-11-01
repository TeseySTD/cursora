import { createBatcher, type BatcherOptions } from "./batcher";
import { startCollector, type CollectorOptions } from "./collector";
import type { SignalTransport } from "./transport";

export type { Signal, SignalBatch } from "./types";
export { consoleTransport, noopTransport, type SignalTransport } from "./transport";

export type SignalOptions = CollectorOptions & BatcherOptions;

export interface SignalSession {
  /** Sends what is buffered now, e.g. when the visitor ticks the checkbox. */
  flush: () => void;
  /** Stops collection and sends what is still buffered. */
  stop: () => void;
}

/** Collects behavioural signals on the page and sends them in batches through `transport`. */
export function startSignals(
  doc: Document,
  transport: SignalTransport,
  options: SignalOptions = {},
): SignalSession {
  const batcher = createBatcher(doc, transport, options);
  const stopCollector = startCollector(doc, batcher.push, options);
  return {
    flush: () => batcher.flush(),
    stop: () => {
      stopCollector();
      batcher.stop();
    },
  };
}
