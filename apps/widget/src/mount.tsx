import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { PortalContainerProvider } from "@/lib/portal";
import { noopTransport, startSignals, type SignalTransport } from "@/lib/signals";
import styles from "@/styles.css?inline";
import { Widget, type WidgetActions, type WidgetView } from "@/Widget";

export const HOST_TAG = "cursora-widget";

export interface MountOptions extends WidgetActions {
  siteKey: string;
  /** What to show first. TODO(team): initial view once the API drives it. */
  view?: WidgetView;
  /** Where signal batches go. Defaults to a no-op until the API accepts signals. */
  signalTransport?: SignalTransport;
}

export interface MountedWidget {
  host: HTMLElement;
  shadowRoot: ShadowRoot;
  setView: (view: WidgetView) => void;
  unmount: () => void;
}

/**
 * Mounts the widget into its own Shadow DOM root next to `anchor`.
 *
 * Isolation: the compiled Tailwind CSS is injected into the shadow root only
 * (never into document.head), and portals (popovers, tooltips) render into a
 * container inside the same shadow root so they stay styled and isolated.
 *
 * Behavioural signals are collected from the whole page for as long as the widget is mounted.
 */
export function mountWidget(
  anchor: Element,
  {
    siteKey,
    view = { state: "checkbox" },
    signalTransport = noopTransport,
    ...actions
  }: MountOptions,
  position: InsertPosition = "beforeend",
): MountedWidget {
  // Outside React: collection lasts as long as the mount, whatever the widget renders.
  const stopSignals = startSignals(anchor.ownerDocument, signalTransport);

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
  const render = (current: WidgetView) =>
    root.render(
      <StrictMode>
        <PortalContainerProvider value={portalContainer}>
          <Widget siteKey={siteKey} view={current} {...actions} />
        </PortalContainerProvider>
      </StrictMode>,
    );
  render(view);

  return {
    host,
    shadowRoot,
    setView: render,
    unmount: () => {
      stopSignals();
      root.unmount();
      host.remove();
    },
  };
}
