import { cn } from "cn";
import { ShieldCheckIcon } from "lucide-react";
import type { ComponentProps, ReactNode } from "react";

// TODO(team): Privacy and Security page URLs.
const PRIVACY_URL = "#";
const SECURITY_URL = "#";

/** Id of the card's title. Ids are scoped to the shadow root and one card renders at a time. */
export const CARD_TITLE_ID = "cursora-title";

/** The widget frame shared by every state: brand, title, shield badge, panel slot, footer. */
export function WidgetCard({
  state,
  title,
  children,
}: {
  state: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <section
      data-state={state}
      aria-label={`Cursora: ${title}`}
      // Liquid glass: translucent fill, blurred and saturated backdrop, bright top edge.
      className="text-cursora-blue flex w-[390px] max-w-full flex-col gap-4 rounded-[18px] border border-white/60 bg-gradient-to-br from-white/45 to-white/15 px-[18px] pt-3.5 pb-3 shadow-[inset_0_1px_0_rgb(255_255_255/0.7),0_8px_32px_rgb(15_40_70/0.18)] backdrop-blur-xl backdrop-saturate-150"
    >
      <header className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] leading-tight font-bold">Cursora</p>
          <h2 id={CARD_TITLE_ID} className="text-xl leading-tight font-bold">
            {title}
          </h2>
        </div>
        <span className="grid size-[30px] shrink-0 place-items-center rounded-full border border-white/70 bg-white/60">
          <ShieldCheckIcon aria-hidden className="size-4" strokeWidth={1.75} />
        </span>
      </header>
      {children}
      <footer className="flex items-center justify-between text-[10px]">
        <span>Protected by Cursora</span>
        <span>
          <a href={PRIVACY_URL} target="_blank" rel="noreferrer" className="underline">
            Privacy
          </a>
          {" · "}
          <a href={SECURITY_URL} target="_blank" rel="noreferrer" className="underline">
            Security
          </a>
        </span>
      </footer>
    </section>
  );
}

/** The light inner panel that holds a state's content. */
export function Panel({ className, ...props }: ComponentProps<"div">) {
  return (
    <div
      className={cn("rounded-xl border border-white/70 bg-white/55 p-3.5", className)}
      {...props}
    />
  );
}

/** Round icon badge used by the status panels. */
export function IconBadge({ className, ...props }: ComponentProps<"span">) {
  return (
    <span
      aria-hidden
      className={cn(
        "grid shrink-0 place-items-center rounded-full border border-white bg-white/80",
        className,
      )}
      {...props}
    />
  );
}

export function LinkButton({ className, ...props }: ComponentProps<"button">) {
  return (
    <button
      type="button"
      className={cn("cursor-pointer text-xs underline underline-offset-2", className)}
      {...props}
    />
  );
}

export function PrimaryButton({ className, ...props }: ComponentProps<"button">) {
  return (
    <button
      type="button"
      className={cn(
        "bg-cursora-blue cursor-pointer rounded-xl px-5 py-3 text-sm font-semibold text-white hover:brightness-110",
        className,
      )}
      {...props}
    />
  );
}

export function SecondaryButton({ className, ...props }: ComponentProps<"button">) {
  return (
    <button
      type="button"
      className={cn(
        "cursor-pointer rounded-xl border border-white bg-white/70 px-3.5 py-2 text-sm hover:bg-white/90",
        className,
      )}
      {...props}
    />
  );
}
