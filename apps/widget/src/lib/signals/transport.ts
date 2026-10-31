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

/**
 * Placeholder until the API accepts signals: drops every batch.
 *
 * TODO(team): signal ingestion endpoint and payload. The real transport sends the batch with
 * `credentials: "include"`, so the browser attaches the HttpOnly session cookie.
 */
export const noopTransport: SignalTransport = {
  send: () => Promise.resolve(),
};

/** Dev harness transport: prints each batch to the console. */
export const consoleTransport: SignalTransport = {
  send: (batch, { keepalive }) => {
    console.debug("[cursora] signal batch", { keepalive, ...batch });
    return Promise.resolve();
  },
};
