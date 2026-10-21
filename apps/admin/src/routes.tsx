import type { RouteObject } from "react-router";

import { AppLayout } from "@/layout/AppLayout";
import { SiteSettingsPage } from "@/pages/SiteSettingsPage";
import { SitesPage } from "@/pages/SitesPage";
import { StatisticsPage } from "@/pages/StatisticsPage";

export const routes: RouteObject[] = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <SitesPage /> },
      { path: "sites/:siteId/settings", element: <SiteSettingsPage /> },
      { path: "statistics", element: <StatisticsPage /> },
    ],
  },
];
