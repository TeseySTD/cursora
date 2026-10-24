import type { SessionState } from "@cursora/api-client";
import { act, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HOST_TAG, mountWidget, type MountedWidget } from "@/mount";

const API_BASE_URL = "http://localhost/api";

let mounted: MountedWidget | undefined;

/** Stubs fetch so that POST /v1/sessions answers with a session in `state`. */
function stubSession(state: SessionState) {
  const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () =>
    Response.json({ state, expires_at: "2026-10-24T18:30:00Z" }, { status: 201 }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** Mounts the widget and lets the session request settle. */
async function mount(): Promise<MountedWidget> {
  await act(async () => {
    mounted = mountWidget(document.body, { siteKey: "test-key", apiBaseUrl: API_BASE_URL });
  });
  await act(() => new Promise((resolve) => setTimeout(resolve, 0)));
  return mounted!;
}

afterEach(() => {
  act(() => mounted?.unmount());
  mounted = undefined;
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("widget session", () => {
  it("opens the session once, with credentials, and shows nothing for a new session", async () => {
    const fetchMock = stubSession("new");
    const { shadowRoot } = await mount();

    // Once, even though StrictMode mounts components twice in development.
    expect(fetchMock).toHaveBeenCalledOnce();
    const request = fetchMock.mock.calls[0]![0];
    expect(request.method).toBe("POST");
    expect(request.url).toBe(`${API_BASE_URL}/v1/sessions`);
    // The session id is in an HttpOnly cookie: the browser only sends it with credentials.
    expect(request.credentials).toBe("include");

    expect(shadowRoot.querySelector("[data-state]")).toBeNull();
  });

  it("shows nothing when the session cannot be opened", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("unavailable", { status: 503 })),
    );
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    const { shadowRoot } = await mount();

    expect(consoleError).toHaveBeenCalledWith(
      "[cursora] could not open a session",
      expect.anything(),
    );
    expect(shadowRoot.querySelector("[data-state]")).toBeNull();
  });
});

describe("widget (smoke)", () => {
  it("renders the challenge checkbox inside a shadow root", async () => {
    stubSession("challenge_required");
    const { host, shadowRoot } = await mount();
    expect(host.tagName.toLowerCase()).toBe(HOST_TAG);

    const ui = within(shadowRoot as unknown as HTMLElement);
    const checkbox = ui.getByRole("checkbox", { name: /not a robot/i });
    expect(checkbox).not.toBeChecked();

    await userEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    // Nothing leaks into the light DOM.
    expect(document.body.querySelector("[role=checkbox]")).toBeNull();
  });

  it("injects the compiled CSS into the shadow root, not document.head", async () => {
    stubSession("new");
    const { shadowRoot } = await mount();
    const css = shadowRoot.querySelector("style")?.textContent ?? "";
    expect(css).toContain(":host");
    expect(css).not.toMatch(/:root\b/);
    expect(document.head.querySelectorAll("style")).toHaveLength(0);
  });

  it("renders popover portals inside the shadow root", async () => {
    stubSession("challenge_required");
    const { shadowRoot } = await mount();
    const ui = within(shadowRoot as unknown as HTMLElement);

    await userEvent.click(ui.getByRole("button", { name: /about this check/i }));

    const content = await ui.findByText("Protected by Cursora.");
    expect(content.closest("[data-cursora-portal]")).not.toBeNull();
    expect(within(document.body).queryByText("Protected by Cursora.")).toBeNull();
  });
});
