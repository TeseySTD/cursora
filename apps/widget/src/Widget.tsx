import { useRef } from "react";

import { CARD_TITLE_ID } from "@/components/card";
import {
  BlockedState,
  CheckboxState,
  FailedState,
  LoadingState,
  VerifiedState,
  VerifyingState,
} from "@/components/states";
import { useModal } from "@/lib/modal";

/**
 * What the widget shows. "hidden" is the `allow` decision: the visitor sees nothing.
 *
 * TODO(team): who drives these transitions (session state / decision from the API) and the
 * attempt limit and block duration; for now the host of `mountWidget` sets the view.
 */
export type WidgetView =
  | { state: "hidden" }
  | { state: "verifying" }
  | { state: "checkbox" }
  | { state: "loading" }
  | { state: "verified" }
  | { state: "failed"; attempt: number; maxAttempts: number }
  | { state: "blocked"; retryInMinutes: number };

/** Visitor actions the widget reports. */
export interface WidgetActions {
  onCheck?: () => void;
  onTryAgain?: () => void;
  onTryAnotherWay?: () => void;
  onRetry?: () => void;
  onContactSupport?: () => void;
}

export interface WidgetProps extends WidgetActions {
  siteKey: string;
  view: WidgetView;
}

export function Widget({ siteKey, view, ...actions }: WidgetProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  // A failed answer or a block dims the page around the widget. The backdrop is a sibling of the
  // card, not inside it: the card's backdrop-filter would make it the containing block of `fixed`.
  const dimmed = view.state === "failed" || view.state === "blocked";
  // The backdrop blocks the mouse; the widget is then modal so keyboard and screen readers
  // cannot reach the page underneath either.
  useModal(dialogRef, dimmed);

  if (view.state === "hidden") return null;

  // The block is centred on the page; every other state sits in the bottom-right corner.
  const placement =
    view.state === "blocked"
      ? "inset-0 grid place-items-center p-4"
      : "right-4 bottom-4 max-w-[calc(100vw-2rem)]";

  return (
    <div data-site-key={siteKey}>
      {dimmed && (
        <div
          data-cursora-backdrop=""
          aria-hidden
          className="animate-in fade-in fixed inset-0 z-[2147483646] bg-slate-950/55"
        />
      )}
      <div
        ref={dialogRef}
        data-placement={view.state === "blocked" ? "center" : "corner"}
        className={`fixed z-[2147483647] outline-none ${placement}`}
        {...(dimmed && {
          role: "dialog",
          "aria-modal": true,
          "aria-labelledby": CARD_TITLE_ID,
          tabIndex: -1,
        })}
      >
        {renderView(view, actions)}
      </div>
    </div>
  );
}

function renderView(view: WidgetView, actions: WidgetActions) {
  switch (view.state) {
    case "verifying":
      return <VerifyingState />;
    case "checkbox":
      return <CheckboxState onCheck={actions.onCheck} />;
    case "loading":
      return <LoadingState />;
    case "verified":
      return <VerifiedState />;
    case "failed":
      return (
        <FailedState
          attempt={view.attempt}
          maxAttempts={view.maxAttempts}
          onTryAgain={actions.onTryAgain}
          onTryAnotherWay={actions.onTryAnotherWay}
          onContactSupport={actions.onContactSupport}
        />
      );
    case "blocked":
      return (
        <BlockedState
          retryInMinutes={view.retryInMinutes}
          onRetry={actions.onRetry}
          onContactSupport={actions.onContactSupport}
        />
      );
  }
}
