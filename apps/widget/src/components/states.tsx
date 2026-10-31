import { Checkbox as CheckboxPrimitive } from "radix-ui";
import { CheckIcon, ClockIcon, XIcon } from "lucide-react";
import { useState } from "react";

import {
  IconBadge,
  LinkButton,
  Panel,
  PrimaryButton,
  SecondaryButton,
  WidgetCard,
} from "@/components/card";

/** Invisible assessment in progress: the visitor does nothing. */
export function VerifyingState() {
  return (
    <WidgetCard state="verifying" title="Security check">
      <Panel role="status" className="flex items-center gap-3">
        <IconBadge className="size-[30px]">
          <span className="bg-cursora-success size-2 animate-pulse rounded-full" />
        </IconBadge>
        <div>
          <p className="text-[13px] font-bold">Verifying automatically…</p>
          <p className="text-[11px]">No action is needed. This should only take a moment.</p>
        </div>
      </Panel>
    </WidgetCard>
  );
}

/** The "I'm not a robot" checkbox. */
export function CheckboxState({ onCheck }: { onCheck?: () => void }) {
  const [checked, setChecked] = useState(false);

  return (
    <WidgetCard state="challenge" title="Quick security check">
      <Panel className="flex items-center gap-3.5 py-3">
        <CheckboxPrimitive.Root
          id="cursora-checkbox"
          checked={checked}
          disabled={checked}
          onCheckedChange={(value) => {
            if (value !== true) return;
            setChecked(true);
            onCheck?.();
          }}
          className="border-cursora-accent data-[state=checked]:bg-cursora-accent focus-visible:ring-cursora-accent/40 grid size-[26px] shrink-0 cursor-pointer place-items-center rounded-md border-2 bg-white text-white outline-none focus-visible:ring-3"
        >
          <CheckboxPrimitive.Indicator>
            <CheckIcon className="size-4" strokeWidth={3} />
          </CheckboxPrimitive.Indicator>
        </CheckboxPrimitive.Root>
        <label htmlFor="cursora-checkbox" className="cursor-pointer text-sm font-semibold">
          I&apos;m not a robot
        </label>
      </Panel>
    </WidgetCard>
  );
}

/** Waiting for the server: the challenge is being loaded or the answer checked. */
export function LoadingState() {
  return (
    <WidgetCard state="loading" title="Checking your browser">
      <Panel role="status" className="flex flex-col items-center gap-1 py-4 text-center">
        <IconBadge className="mb-2 size-[42px]">
          <span className="bg-cursora-accent h-3.5 w-[3px] animate-spin rounded-full" />
        </IconBadge>
        <p className="text-[13px] font-bold">Loading verification challenge…</p>
        <p className="text-[11px]">Keep this window open.</p>
      </Panel>
    </WidgetCard>
  );
}

export function VerifiedState() {
  return (
    <WidgetCard state="verified" title="Access restored">
      <Panel role="status" className="flex flex-col items-center gap-1 py-4 text-center">
        <span
          aria-hidden
          className="bg-cursora-success mb-2 grid size-[42px] place-items-center rounded-full text-white"
        >
          <CheckIcon className="size-5" strokeWidth={1.75} />
        </span>
        <p className="text-sm font-bold">You&apos;re verified</p>
        <p className="text-[11px]">Verification succeeded. Access is restored for this session.</p>
      </Panel>
    </WidgetCard>
  );
}

export function FailedState({
  attempt,
  maxAttempts,
  onTryAgain,
  onTryAnotherWay,
  onContactSupport,
}: {
  attempt: number;
  maxAttempts: number;
  onTryAgain?: () => void;
  onTryAnotherWay?: () => void;
  onContactSupport?: () => void;
}) {
  const retriesLeft = maxAttempts - attempt;
  return (
    <WidgetCard state="failed" title="Verification failed">
      <Panel role="alert" className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <IconBadge className="border-cursora-danger text-cursora-danger size-8">
            <XIcon className="size-4" strokeWidth={1.5} />
          </IconBadge>
          <div>
            <p className="text-[13px] font-bold">Your answer didn&apos;t match</p>
            <p className="text-[11px]">
              Attempt {attempt} of {maxAttempts}
            </p>
          </div>
        </div>
        <p className="text-[11px]">
          Your answer did not match.{" "}
          {retriesLeft === 1
            ? "One retry remains before verification is temporarily blocked."
            : `${retriesLeft} retries remain before verification is temporarily blocked.`}
        </p>
        <div className="flex items-center justify-between">
          <LinkButton onClick={onTryAnotherWay}>Try another way</LinkButton>
          <PrimaryButton disabled={retriesLeft <= 0} onClick={onTryAgain}>Try again</PrimaryButton>
        </div>
        <LinkButton className="self-start" onClick={onContactSupport}>
          Contact support
        </LinkButton>
      </Panel>
    </WidgetCard>
  );
}

export function BlockedState({
  retryInMinutes,
  onRetry,
  onContactSupport,
}: {
  retryInMinutes: number;
  onRetry?: () => void;
  onContactSupport?: () => void;
}) {
  return (
    <WidgetCard state="blocked" title="Temporarily blocked">
      <Panel role="alert" className="flex flex-col gap-3">
        <div className="flex items-center gap-3">
          <IconBadge className="border-cursora-danger text-cursora-danger size-8">
            <ClockIcon className="size-4" strokeWidth={1.5} />
          </IconBadge>
          <div>
            <p className="text-[13px] font-bold">Too many failed attempts</p>
            <p className="text-[11px]">Try again in {retryInMinutes} minutes</p>
          </div>
        </div>
        <p className="text-[11px]">
          This is a temporary pause. You can try again when the {retryInMinutes}-minute block ends.
        </p>
        <div className="flex items-center justify-between">
          <LinkButton onClick={onContactSupport}>Contact support</LinkButton>
          <SecondaryButton onClick={onRetry}>Retry</SecondaryButton>
        </div>
      </Panel>
    </WidgetCard>
  );
}
