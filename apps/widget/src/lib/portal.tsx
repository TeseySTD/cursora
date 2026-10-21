import { createContext, useContext } from "react";

/**
 * Element inside the widget's shadow root that shadcn/Radix portals must target.
 * Every shadcn component that renders a Portal (Popover, Tooltip, Dialog, Select, ...)
 * must pass `container={usePortalContainer()}`, otherwise it renders into
 * document.body — outside the shadow root and without the widget's styles.
 */
const PortalContainerContext = createContext<HTMLElement | null>(null);

export const PortalContainerProvider = PortalContainerContext.Provider;

// eslint-disable-next-line react-refresh/only-export-components -- hook next to its context
export function usePortalContainer(): HTMLElement | undefined {
  return useContext(PortalContainerContext) ?? undefined;
}
