import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function SitesPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Sites</CardTitle>
        <CardDescription>Sites protected by Cursora and their site keys.</CardDescription>
      </CardHeader>
      <CardContent className="text-muted-foreground text-sm">
        {/* TODO(team): list sites from the tenant module once its API exists. */}
        No sites yet.
      </CardContent>
    </Card>
  );
}
