import type { ReactNode } from "react";

import { DashboardShell } from "@/components/dashboard/dashboard-shell";

interface ApplicationsLayoutProps {
  children: ReactNode;
}

export default function ApplicationsLayout({ children }: ApplicationsLayoutProps) {
  return <DashboardShell>{children}</DashboardShell>;
}
