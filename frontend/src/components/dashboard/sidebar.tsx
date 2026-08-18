"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  AnalyticsIcon,
  ApplicationsIcon,
  BellIcon,
  DashboardIcon,
} from "@/components/dashboard/icons";

const navigation = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: DashboardIcon,
    enabled: true,
  },
  {
    label: "Applications",
    href: "/applications",
    icon: ApplicationsIcon,
    enabled: true,
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: AnalyticsIcon,
    enabled: true,
  },
  {
    label: "Notifications",
    href: "/notifications",
    icon: BellIcon,
    enabled: true,
  },
];

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col bg-slate-950 text-white">
      <div className="flex h-20 items-center border-b border-white/10 px-6">
        <Link href="/dashboard" className="flex items-center gap-3" onClick={onNavigate}>
          <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-500 font-bold shadow-lg shadow-indigo-950/20">
            CI
          </div>

          <div>
            <p className="text-sm leading-none font-semibold">Career Intelligence</p>
            <p className="mt-1 text-xs text-slate-400">AI Career OS</p>
          </div>
        </Link>
      </div>

      <nav className="flex-1 px-4 py-6">
        <p className="px-3 text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
          Workspace
        </p>

        <div className="mt-3 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active =
              item.enabled && (pathname === item.href || pathname.startsWith(`${item.href}/`));

            if (!item.enabled) {
              return (
                <div
                  key={item.label}
                  className="flex cursor-not-allowed items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium text-slate-500"
                  title={`${item.label} will be implemented in a later dashboard milestone`}
                >
                  <Icon className="size-5" />
                  <span className="flex-1">{item.label}</span>
                  <span className="rounded-md border border-slate-700 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-slate-500 uppercase">
                    Soon
                  </span>
                </div>
              );
            }

            return (
              <Link
                key={item.label}
                href={item.href}
                onClick={onNavigate}
                className={[
                  "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-medium transition",
                  active
                    ? "bg-indigo-500 text-white shadow-lg shadow-indigo-950/20"
                    : "text-slate-300 hover:bg-white/5 hover:text-white",
                ].join(" ")}
              >
                <Icon className="size-5" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-2xl bg-white/5 p-4">
          <p className="text-xs font-semibold text-indigo-300">AI Workspace</p>

          <p className="mt-2 text-xs leading-5 text-slate-400">
            Your resume, job matching, ATS optimization, skill gaps, and application intelligence in
            one place.
          </p>
        </div>
      </div>
    </div>
  );
}
