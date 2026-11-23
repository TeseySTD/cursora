import { sessionsIngestSignals } from "@cursora/api-client";

import type { SessionLink } from "@/lib/session";

import type { SignalTransport } from "./transport";

/**
 * Sends signal batches to the Cursora API.
 *
 * The session id stays in the HttpOnly cookie: the request goes with credentials and the browser
 * attaches it. A batch waits while the session is being opened, so it never races the first
 * cookie, and nothing is sent once the API has rejected the site key.
 *
 * A batch the API rejects is dropped, never retried: after a 401 it belongs to a session that is
 * gone (the transport opens a new one), and a batch that was too large or too frequent would only
 * be rejected again. Only the status is logged, never the batch.
 */
export function createApiTransport(apiBaseUrl: string, session: SessionLink): SignalTransport {
  return {
    async send(batch, { keepalive }) {
      await session.settled();
      if (!session.usable) return;

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
        await session.open();
        return;
      }
      console.warn(`[cursora] signal batch not accepted (${response?.status ?? "network error"})`);
    },
  };
}
