import type { ReactNode } from "react";

import { DashboardShell } from "@/components/dashboard/dashboard-shell";

interface NotificationsLayoutProps {
  children: ReactNode;
}

export default function NotificationsLayout({ children }: NotificationsLayoutProps) {
  return <DashboardShell>{children}</DashboardShell>;
}
