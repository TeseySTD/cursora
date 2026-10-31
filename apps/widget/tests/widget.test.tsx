import { act, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { PortalContainerProvider } from "@/lib/portal";
import type { SignalTransport } from "@/lib/signals";
import { HOST_TAG, mountWidget, type MountedWidget, type MountOptions } from "@/mount";

let mounted: MountedWidget | undefined;

async function mount(options: Partial<MountOptions> = {}): Promise<MountedWidget> {
  await act(async () => {
    mounted = mountWidget(document.body, { siteKey: "test-key", ...options });
  });
  return mounted!;
}

function query(shadowRoot: ShadowRoot) {
  return within(shadowRoot as unknown as HTMLElement);
}

afterEach(() => {
  act(() => mounted?.unmount());
  mounted = undefined;
});

describe("widget (smoke)", () => {
  it("renders the challenge checkbox inside a shadow root", async () => {
    const onCheck = vi.fn();
    const { host, shadowRoot } = await mount({ onCheck });
    expect(host.tagName.toLowerCase()).toBe(HOST_TAG);

    const checkbox = query(shadowRoot).getByRole("checkbox", { name: /not a robot/i });
    expect(checkbox).not.toBeChecked();

    await userEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    expect(onCheck).toHaveBeenCalledOnce();
    // Nothing leaks into the light DOM.
    expect(document.body.querySelector("[role=checkbox]")).toBeNull();
  });

  it("sends the collected signals, the click included, as soon as the checkbox is ticked", async () => {
    const send = vi.fn<SignalTransport["send"]>(() => Promise.resolve());
    const { shadowRoot } = await mount({ signalTransport: { send } });
    expect(send).not.toHaveBeenCalled();

    await userEvent.click(query(shadowRoot).getByRole("checkbox", { name: /not a robot/i }));

    expect(send).toHaveBeenCalledOnce();
    const [batch, options] = send.mock.calls[0]!;
    expect(batch.signals.map((s) => s.type)).toContain("env");
    expect(batch.signals.at(-1)?.type).toBe("click");
    expect(options).toEqual({ keepalive: false });
  });

  it("injects the compiled CSS into the shadow root, not document.head", async () => {
    const { shadowRoot } = await mount();
    const css = shadowRoot.querySelector("style")?.textContent ?? "";
    expect(css).toContain(":host");
    expect(css).not.toMatch(/:root\b/);
    expect(document.head.querySelectorAll("style")).toHaveLength(0);
  });

  it("renders popover portals inside the shadow root", async () => {
    // The widget has no popover right now; check the portal plumbing directly.
    const host = document.body.appendChild(document.createElement("div"));
    const shadowRoot = host.attachShadow({ mode: "open" });
    const app = shadowRoot.appendChild(document.createElement("div"));
    const portal = shadowRoot.appendChild(document.createElement("div"));
    portal.dataset.cursoraPortal = "";
    const root = createRoot(app);
    act(() =>
      root.render(
        <StrictMode>
          <PortalContainerProvider value={portal}>
            <Popover>
              <PopoverTrigger>About</PopoverTrigger>
              <PopoverContent>Popover body</PopoverContent>
            </Popover>
          </PortalContainerProvider>
        </StrictMode>,
      ),
    );

    await userEvent.click(query(shadowRoot).getByRole("button", { name: "About" }));

    const content = await query(shadowRoot).findByText("Popover body");
    expect(content.closest("[data-cursora-portal]")).not.toBeNull();
    expect(within(document.body).queryByText("Popover body")).toBeNull();
    act(() => root.unmount());
    host.remove();
  });
});

describe("widget states", () => {
  it.each([
    [{ state: "verifying" } as const, "Security check"],
    [{ state: "checkbox" } as const, "Quick security check"],
    [{ state: "loading" } as const, "Checking your browser"],
    [{ state: "verified" } as const, "Access restored"],
    [{ state: "failed", attempt: 2, maxAttempts: 3 } as const, "Verification failed"],
    [{ state: "blocked", retryInMinutes: 14 } as const, "Temporarily blocked"],
  ])("renders %o with its title", async (view, title) => {
    const { shadowRoot } = await mount({ view });
    expect(query(shadowRoot).getByRole("heading", { name: title })).toBeInTheDocument();
  });

  it("shows nothing when hidden (allow)", async () => {
    const { shadowRoot } = await mount({ view: { state: "hidden" } });
    expect(shadowRoot.querySelector("[data-state]")).toBeNull();
  });

  it("dims the page only when the answer failed or the visitor is blocked", async () => {
    const widget = await mount();
    const backdrop = () => widget.shadowRoot.querySelector("[data-cursora-backdrop]");
    expect(backdrop()).toBeNull();

    act(() => widget.setView({ state: "failed", attempt: 2, maxAttempts: 3 }));
    expect(backdrop()).not.toBeNull();

    act(() => widget.setView({ state: "blocked", retryInMinutes: 14 }));
    expect(backdrop()).not.toBeNull();

    act(() => widget.setView({ state: "checkbox" }));
    expect(backdrop()).toBeNull();
  });

  it("sits in the corner, except the block, which is centred", async () => {
    const widget = await mount();
    const placement = () =>
      widget.shadowRoot.querySelector<HTMLElement>("[data-placement]")?.dataset.placement;
    expect(placement()).toBe("corner");

    act(() => widget.setView({ state: "failed", attempt: 2, maxAttempts: 3 }));
    expect(placement()).toBe("corner");

    act(() => widget.setView({ state: "blocked", retryInMinutes: 14 }));
    expect(placement()).toBe("center");
  });

  it("switches views with setView", async () => {
    const widget = await mount();
    act(() => widget.setView({ state: "verified" }));
    expect(query(widget.shadowRoot).getByText("You're verified")).toBeInTheDocument();
  });

  it("reports the failed state's actions", async () => {
    const onTryAgain = vi.fn();
    const onTryAnotherWay = vi.fn();
    const { shadowRoot } = await mount({
      view: { state: "failed", attempt: 2, maxAttempts: 3 },
      onTryAgain,
      onTryAnotherWay,
    });
    const ui = query(shadowRoot);
    expect(ui.getByText("Attempt 2 of 3")).toBeInTheDocument();
    expect(ui.getByText(/One retry remains/)).toBeInTheDocument();

    await userEvent.click(ui.getByRole("button", { name: "Try again" }));
    await userEvent.click(ui.getByRole("button", { name: "Try another way" }));
    expect(onTryAgain).toHaveBeenCalledOnce();
    expect(onTryAnotherWay).toHaveBeenCalledOnce();
  });

  it("shows the block duration and reports retry", async () => {
    const onRetry = vi.fn();
    const { shadowRoot } = await mount({ view: { state: "blocked", retryInMinutes: 14 }, onRetry });
    const ui = query(shadowRoot);
    expect(ui.getByText("Try again in 14 minutes")).toBeInTheDocument();

    await userEvent.click(ui.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledOnce();
  });
});
