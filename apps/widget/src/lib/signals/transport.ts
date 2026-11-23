import type { SignalBatch } from "./types";

export interface SendOptions {
  /**
   * The page is being hidden or unloaded: the request must outlive it
   * (`fetch(..., { keepalive: true })` or `navigator.sendBeacon`).
   */
  keepalive: boolean;
}

/** Delivers signal batches to the API. */
export interface SignalTransport {
  send(batch: SignalBatch, options: SendOptions): Promise<void>;
}

/** Drops every batch: for tests and pages that mount the widget without the API. */
export const noopTransport: SignalTransport = {
  send: () => Promise.resolve(),
};

/**
 * Dev harness transport: prints a count per signal type for each batch. Never the batch itself:
 * it holds raw device attributes and pointer coordinates.
 */
export const consoleTransport: SignalTransport = {
  send: (batch, { keepalive }) => {
    const counts: Record<string, number> = {};
    for (const signal of batch.signals) counts[signal.type] = (counts[signal.type] ?? 0) + 1;
    const summary = Object.entries(counts)
      .map(([type, count]) => `${type}: ${count}`)
      .join(", ");
    console.log(`[cursora] signal batch (${summary})`, { keepalive });
    return Promise.resolve();
  },
};
