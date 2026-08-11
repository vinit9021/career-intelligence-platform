"use client";

import type { ReactNode } from "react";
import { useEffect, useState, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";

import { CloseIcon } from "@/components/dashboard/icons";
import { Sidebar } from "@/components/dashboard/sidebar";
import { Topbar } from "@/components/dashboard/topbar";
import { hasAuthSession } from "@/lib/auth-storage";

interface DashboardShellProps {
  children: ReactNode;
}

function subscribeToMount() {
  return () => {};
}

export function DashboardShell({ children }: DashboardShellProps) {
  const router = useRouter();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const mounted = useSyncExternalStore(
    subscribeToMount,
    () => true,
    () => false,
  );

  const authenticated = mounted && hasAuthSession();

  useEffect(() => {
    if (mounted && !authenticated) {
      router.replace("/");
    }
  }, [authenticated, mounted, router]);

  if (!mounted || !authenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto size-10 animate-pulse rounded-xl bg-indigo-600" />

          <p className="mt-4 text-sm font-medium text-slate-500">Loading your workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 lg:block">
        <Sidebar />
      </aside>

      {mobileMenuOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close navigation overlay"
          />

          <aside className="relative h-full w-[min(18rem,85vw)] shadow-2xl">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-5 right-4 z-10 inline-flex size-9 items-center justify-center rounded-xl bg-white/10 text-white transition hover:bg-white/15"
              aria-label="Close navigation"
            >
              <CloseIcon className="size-5" />
            </button>

            <Sidebar onNavigate={() => setMobileMenuOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="lg:pl-72">
        <Topbar onOpenMenu={() => setMobileMenuOpen(true)} />

        <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
