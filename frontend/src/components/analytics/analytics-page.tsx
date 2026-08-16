"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import {
  ApplicationsIcon,
  BriefcaseIcon,
  CalendarIcon,
  TargetIcon,
} from "@/components/dashboard/icons";
import {
  getAnalyticsOverview,
  type AnalyticsOverview,
  type RecentActivityItem,
  type StatusBreakdownItem,
} from "@/lib/analytics";
import type { ApplicationStatus } from "@/lib/applications";

const statusLabels: Record<ApplicationStatus, string> = {
  applied: "Applied",

  online_assessment: "Online Assessment",

  interview: "Interview",

  offer: "Offer",

  rejected: "Rejected",

  withdrawn: "Withdrawn",
};

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function sourceLabel(source: RecentActivityItem["source"]): string {
  if (source === "gmail") {
    return "Gmail";
  }

  if (source === "integration") {
    return "Integration";
  }

  if (source === "system") {
    return "System";
  }

  return "Manual";
}

interface MetricCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: React.ComponentType<{
    className?: string;
  }>;
}

function MetricCard({ title, value, subtitle, icon: Icon }: MetricCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium text-slate-500">{title}</p>

          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-950">{value}</p>

          <p className="mt-2 text-xs text-slate-500">{subtitle}</p>
        </div>

        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
          <Icon className="size-5" />
        </div>
      </div>
    </div>
  );
}

function StatusRow({ item }: { item: StatusBreakdownItem }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-4">
        <p className="text-sm font-medium text-slate-700">{statusLabels[item.status]}</p>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">{item.percentage}%</span>

          <span className="min-w-6 text-right text-sm font-semibold text-slate-950">
            {item.count}
          </span>
        </div>
      </div>

      <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-indigo-500"
          style={{
            width: `${item.percentage}%`,
          }}
        />
      </div>
    </div>
  );
}

export function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    getAnalyticsOverview()
      .then((result) => {
        if (!active) {
          return;
        }

        setAnalytics(result);

        setError("");
      })
      .catch((caught: unknown) => {
        if (!active) {
          return;
        }

        setError(caught instanceof Error ? caught.message : "Unable to load analytics.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto size-10 animate-pulse rounded-xl bg-indigo-500" />

          <p className="mt-4 text-sm font-medium text-slate-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="rounded-2xl border border-red-200 bg-white p-8 shadow-sm">
        <h1 className="text-xl font-bold text-slate-950">Analytics unavailable</h1>

        <p className="mt-2 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  const {
    summary,
    status_breakdown: statusBreakdown,
    application_trend: applicationTrend,
    recent_activity: recentActivity,
  } = analytics;

  const trendMax = Math.max(1, ...applicationTrend.map((item) => item.count));

  return (
    <div>
      <div>
        <p className="text-sm font-semibold text-indigo-600">Career Intelligence</p>

        <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
          Analytics
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">
          Understand your application pipeline and career progress using real application data.
        </p>
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          title="Total applications"
          value={summary.total_applications}
          subtitle="All tracked opportunities"
          icon={ApplicationsIcon}
        />

        <MetricCard
          title="Active applications"
          value={summary.active_applications}
          subtitle={`${summary.active_rate}% of applications`}
          icon={BriefcaseIcon}
        />

        <MetricCard
          title="Online assessments"
          value={summary.online_assessments}
          subtitle="Current OA stage"
          icon={CalendarIcon}
        />

        <MetricCard
          title="Interviews"
          value={summary.interviews}
          subtitle={`${summary.interview_rate}% interview rate`}
          icon={TargetIcon}
        />

        <MetricCard
          title="Offers"
          value={summary.offers}
          subtitle={`${summary.offer_rate}% offer rate`}
          icon={TargetIcon}
        />

        <MetricCard
          title="Rejections"
          value={summary.rejections}
          subtitle={`${summary.rejection_rate}% rejection rate`}
          icon={ApplicationsIcon}
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-5">
            <h2 className="text-base font-semibold text-slate-950">Application status</h2>

            <p className="mt-1 text-sm text-slate-500">
              Current distribution of your application pipeline.
            </p>
          </div>

          <div className="space-y-5 p-6">
            {statusBreakdown.map((item) => (
              <StatusRow key={item.status} item={item} />
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-6 py-5">
            <h2 className="text-base font-semibold text-slate-950">Applications over time</h2>

            <p className="mt-1 text-sm text-slate-500">
              Applications submitted during the last six months.
            </p>
          </div>

          <div className="space-y-5 p-6">
            {applicationTrend.map((item) => {
              const percentage = (item.count / trendMax) * 100;

              return (
                <div key={item.period}>
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-700">{item.label}</p>

                    <p className="text-sm font-semibold text-slate-950">{item.count}</p>
                  </div>

                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full bg-indigo-500"
                      style={{
                        width: `${percentage}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      <section className="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-5">
          <h2 className="text-base font-semibold text-slate-950">Recent activity</h2>

          <p className="mt-1 text-sm text-slate-500">
            Latest events from your application timelines.
          </p>
        </div>

        {recentActivity.length === 0 ? (
          <div className="flex min-h-52 flex-col items-center justify-center px-6 text-center">
            <div className="flex size-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
              <CalendarIcon className="size-5" />
            </div>

            <p className="mt-4 text-sm font-semibold text-slate-950">No activity yet</p>

            <p className="mt-1 text-sm text-slate-500">
              Application timeline events will appear here.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {recentActivity.map((activity) => (
              <Link
                key={activity.event_id}
                href={`/applications/${activity.application_id}`}
                className="flex flex-col gap-3 px-6 py-5 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-semibold text-slate-950">{activity.title}</p>

                    <span className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">
                      {sourceLabel(activity.source)}
                    </span>
                  </div>

                  <p className="mt-1 text-sm text-slate-500">
                    {activity.company}
                    {" | "}
                    {activity.role}
                  </p>
                </div>

                <p className="shrink-0 text-xs font-medium text-slate-500">
                  {formatDateTime(activity.event_at)}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
