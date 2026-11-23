import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createApiTransport } from "@/lib/signals/apiTransport";
import type { SignalBatch } from "@/lib/signals/types";

const API = "https://cursora.test/api";
const BATCH: SignalBatch = {
  t: 2000,
  signals: [{ type: "move", t: 100, x: 1, y: 2, pointer: "mouse" }],
};

let fetchMock: ReturnType<typeof vi.fn<typeof fetch>>;

function answer(status: number) {
  fetchMock.mockImplementation(() => Promise.resolve(new Response(null, { status })));
}

beforeEach(() => {
  fetchMock = vi.fn<typeof fetch>();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function sentRequest(index = 0): Request {
  const request = fetchMock.mock.calls[index]?.[0];
  if (!(request instanceof Request)) throw new Error("no request sent");
  return request;
}

describe("API signal transport", () => {
  it("posts the batch with the session cookie", async () => {
    answer(204);
    const onSessionLost = vi.fn(() => Promise.resolve());

    await createApiTransport(API, { onSessionLost }).send(BATCH, { keepalive: true });

    const request = sentRequest();
    expect(request.method).toBe("POST");
    expect(request.url).toBe(`${API}/v1/sessions/signals`);
    expect(request.credentials).toBe("include");
    expect(request.keepalive).toBe(true);
    expect(await request.json()).toEqual(BATCH);
    expect(onSessionLost).not.toHaveBeenCalled();
  });

  it("opens a new session once on 401 and does not resend the batch", async () => {
    answer(401);
    const onSessionLost = vi.fn(() => Promise.resolve());
    const transport = createApiTransport(API, { onSessionLost });

    await Promise.all([
      transport.send(BATCH, { keepalive: false }),
      transport.send(BATCH, { keepalive: false }),
    ]);

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(onSessionLost).toHaveBeenCalledOnce();

    // A later loss opens a session again.
    await transport.send(BATCH, { keepalive: false });
    expect(onSessionLost).toHaveBeenCalledTimes(2);
  });

  it("survives a failure to open the new session", async () => {
    answer(401);
    const error = vi.spyOn(console, "error").mockImplementation(() => {});

    await createApiTransport(API, {
      onSessionLost: () => Promise.reject(new Error("offline")),
    }).send(BATCH, { keepalive: false });

    expect(error).toHaveBeenCalledOnce();
  });

  it.each([413, 422, 429, 500])(
    "drops a batch rejected with %i and logs only the status",
    async (status) => {
      answer(status);
      const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
      const onSessionLost = vi.fn(() => Promise.resolve());

      await createApiTransport(API, { onSessionLost }).send(BATCH, { keepalive: false });

      expect(fetchMock).toHaveBeenCalledOnce();
      expect(onSessionLost).not.toHaveBeenCalled();
      expect(warn).toHaveBeenCalledExactlyOnceWith(
        `[cursora] signal batch not accepted (${status})`,
      );
    },
  );

  it("drops a batch on a network error", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});

    await createApiTransport(API, { onSessionLost: () => Promise.resolve() }).send(BATCH, {
      keepalive: false,
    });

    expect(warn).toHaveBeenCalledExactlyOnceWith(
      "[cursora] signal batch not accepted (network error)",
    );
  });
});
