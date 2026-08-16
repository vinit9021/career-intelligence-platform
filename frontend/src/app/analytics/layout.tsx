import type { ReactNode } from "react";

import { DashboardShell } from "@/components/dashboard/dashboard-shell";

interface AnalyticsLayoutProps {
  children: ReactNode;
}

export default function AnalyticsLayout({ children }: AnalyticsLayoutProps) {
  return <DashboardShell>{children}</DashboardShell>;
}
