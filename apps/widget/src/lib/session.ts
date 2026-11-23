import { sessionsEnsureSession, type SessionResponse } from "@cursora/api-client";

/** The API knows no site with the widget's site key (404). Retrying cannot help. */
export class UnknownSiteKeyError extends Error {
  constructor() {
    super("unknown site key");
    this.name = "UnknownSiteKeyError";
  }
}

/**
 * Restores the visitor's server-side session on the site or creates a new one.
 *
 * The session id lives only in an HttpOnly cookie, so the widget never sees it: it just sends
 * the request with credentials and the browser attaches (or stores) the cookie.
 */
export async function openSession(apiBaseUrl: string, siteKey: string): Promise<SessionResponse> {
  const { data, response } = await sessionsEnsureSession({
    baseUrl: apiBaseUrl,
    body: { site_key: siteKey },
    credentials: "include",
  });
  if (data) return data;
  // Undefined when the request never got an answer (network error).
  const status = (response as Response | undefined)?.status;
  if (status === 404) throw new UnknownSiteKeyError();
  throw new Error(`could not open a session (${status ?? "network error"})`);
}

/** The widget's one connection to its session, shared by the page load and the signal transport. */
export interface SessionLink {
  /**
   * Opens the session, or restores it from the cookie. Calls while a request is in flight share
   * it. Resolves to the session, or to undefined if it could not be opened.
   */
  open(): Promise<SessionResponse | undefined>;
  /** Resolves once no session request is in flight, so a request sent then carries its cookie. */
  settled(): Promise<unknown>;
  /** False once the API rejected the site key: nothing more should be sent for this page. */
  readonly usable: boolean;
}

export interface SessionLinkOptions {
  /** The site key is unknown to the API; called once. */
  onUnknownSite?: () => void;
}

export function createSessionLink(
  apiBaseUrl: string,
  siteKey: string,
  { onUnknownSite }: SessionLinkOptions = {},
): SessionLink {
  let inFlight: Promise<SessionResponse | undefined> | undefined;
  let usable = true;

  return {
    get usable() {
      return usable;
    },
    open() {
      if (!usable) return Promise.resolve(undefined);
      inFlight ??= openSession(apiBaseUrl, siteKey)
        .catch((error: unknown) => {
          console.error("[cursora] could not open a session", error);
          if (error instanceof UnknownSiteKeyError) {
            usable = false;
            onUnknownSite?.();
          }
          return undefined;
        })
        .finally(() => {
          inFlight = undefined;
        });
      return inFlight;
    },
    settled() {
      return inFlight ?? Promise.resolve();
    },
  };
}
