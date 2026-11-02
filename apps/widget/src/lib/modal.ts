import { useEffect, type RefObject } from "react";

const FOCUSABLE = [
  "button:not([disabled])",
  "a[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  '[tabindex]:not([tabindex="-1"])',
].join(",");

/**
 * The focused element, looking inside shadow roots: for focus inside the widget,
 * `document.activeElement` is only the (non-focusable) shadow host.
 */
function deepActiveElement(doc: Document): Element | null {
  let active = doc.activeElement;
  while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
  return active;
}

/**
 * While `active`, makes the widget modal: everything on the host page outside the widget is
 * `inert` (no focus, no clicks, hidden from screen readers) and focus moves into `ref`.
 *
 * On deactivation the page is restored and focus returns to where it was. If that element is
 * gone (typically a control of the previous widget view, unmounted by the view change), focus
 * moves to the first focusable element of the widget's new view instead of being lost.
 *
 * The widget lives in a shadow root, so "outside" is computed from the shadow host: every
 * sibling of the host and of each of its ancestors, up to `<body>`.
 */
export function useModal(ref: RefObject<HTMLElement | null>, active: boolean) {
  useEffect(() => {
    const dialog = ref.current;
    if (!active || !dialog) return;

    const doc = dialog.ownerDocument;
    const root = dialog.getRootNode();
    const previousFocus = deepActiveElement(doc);
    const madeInert: Element[] = [];
    let node: Element = root instanceof ShadowRoot ? root.host : dialog;
    while (node !== doc.body && node.parentElement) {
      for (const sibling of node.parentElement.children) {
        // Leave elements the page made inert itself alone, so we never un-inert them.
        if (sibling === node || sibling.hasAttribute("inert")) continue;
        sibling.setAttribute("inert", "");
        madeInert.push(sibling);
      }
      node = node.parentElement;
    }

    dialog.focus({ preventScroll: true });

    return () => {
      for (const element of madeInert) element.removeAttribute("inert");

      const fallback = dialog.isConnected ? dialog.querySelector(FOCUSABLE) : null;
      for (const target of [previousFocus, fallback]) {
        // <body> is "nothing focused" (e.g. the ticked checkbox disabled itself): not a target.
        if (!(target instanceof HTMLElement) || !target.isConnected || target === doc.body) {
          continue;
        }
        target.focus({ preventScroll: true });
        if (deepActiveElement(doc) === target) break;
      }
    };
  }, [ref, active]);
}
