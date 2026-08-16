import { clearAuthSession, loadAuthSession } from "@/lib/auth-storage";
import { env } from "@/lib/env";

import type { ApplicationStatus, TimelineEventSource, TimelineEventType } from "@/lib/applications";

export interface AnalyticsSummary {
  total_applications: number;
  active_applications: number;
  online_assessments: number;
  interviews: number;
  offers: number;
  rejections: number;

  active_rate: number;
  interview_rate: number;
  offer_rate: number;
  rejection_rate: number;
}

export interface StatusBreakdownItem {
  status: ApplicationStatus;
  count: number;
  percentage: number;
}

export interface ApplicationTrendPoint {
  period: string;
  label: string;
  count: number;
}

export interface RecentActivityItem {
  event_id: string;
  application_id: string;

  company: string;
  role: string;

  event_type: TimelineEventType;
  title: string;
  source: TimelineEventSource;

  event_at: string;
}

export interface AnalyticsOverview {
  summary: AnalyticsSummary;

  status_breakdown: StatusBreakdownItem[];

  application_trend: ApplicationTrendPoint[];

  recent_activity: RecentActivityItem[];
}

function getErrorMessage(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (
      body as {
        detail?: unknown;
      }
    ).detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return fallback;
}

async function authenticatedRequest<T>(path: string): Promise<T> {
  const session = loadAuthSession();

  if (!session) {
    throw new Error("Your session has expired. Please sign in again.");
  }

  let response: Response;

  try {
    response = await fetch(`${env.apiBaseUrl}${path}`, {
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
      },
    });
  } catch {
    throw new Error("Unable to reach the backend API.");
  }

  if (response.status === 401) {
    clearAuthSession();

    if (typeof window !== "undefined") {
      window.location.assign("/");
    }

    throw new Error("Your session has expired. Please sign in again.");
  }

  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(body, `Request failed with status ${response.status}.`));
  }

  return body as T;
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  return authenticatedRequest<AnalyticsOverview>("/analytics/overview");
}
