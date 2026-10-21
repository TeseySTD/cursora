import { useState } from "react";

import { Checkbox } from "@/components/ui/checkbox";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export interface WidgetProps {
  siteKey: string;
}

/**
 * Placeholder UI: renders the "challenge" state (checkbox).
 *
 * TODO(team): widget state machine (collecting signals / challenge / route drag / passed /
 * blocked), copy and i18n, and talking to the API with `siteKey`.
 */
export function Widget({ siteKey }: WidgetProps) {
  const [checked, setChecked] = useState(false);

  return (
    <div
      data-state="challenge"
      data-site-key={siteKey}
      className="bg-background text-foreground inline-flex items-center gap-3 rounded-md border p-3 text-sm shadow-sm"
    >
      <Checkbox
        id="cursora-checkbox"
        checked={checked}
        onCheckedChange={(value) => setChecked(value === true)}
      />
      <label htmlFor="cursora-checkbox" className="cursor-pointer select-none">
        I&apos;m not a robot
      </label>
      <Popover>
        <PopoverTrigger
          aria-label="About this check"
          className="text-muted-foreground hover:text-foreground ml-2 size-5 rounded-full border text-xs"
        >
          ?
        </PopoverTrigger>
        <PopoverContent className="w-56 text-xs">Protected by Cursora.</PopoverContent>
      </Popover>
    </div>
  );
}
