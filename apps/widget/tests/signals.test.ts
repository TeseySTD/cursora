import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createBatcher } from "@/lib/signals/batcher";
import { startCollector } from "@/lib/signals/collector";
import type { SignalTransport } from "@/lib/signals/transport";
import type { Signal } from "@/lib/signals/types";

function stubTransport() {
  const send = vi.fn<SignalTransport["send"]>(() => Promise.resolve());
  return { transport: { send }, send };
}

function pointer(type: string, x: number, y: number, pointerType = "mouse") {
  document.dispatchEvent(
    new PointerEvent(type, { clientX: x, clientY: y, pointerType, bubbles: true }),
  );
}

function move(signal: Signal) {
  return signal.type === "move";
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());

describe("collector", () => {
  it("records the environment once, then pointer moves and clicks", () => {
    const signals: Signal[] = [];
    const stop = startCollector(document, (s) => signals.push(s), { moveIntervalMs: 0 });

    pointer("pointermove", 10, 20, "pen");
    pointer("click", 30, 40, "touch");
    stop();

    expect(signals.map((s) => s.type)).toEqual(["env", "move", "click"]);
    expect(signals[1]).toMatchObject({ x: 10, y: 20, pointer: "pen" });
    expect(signals[2]).toMatchObject({ x: 30, y: 40, button: 0, pointer: "touch" });
  });

  it("records only coarse browser parameters, nothing fingerprint-like", () => {
    const signals: Signal[] = [];
    startCollector(document, (s) => signals.push(s))();

    expect(Object.keys(signals[0] ?? {}).sort()).toEqual([
      "cookieEnabled",
      "devicePixelRatio",
      "maxTouchPoints",
      "t",
      "type",
      "viewport",
      "webdriver",
    ]);
  });

  it("reports input without a known pointer, e.g. a keyboard click, as an empty pointer type", () => {
    const signals: Signal[] = [];
    const stop = startCollector(document, (s) => signals.push(s), { moveIntervalMs: 0 });

    pointer("click", 0, 0, "");
    pointer("pointermove", 0, 0, "eye-tracker");
    stop();

    expect(signals.slice(1).map((s) => ("pointer" in s ? s.pointer : null))).toEqual(["", ""]);
  });

  it("samples pointer moves no more often than moveIntervalMs", () => {
    const signals: Signal[] = [];
    const stop = startCollector(document, (s) => signals.push(s), { moveIntervalMs: 50 });

    pointer("pointermove", 1, 1);
    vi.advanceTimersByTime(10);
    pointer("pointermove", 2, 2);
    vi.advanceTimersByTime(50);
    pointer("pointermove", 3, 3);
    stop();

    expect(signals.filter(move).map((s) => (s.type === "move" ? s.x : 0))).toEqual([1, 3]);
  });

  it("stops listening when stopped", () => {
    const signals: Signal[] = [];
    startCollector(document, (s) => signals.push(s), { moveIntervalMs: 0 })();

    pointer("pointermove", 1, 1);
    expect(signals.filter(move)).toHaveLength(0);
  });
});

describe("batcher", () => {
  const click = { type: "click", t: 0, x: 0, y: 0, button: 0, pointer: "mouse" } as const;
  const batch = (signals: Signal[]) => ({ t: expect.any(Number) as number, signals });

  it("sends buffered signals on the timer with the time on page", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport, { flushIntervalMs: 1000 });

    batcher.push(click);
    batcher.push(click);
    expect(send).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1000);
    expect(send).toHaveBeenCalledExactlyOnceWith(batch([click, click]), { keepalive: false });
    expect(send.mock.calls[0]?.[0].t).toBe(performance.now());

    vi.advanceTimersByTime(1000);
    expect(send).toHaveBeenCalledOnce(); // empty buffer: the timer sends nothing
    batcher.stop();
  });

  it("sends an explicit flush even without signals, for the time on page", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport);

    batcher.flush();
    expect(send).toHaveBeenCalledExactlyOnceWith(batch([]), { keepalive: false });
    batcher.stop();
  });

  it("sends early when the batch is full", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport, { maxBatchSize: 2 });

    batcher.push(click);
    batcher.push(click);
    expect(send).toHaveBeenCalledOnce();
    batcher.stop();
  });

  it("sends with keepalive when the page is hidden, even without signals", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport);
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");

    batcher.push(click);
    document.dispatchEvent(new Event("visibilitychange"));
    document.dispatchEvent(new Event("visibilitychange"));
    expect(send.mock.calls).toEqual([
      [batch([click]), { keepalive: true }],
      [batch([]), { keepalive: true }],
    ]);

    visibility.mockRestore();
    batcher.stop();
  });

  it("sends what is left on stop and then stops the timer", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport, { flushIntervalMs: 1000 });

    batcher.push(click);
    batcher.stop();
    expect(send).toHaveBeenCalledExactlyOnceWith(batch([click]), { keepalive: false });

    batcher.push(click);
    batcher.stop();
    vi.advanceTimersByTime(5000);
    expect(send).toHaveBeenCalledOnce();
  });
});
