import { sessionsEnsureSession, type SessionResponse } from "@cursora/api-client";

/**
 * Restores the visitor's server-side session on the site or creates a new one.
 *
 * The session id lives only in an HttpOnly cookie, so the widget never sees it: it just sends
 * the request with credentials and the browser attaches (or stores) the cookie.
 */
export async function openSession(apiBaseUrl: string, siteKey: string): Promise<SessionResponse> {
  const { data } = await sessionsEnsureSession({
    baseUrl: apiBaseUrl,
    body: { site_key: siteKey },
    credentials: "include",
    throwOnError: true,
  });
  return data;
}
