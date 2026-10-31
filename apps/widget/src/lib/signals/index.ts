import { createBatcher, type BatcherOptions } from "./batcher";
import { startCollector, type CollectorOptions } from "./collector";
import type { SignalTransport } from "./transport";

export type { Signal, SignalBatch } from "./types";
export { consoleTransport, noopTransport, type SignalTransport } from "./transport";

export type SignalOptions = CollectorOptions & BatcherOptions;

/**
 * Collects behavioural signals on the page and sends them in batches through `transport`.
 * Returns a function that stops collection and sends what is still buffered.
 */
export function startSignals(
  doc: Document,
  transport: SignalTransport,
  options: SignalOptions = {},
): () => void {
  const batcher = createBatcher(doc, transport, options);
  const stopCollector = startCollector(doc, batcher.push, options);
  return () => {
    stopCollector();
    batcher.stop();
  };
}
