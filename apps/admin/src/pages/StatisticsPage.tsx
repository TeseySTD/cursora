import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function StatisticsPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Statistics</CardTitle>
        <CardDescription>Aggregate allow / challenge / block counts.</CardDescription>
      </CardHeader>
      <CardContent className="text-muted-foreground text-sm">
        {/* TODO(team): which aggregates and time ranges the insights module exposes. */}
        No data yet.
      </CardContent>
    </Card>
  );
}
