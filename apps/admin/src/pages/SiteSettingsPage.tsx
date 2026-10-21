import { useState } from "react";
import { useParams } from "react-router";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";

const SENSITIVITY_MIN = 0;
const SENSITIVITY_MAX = 100;

export function SiteSettingsPage() {
  const { siteId } = useParams();
  // UI placeholder only: not loaded from or saved to the API yet.
  // TODO(team): default sensitivity value and persistence via the tenant module.
  const [sensitivity, setSensitivity] = useState(SENSITIVITY_MIN);

  return (
    <Card className="max-w-xl">
      <CardHeader>
        <CardTitle>Site settings</CardTitle>
        <CardDescription>Site: {siteId}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <Label>Sensitivity</Label>
          <span className="text-sm tabular-nums" data-testid="sensitivity-value">
            {sensitivity}
          </span>
        </div>
        <Slider
          min={SENSITIVITY_MIN}
          max={SENSITIVITY_MAX}
          step={1}
          value={[sensitivity]}
          onValueChange={([value]) => setSensitivity(value ?? SENSITIVITY_MIN)}
        />
      </CardContent>
    </Card>
  );
}
