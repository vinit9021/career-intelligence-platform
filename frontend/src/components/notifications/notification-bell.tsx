"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BellIcon } from "@/components/dashboard/icons";
import { getUnreadNotificationCount } from "@/lib/notifications";

export function NotificationBell() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let active = true;

    function refresh() {
      void getUnreadNotificationCount()
        .then((value) => {
          if (active) {
            setCount(value);
          }
        })
        .catch(() => {
          // Authentication layer handles
          // expired sessions.
        });
    }

    refresh();

    const timer = window.setInterval(refresh, 30000);

    window.addEventListener("career-notifications-changed", refresh);

    return () => {
      active = false;

      window.clearInterval(timer);

      window.removeEventListener("career-notifications-changed", refresh);
    };
  }, []);

  return (
    <Link
      href="/notifications"
      aria-label="Notifications"
      className="relative inline-flex size-10 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
    >
      <BellIcon className="size-5" />

      {count > 0 ? (
        <span className="absolute -top-1 -right-1 flex min-w-5 items-center justify-center rounded-full bg-indigo-600 px-1.5 py-0.5 text-[10px] font-bold text-white ring-2 ring-white">
          {count > 99 ? "99+" : count}
        </span>
      ) : null}
    </Link>
  );
}
