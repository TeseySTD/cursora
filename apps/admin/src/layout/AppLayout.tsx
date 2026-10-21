import { systemHealth } from "@cursora/api-client";
import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router";

import { Separator } from "@/components/ui/separator";

const NAV = [
  { to: "/", label: "Sites", end: true },
  { to: "/sites/demo/settings", label: "Site settings", end: false },
  { to: "/statistics", label: "Statistics", end: false },
];

function ApiStatus() {
  const { data, isError } = useQuery({
    queryKey: ["system", "health"],
    queryFn: async () => (await systemHealth({ throwOnError: true })).data,
  });
  const label = isError ? "unreachable" : (data?.status ?? "…");
  return <p className="text-muted-foreground text-xs">API: {label}</p>;
}

export function AppLayout() {
  return (
    <div className="bg-background text-foreground flex min-h-svh">
      <aside className="bg-sidebar text-sidebar-foreground flex w-56 shrink-0 flex-col gap-4 border-r p-4">
        <span className="text-lg font-semibold">Cursora</span>
        <Separator />
        <nav className="flex flex-col gap-1">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm ${isActive ? "bg-sidebar-accent font-medium" : "hover:bg-sidebar-accent/60"}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto">
          <ApiStatus />
        </div>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
