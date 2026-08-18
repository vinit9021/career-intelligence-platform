"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { BellIcon } from "@/components/dashboard/icons";
import {
  deleteNotification,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  markNotificationUnread,
  type Notification,
  signalNotificationsChanged,
} from "@/lib/notifications";

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const [unreadOnly, setUnreadOnly] = useState(false);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;

    listNotifications(unreadOnly)
      .then((result) => {
        if (!active) {
          return;
        }

        setNotifications(result.items);

        setError("");
      })
      .catch((caught: unknown) => {
        if (!active) {
          return;
        }

        setError(caught instanceof Error ? caught.message : "Unable to load notifications.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [reloadKey, unreadOnly]);

  function refresh() {
    setLoading(true);

    setReloadKey((value) => value + 1);

    signalNotificationsChanged();
  }

  async function toggleRead(notification: Notification) {
    try {
      if (notification.is_read) {
        await markNotificationUnread(notification.id);
      } else {
        await markNotificationRead(notification.id);
      }

      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update notification.");
    }
  }

  async function markAllRead() {
    try {
      await markAllNotificationsRead();
      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update notifications.");
    }
  }

  async function remove(notification: Notification) {
    if (!window.confirm(`Delete "${notification.title}"?`)) {
      return;
    }

    try {
      await deleteNotification(notification.id);

      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete notification.");
    }
  }

  return (
    <div>
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-indigo-600">Career Intelligence</p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Notifications
          </h1>

          <p className="mt-2 text-sm text-slate-500 sm:text-base">
            Application updates, assessments, interviews and offers in one place.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void markAllRead()}
          className="h-11 rounded-xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Mark all as read
        </button>
      </div>

      <section className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex gap-2 border-b border-slate-100 p-4">
          <button
            type="button"
            onClick={() => {
              setUnreadOnly(false);
              setLoading(true);
            }}
            className={[
              "rounded-xl px-4 py-2 text-sm font-semibold",
              !unreadOnly ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100",
            ].join(" ")}
          >
            All
          </button>

          <button
            type="button"
            onClick={() => {
              setUnreadOnly(true);
              setLoading(true);
            }}
            className={[
              "rounded-xl px-4 py-2 text-sm font-semibold",
              unreadOnly ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100",
            ].join(" ")}
          >
            Unread
          </button>
        </div>

        {error ? (
          <div className="m-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        {loading ? (
          <div className="flex min-h-72 items-center justify-center">
            <p className="text-sm text-slate-500">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex min-h-72 flex-col items-center justify-center px-6 text-center">
            <div className="flex size-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <BellIcon className="size-6" />
            </div>

            <h2 className="mt-4 font-semibold text-slate-950">
              {unreadOnly ? "No unread notifications" : "No notifications yet"}
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              New application activity will appear here.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {notifications.map((notification) => (
              <article
                key={notification.id}
                className={[
                  "px-6 py-5",
                  notification.is_read ? "bg-white" : "bg-indigo-50/30",
                ].join(" ")}
              >
                <div className="flex flex-col gap-4 lg:flex-row lg:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-slate-950">{notification.title}</h3>

                      {!notification.is_read ? (
                        <span className="rounded-lg bg-indigo-100 px-2 py-1 text-[11px] font-semibold text-indigo-700">
                          New
                        </span>
                      ) : null}
                    </div>

                    <p className="mt-2 text-sm leading-6 text-slate-600">{notification.message}</p>

                    <p className="mt-2 text-xs text-slate-500">
                      {formatDateTime(notification.created_at)}
                    </p>

                    {notification.application_id ? (
                      <Link
                        href={`/applications/${notification.application_id}`}
                        className="mt-3 inline-flex text-xs font-semibold text-indigo-600"
                      >
                        View application
                      </Link>
                    ) : null}
                  </div>

                  <div className="flex shrink-0 gap-2">
                    <button
                      type="button"
                      onClick={() => void toggleRead(notification)}
                      className="rounded-lg px-3 py-2 text-xs font-semibold text-indigo-600 hover:bg-indigo-50"
                    >
                      {notification.is_read ? "Mark unread" : "Mark read"}
                    </button>

                    <button
                      type="button"
                      onClick={() => void remove(notification)}
                      className="rounded-lg px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
