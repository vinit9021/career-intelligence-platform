"use client";

import { useRouter } from "next/navigation";

import { MenuIcon, SearchIcon } from "@/components/dashboard/icons";
import { NotificationBell } from "@/components/notifications/notification-bell";
import { clearAuthSession, loadAuthSession } from "@/lib/auth-storage";

interface TopbarProps {
  onOpenMenu: () => void;
}

export function Topbar({ onOpenMenu }: TopbarProps) {
  const router = useRouter();

  const session = loadAuthSession();

  const fullName = session?.user.full_name ?? "Career Workspace";

  const initial = fullName.trim().charAt(0).toUpperCase() || "U";

  function logout() {
    clearAuthSession();

    router.replace("/");
  }

  return (
    <header className="sticky top-0 z-20 flex h-20 items-center border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6 lg:px-8">
      <button
        type="button"
        onClick={onOpenMenu}
        className="mr-3 inline-flex size-10 items-center justify-center rounded-xl border border-slate-200 text-slate-700 transition hover:bg-slate-50 lg:hidden"
        aria-label="Open navigation"
      >
        <MenuIcon className="size-5" />
      </button>

      <div className="hidden max-w-md flex-1 sm:block">
        <div className="relative">
          <SearchIcon className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />

          <input
            type="search"
            placeholder="Search applications, companies, roles..."
            disabled
            className="h-10 w-full cursor-not-allowed rounded-xl border border-slate-200 bg-slate-50 pr-4 pl-10 text-sm text-slate-500 outline-none"
          />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-3">
        <NotificationBell />

        <div className="hidden h-8 w-px bg-slate-200 sm:block" />

        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-slate-900 text-xs font-bold text-white">
            {initial}
          </div>

          <div className="hidden sm:block">
            <p className="max-w-40 truncate text-sm font-semibold text-slate-900">{fullName}</p>

            <p className="max-w-40 truncate text-xs text-slate-500">
              {session?.user.email ?? "Personal account"}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={logout}
          className="ml-1 rounded-lg px-3 py-2 text-xs font-semibold text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
        >
          Logout
        </button>
      </div>
    </header>
  );
}
