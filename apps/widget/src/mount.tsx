import { StrictMode, Suspense } from "react";
import { createRoot } from "react-dom/client";

import { PortalContainerProvider } from "@/lib/portal";
import { openSession } from "@/lib/session";
import styles from "@/styles.css?inline";
import { Widget } from "@/Widget";

export const HOST_TAG = "cursora-widget";

export interface MountOptions {
  siteKey: string;
  /** Base URL of the Cursora API, e.g. "https://<cursora-host>/api". */
  apiBaseUrl: string;
}

export interface MountedWidget {
  host: HTMLElement;
  shadowRoot: ShadowRoot;
  unmount: () => void;
}

/**
 * Mounts the widget into its own Shadow DOM root next to `anchor`.
 *
 * Isolation: the compiled Tailwind CSS is injected into the shadow root only
 * (never into document.head), and portals (popovers, tooltips) render into a
 * container inside the same shadow root so they stay styled and isolated.
 */
export function mountWidget(
  anchor: Element,
  { siteKey, apiBaseUrl }: MountOptions,
  position: InsertPosition = "beforeend",
): MountedWidget {
  // Once per mount, outside React: StrictMode runs effects twice in development, which would
  // race two "create" requests for a visitor without a session cookie.
  const session = openSession(apiBaseUrl).catch((error: unknown) => {
    console.error("[cursora] could not open a session", error);
    return null;
  });

  // A custom tag name so generic host selectors (div, span, ...) do not hit the host element.
  const host = document.createElement(HOST_TAG);
  anchor.insertAdjacentElement(position, host);

  // TODO(team): "open" eases debugging/testing; decide whether production uses "closed".
  const shadowRoot = host.attachShadow({ mode: "open" });

  const style = document.createElement("style");
  style.textContent = styles;
  const appContainer = document.createElement("div");
  const portalContainer = document.createElement("div");
  portalContainer.dataset.cursoraPortal = "";
  shadowRoot.append(style, appContainer, portalContainer);

  const root = createRoot(appContainer);
  root.render(
    <StrictMode>
      <PortalContainerProvider value={portalContainer}>
        <Suspense fallback={null}>
          <Widget siteKey={siteKey} session={session} />
        </Suspense>
      </PortalContainerProvider>
    </StrictMode>,
  );

  return {
    host,
    shadowRoot,
    unmount: () => {
      root.unmount();
      host.remove();
    },
  };
}
