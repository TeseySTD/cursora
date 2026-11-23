import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createSessionLink, openSession, UnknownSiteKeyError } from "@/lib/session";
import { createApiTransport } from "@/lib/signals/apiTransport";
import type { SignalBatch } from "@/lib/signals/types";

const API = "https://cursora.test/api";
const SESSIONS = `${API}/v1/sessions`;
const SIGNALS = `${API}/v1/sessions/signals`;
const SESSION = { state: "new", expires_at: "2026-11-23T12:30:00Z" };
const BATCH: SignalBatch = {
  t: 2000,
  signals: [{ type: "move", t: 100, x: 1, y: 2, pointer: "mouse" }],
};

let fetchMock: ReturnType<typeof vi.fn<typeof fetch>>;
/** What the fake API answers, per endpoint. */
let answers: { sessions: () => Promise<Response>; signals: () => Promise<Response> };

const json = (status: number, body: unknown) => Promise.resolve(Response.json(body, { status }));
const empty = (status: number) => Promise.resolve(new Response(null, { status }));

beforeEach(() => {
  answers = { sessions: () => json(201, SESSION), signals: () => empty(204) };
  fetchMock = vi.fn<typeof fetch>((input) => {
    const url = input instanceof Request ? input.url : String(input);
    return url === SIGNALS ? answers.signals() : answers.sessions();
  });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function requests(): Request[] {
  return fetchMock.mock.calls.map(([input]) => input as Request);
}

function urls(): string[] {
  return requests().map((request) => request.url);
}

describe("openSession", () => {
  it("sends the site key with the cookie", async () => {
    await expect(openSession(API, "site-key")).resolves.toEqual(SESSION);

    const [request] = requests();
    expect(request?.url).toBe(SESSIONS);
    expect(request?.credentials).toBe("include");
    expect(await request?.json()).toEqual({ site_key: "site-key" });
  });

  it("tells an unknown site key apart from other failures", async () => {
    answers.sessions = () => json(404, { detail: "Unknown site key" });
    await expect(openSession(API, "nope")).rejects.toBeInstanceOf(UnknownSiteKeyError);

    answers.sessions = () => empty(500);
    await expect(openSession(API, "site-key")).rejects.toThrow("could not open a session (500)");
  });
});

describe("API signal transport", () => {
  it("posts the batch with the session cookie", async () => {
    const session = createSessionLink(API, "site-key");

    await createApiTransport(API, session).send(BATCH, { keepalive: true });

    const [request] = requests();
    expect(request?.method).toBe("POST");
    expect(request?.url).toBe(SIGNALS);
    expect(request?.credentials).toBe("include");
    expect(request?.keepalive).toBe(true);
    expect(await request?.json()).toEqual(BATCH);
  });

  it("waits for the session being opened before sending a batch", async () => {
    let finishOpening = () => {};
    answers.sessions = () =>
      new Promise((resolve) => {
        finishOpening = () => resolve(Response.json(SESSION, { status: 201 }));
      });
    const session = createSessionLink(API, "site-key");
    const opening = session.open();

    const sending = createApiTransport(API, session).send(BATCH, { keepalive: true });
    await Promise.resolve();
    expect(urls()).toEqual([SESSIONS]);

    finishOpening();
    await Promise.all([opening, sending]);
    expect(urls()).toEqual([SESSIONS, SIGNALS]);
  });

  it("opens a new session once on 401 and does not resend the batch", async () => {
    answers.signals = () => empty(401);
    const session = createSessionLink(API, "site-key");
    const transport = createApiTransport(API, session);

    await Promise.all([
      transport.send(BATCH, { keepalive: false }),
      transport.send(BATCH, { keepalive: false }),
    ]);

    expect(urls()).toEqual([SIGNALS, SIGNALS, SESSIONS]);
  });

  it("sends nothing more once the site key is unknown", async () => {
    answers.sessions = () => json(404, { detail: "Unknown site key" });
    vi.spyOn(console, "error").mockImplementation(() => {});
    const onUnknownSite = vi.fn();
    const session = createSessionLink(API, "nope", { onUnknownSite });
    const transport = createApiTransport(API, session);

    await session.open();
    await transport.send(BATCH, { keepalive: false });
    await session.open();

    expect(session.usable).toBe(false);
    expect(onUnknownSite).toHaveBeenCalledOnce();
    expect(urls()).toEqual([SESSIONS]);
  });

  it("keeps trying after a session failure that is not about the site key", async () => {
    answers.sessions = () => Promise.reject(new TypeError("Failed to fetch"));
    vi.spyOn(console, "error").mockImplementation(() => {});
    const session = createSessionLink(API, "site-key");

    await expect(session.open()).resolves.toBeUndefined();
    expect(session.usable).toBe(true);

    answers.sessions = () => json(201, SESSION);
    await expect(session.open()).resolves.toEqual(SESSION);
  });

  it.each([413, 422, 429, 500])(
    "drops a batch rejected with %i and logs only the status",
    async (status) => {
      answers.signals = () => empty(status);
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

      await createApiTransport(API, createSessionLink(API, "site-key")).send(BATCH, {
        keepalive: false,
      });

      expect(urls()).toEqual([SIGNALS]);
      expect(warn).toHaveBeenCalledExactlyOnceWith(
        `[cursora] signal batch not accepted (${status})`,
      );
    },
  );

  it("drops a batch on a network error", async () => {
    answers.signals = () => Promise.reject(new TypeError("Failed to fetch"));
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    await createApiTransport(API, createSessionLink(API, "site-key")).send(BATCH, {
      keepalive: false,
    });

    expect(warn).toHaveBeenCalledExactlyOnceWith(
      "[cursora] signal batch not accepted (network error)",
    );
  });
});
