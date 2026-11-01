import { useEffect, type RefObject } from "react";

/**
 * While `active`, makes the widget modal: everything on the host page outside the widget is
 * `inert` (no focus, no clicks, hidden from screen readers) and focus moves into `ref`.
 * On deactivation the page is restored and focus returns to where it was.
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

    const previousFocus = doc.activeElement;
    dialog.focus({ preventScroll: true });

    return () => {
      for (const element of madeInert) element.removeAttribute("inert");
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) {
        previousFocus.focus({ preventScroll: true });
      }
    };
  }, [ref, active]);
}
