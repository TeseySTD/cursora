import { act, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { HOST_TAG, mountWidget, type MountedWidget } from "@/mount";

let mounted: MountedWidget | undefined;

async function mount(): Promise<MountedWidget> {
  await act(async () => {
    mounted = mountWidget(document.body, { siteKey: "test-key" });
  });
  return mounted!;
}

afterEach(() => {
  act(() => mounted?.unmount());
  mounted = undefined;
});

describe("widget (smoke)", () => {
  it("renders the challenge checkbox inside a shadow root", async () => {
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
    const { shadowRoot } = await mount();
    const css = shadowRoot.querySelector("style")?.textContent ?? "";
    expect(css).toContain(":host");
    expect(css).not.toMatch(/:root\b/);
    expect(document.head.querySelectorAll("style")).toHaveLength(0);
  });

  it("renders popover portals inside the shadow root", async () => {
    const { shadowRoot } = await mount();
    const ui = within(shadowRoot as unknown as HTMLElement);

    await userEvent.click(ui.getByRole("button", { name: /about this check/i }));

    const content = await ui.findByText("Protected by Cursora.");
    expect(content.closest("[data-cursora-portal]")).not.toBeNull();
    expect(within(document.body).queryByText("Protected by Cursora.")).toBeNull();
  });
});
