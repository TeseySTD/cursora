import { sessionsIngestSignals } from "@cursora/api-client";

import type { SignalTransport } from "./transport";

export interface ApiTransportOptions {
  /**
   * The API has no live session for the batch (no cookie, or the session is unknown or
   * expired): open a new one. Concurrent losses share one call.
   */
  onSessionLost: () => Promise<unknown>;
}

/**
 * Sends signal batches to the Cursora API.
 *
 * The session id stays in the HttpOnly cookie: the request goes with credentials and the browser
 * attaches it. A batch the API rejects is dropped, never retried: after a 401 it belongs to a
 * session that is gone, and a batch that was too large or too frequent would only be rejected
 * again. Only the status is logged, never the batch.
 */
export function createApiTransport(
  apiBaseUrl: string,
  { onSessionLost }: ApiTransportOptions,
): SignalTransport {
  let reopening: Promise<unknown> | undefined;

  const reopenSession = () => {
    reopening ??= onSessionLost()
      .catch((error: unknown) => {
        console.error("[cursora] could not open a session", error);
      })
      .finally(() => {
        reopening = undefined;
      });
    return reopening;
  };

  return {
    async send(batch, { keepalive }) {
      const result = await sessionsIngestSignals({
        baseUrl: apiBaseUrl,
        body: batch,
        credentials: "include",
        keepalive,
        // Read the empty 204 body; left unread, the browser reports the request as aborted.
        parseAs: "text",
      });
      // Undefined when the request never got an answer (network error).
      const response: Response | undefined = result.response;
      if (response?.ok) return;
      if (response?.status === 401) {
        await reopenSession();
        return;
      }
      console.warn(`[cursora] signal batch not accepted (${response?.status ?? "network error"})`);
    },
  };
}
