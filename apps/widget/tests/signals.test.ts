import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { createBatcher } from "@/lib/signals/batcher";
import { startCollector } from "@/lib/signals/collector";
import type { SignalTransport } from "@/lib/signals/transport";
import type { Signal } from "@/lib/signals/types";

function stubTransport() {
  const send = vi.fn<SignalTransport["send"]>(() => Promise.resolve());
  return { transport: { send }, send };
}

function pointer(type: string, x: number, y: number) {
  document.dispatchEvent(new MouseEvent(type, { clientX: x, clientY: y, bubbles: true }));
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

    pointer("pointermove", 10, 20);
    pointer("click", 30, 40);
    stop();

    expect(signals.map((s) => s.type)).toEqual(["env", "move", "click"]);
    expect(signals[1]).toMatchObject({ x: 10, y: 20 });
    expect(signals[2]).toMatchObject({ x: 30, y: 40, button: 0 });
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

  it("sends buffered signals on the timer", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport, { flushIntervalMs: 1000 });

    batcher.push(click);
    batcher.push(click);
    expect(send).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1000);
    expect(send).toHaveBeenCalledExactlyOnceWith({ signals: [click, click] }, { keepalive: false });

    vi.advanceTimersByTime(1000);
    expect(send).toHaveBeenCalledOnce(); // empty buffer: nothing sent
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

  it("sends with keepalive when the page is hidden", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport);
    const visibility = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden");

    batcher.push(click);
    document.dispatchEvent(new Event("visibilitychange"));
    expect(send).toHaveBeenCalledExactlyOnceWith({ signals: [click] }, { keepalive: true });

    visibility.mockRestore();
    batcher.stop();
  });

  it("sends what is left on stop and then stops the timer", () => {
    const { transport, send } = stubTransport();
    const batcher = createBatcher(document, transport, { flushIntervalMs: 1000 });

    batcher.push(click);
    batcher.stop();
    expect(send).toHaveBeenCalledOnce();

    batcher.push(click);
    vi.advanceTimersByTime(5000);
    expect(send).toHaveBeenCalledOnce();
  });
});
