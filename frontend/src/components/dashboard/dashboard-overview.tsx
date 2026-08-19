"use client";

import Link from "next/link";
import type { ComponentType, SVGProps } from "react";
import { useEffect, useState } from "react";

import {
  AnalyticsIcon,
  ApplicationsIcon,
  ArrowRightIcon,
  BellIcon,
  BriefcaseIcon,
  TargetIcon,
} from "@/components/dashboard/icons";
import { SectionCard } from "@/components/dashboard/section-card";
import {
  getAnalyticsOverview,
  type AnalyticsOverview,
  type RecentActivityItem,
  type StatusBreakdownItem,
} from "@/lib/analytics";
import { listApplications, type Application, type ApplicationStatus } from "@/lib/applications";
import { getUnreadNotificationCount } from "@/lib/notifications";

interface DashboardData {
  analytics: AnalyticsOverview;
  applications: Application[];
  unreadCount: number;
}

interface MetricCardProps {
  title: string;
  value: number;
  detail: string;
  href: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const statusLabels: Record<ApplicationStatus, string> = {
  applied: "Applied",
  online_assessment: "Online Assessment",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

const statusBadgeClasses: Record<ApplicationStatus, string> = {
  applied: "bg-blue-50 text-blue-700 ring-blue-100",

  online_assessment: "bg-violet-50 text-violet-700 ring-violet-100",

  interview: "bg-amber-50 text-amber-700 ring-amber-100",

  offer: "bg-emerald-50 text-emerald-700 ring-emerald-100",

  rejected: "bg-red-50 text-red-700 ring-red-100",

  withdrawn: "bg-slate-100 text-slate-600 ring-slate-200",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function MetricCard({ title, value, detail, href, icon: Icon }: MetricCardProps) {
  return (
    <Link
      href={href}
      className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>

          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">{value}</p>
        </div>

        <div className="flex size-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition group-hover:bg-indigo-100">
          <Icon className="size-5" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="text-xs leading-5 text-slate-500">{detail}</p>

        <ArrowRightIcon className="size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-600" />
      </div>
    </Link>
  );
}

function PipelineRow({ item }: { item: StatusBreakdownItem }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-700">{statusLabels[item.status]}</span>

          <span className="text-xs text-slate-400">{item.percentage}%</span>
        </div>

        <span className="text-sm font-semibold text-slate-950">{item.count}</span>
      </div>

      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all"
          style={{
            width: `${item.percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

function RecentApplicationRow({ application }: { application: Application }) {
  return (
    <Link
      href={`/applications/${application.id}`}
      className="group flex flex-col gap-3 rounded-xl border border-slate-100 px-4 py-4 transition hover:border-indigo-100 hover:bg-indigo-50/30 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <p className="truncate text-sm font-semibold text-slate-950">{application.company}</p>

          <span
            className={[
              "rounded-lg px-2 py-1 text-[11px] font-semibold ring-1",
              statusBadgeClasses[application.status],
            ].join(" ")}
          >
            {statusLabels[application.status]}
          </span>
        </div>

        <p className="mt-1 truncate text-sm text-slate-500">{application.role}</p>

        <p className="mt-2 text-xs text-slate-400">Applied {formatDate(application.applied_at)}</p>
      </div>

      <ArrowRightIcon className="size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-600" />
    </Link>
  );
}

function RecentActivityRow({ activity }: { activity: RecentActivityItem }) {
  return (
    <Link
      href={`/applications/${activity.application_id}`}
      className="group flex gap-4 rounded-xl px-2 py-3 transition hover:bg-slate-50"
    >
      <div className="mt-1 flex size-8 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
        <div className="size-2.5 rounded-full bg-indigo-500" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-slate-900">{activity.title}</p>

        <p className="mt-1 truncate text-xs text-slate-500">
          {activity.company}
          {" | "}
          {activity.role}
        </p>

        <p className="mt-1 text-xs text-slate-400">{formatDateTime(activity.event_at)}</p>
      </div>

      <ArrowRightIcon className="mt-2 size-4 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-indigo-600" />
    </Link>
  );
}

export function DashboardOverview() {
  const [data, setData] = useState<DashboardData | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      try {
        const [analytics, applicationPage, unreadCount] = await Promise.all([
          getAnalyticsOverview(),

          listApplications({
            sortBy: "applied_at",

            sortOrder: "desc",

            page: 1,

            pageSize: 5,
          }),

          getUnreadNotificationCount(),
        ]);

        if (!active) {
          return;
        }

        setData({
          analytics,
          applications: applicationPage.items,
          unreadCount,
        });

        setError("");
      } catch (caught) {
        if (!active) {
          return;
        }

        setError(caught instanceof Error ? caught.message : "Unable to load dashboard data.");
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    function refreshNotificationCount() {
      void getUnreadNotificationCount()
        .then((unreadCount) => {
          if (!active) {
            return;
          }

          setData((current) => {
            if (!current) {
              return current;
            }

            return {
              ...current,
              unreadCount,
            };
          });
        })
        .catch(() => {
          // Existing authentication
          // handling manages failures.
        });
    }

    void loadDashboard();

    window.addEventListener("career-notifications-changed", refreshNotificationCount);

    return () => {
      active = false;

      window.removeEventListener("career-notifications-changed", refreshNotificationCount);
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto size-10 animate-pulse rounded-xl bg-indigo-600" />

          <p className="mt-4 text-sm font-medium text-slate-500">
            Loading your career dashboard...
          </p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-2xl border border-red-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold text-red-600">Dashboard unavailable</p>

        <h1 className="mt-2 text-2xl font-bold text-slate-950">
          We could not load your career data.
        </h1>

        <p className="mt-2 text-sm text-slate-500">{error}</p>
      </div>
    );
  }

  const { analytics, applications, unreadCount } = data;

  const { summary, status_breakdown: statusBreakdown, recent_activity: recentActivity } = analytics;

  return (
    <div>
      <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-indigo-600">Career Intelligence</p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Dashboard
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">
            Your application pipeline, recent activity and career progress in one workspace.
          </p>
        </div>

        <Link
          href="/applications"
          className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
        >
          View applications
          <ArrowRightIcon className="size-4" />
        </Link>
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard
          title="Applications"
          value={summary.total_applications}
          detail="All tracked opportunities"
          href="/applications"
          icon={ApplicationsIcon}
        />

        <MetricCard
          title="Active"
          value={summary.active_applications}
          detail={`${summary.active_rate}% currently active`}
          href="/analytics"
          icon={BriefcaseIcon}
        />

        <MetricCard
          title="Interviews"
          value={summary.interviews}
          detail={`${summary.interview_rate}% interview rate`}
          href="/analytics"
          icon={TargetIcon}
        />

        <MetricCard
          title="Offers"
          value={summary.offers}
          detail={`${summary.offer_rate}% offer rate`}
          href="/analytics"
          icon={AnalyticsIcon}
        />

        <MetricCard
          title="Unread"
          value={unreadCount}
          detail="Notifications needing attention"
          href="/notifications"
          icon={BellIcon}
        />
      </section>

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.75fr)]">
        <SectionCard
          title="Recent Applications"
          description="Your latest tracked opportunities."
          action={
            <Link
              href="/applications"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              View all
              <ArrowRightIcon className="size-3.5" />
            </Link>
          }
        >
          {applications.length === 0 ? (
            <div className="flex min-h-52 flex-col items-center justify-center text-center">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <ApplicationsIcon className="size-5" />
              </div>

              <p className="mt-4 text-sm font-semibold text-slate-950">No applications yet</p>

              <p className="mt-1 max-w-sm text-sm leading-6 text-slate-500">
                Your latest applications will appear here after you add or import them.
              </p>

              <Link href="/applications" className="mt-4 text-sm font-semibold text-indigo-600">
                Go to Applications
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {applications.map((application) => (
                <RecentApplicationRow key={application.id} application={application} />
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Career Snapshot"
          description="Quick conversion and pipeline indicators."
          action={
            <Link
              href="/analytics"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              Analytics
              <ArrowRightIcon className="size-3.5" />
            </Link>
          }
        >
          <div className="grid gap-4">
            <div className="rounded-xl bg-slate-50 p-4">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-medium text-slate-500">Interview rate</p>

                  <p className="mt-2 text-2xl font-bold text-slate-950">
                    {summary.interview_rate}%
                  </p>
                </div>

                <TargetIcon className="size-5 text-indigo-500" />
              </div>
            </div>

            <div className="rounded-xl bg-slate-50 p-4">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-medium text-slate-500">Offer rate</p>

                  <p className="mt-2 text-2xl font-bold text-slate-950">{summary.offer_rate}%</p>
                </div>

                <AnalyticsIcon className="size-5 text-indigo-500" />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-100 p-4">
                <p className="text-xs text-slate-500">Assessments</p>

                <p className="mt-1 text-xl font-bold text-slate-950">
                  {summary.online_assessments}
                </p>
              </div>

              <div className="rounded-xl border border-slate-100 p-4">
                <p className="text-xs text-slate-500">Rejections</p>

                <p className="mt-1 text-xl font-bold text-slate-950">{summary.rejections}</p>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <SectionCard
          title="Application Pipeline"
          description="Current distribution across application stages."
          action={
            <Link
              href="/analytics"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              Full analytics
              <ArrowRightIcon className="size-3.5" />
            </Link>
          }
        >
          {summary.total_applications === 0 ? (
            <div className="flex min-h-48 items-center justify-center text-center">
              <p className="max-w-sm text-sm leading-6 text-slate-500">
                Pipeline information will appear after applications are added.
              </p>
            </div>
          ) : (
            <div className="space-y-5">
              {statusBreakdown.map((item) => (
                <PipelineRow key={item.status} item={item} />
              ))}
            </div>
          )}
        </SectionCard>

        <SectionCard
          title="Recent Activity"
          description="Latest updates from your application timelines."
          action={
            <Link
              href="/notifications"
              className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-700"
            >
              Notifications
              <ArrowRightIcon className="size-3.5" />
            </Link>
          }
        >
          {recentActivity.length === 0 ? (
            <div className="flex min-h-48 flex-col items-center justify-center text-center">
              <div className="flex size-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <BriefcaseIcon className="size-5" />
              </div>

              <p className="mt-4 text-sm font-semibold text-slate-950">No recent activity</p>

              <p className="mt-1 max-w-sm text-sm leading-6 text-slate-500">
                Application and timeline activity will appear here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {recentActivity.slice(0, 6).map((activity) => (
                <RecentActivityRow key={activity.event_id} activity={activity} />
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
