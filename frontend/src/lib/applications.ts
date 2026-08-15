import { clearAuthSession, loadAuthSession } from "@/lib/auth-storage";
import { env } from "@/lib/env";

export type ApplicationStatus =
  "applied" | "online_assessment" | "interview" | "offer" | "rejected" | "withdrawn";

export type ApplicationSource = "manual" | "gmail" | "integration";

export type ApplicationSortField = "applied_at" | "created_at" | "company" | "role" | "status";

export interface Application {
  id: string;
  company: string;
  role: string;
  job_url: string | null;
  location: string | null;
  applied_at: string;
  status: ApplicationStatus;
  source: ApplicationSource;
  external_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ApplicationCreateInput {
  company: string;
  role: string;
  job_url?: string | null;
  location?: string | null;
  applied_at: string;
  status: ApplicationStatus;
  notes?: string | null;
}

export interface ApplicationPage {
  items: Application[];
  total: number;
  page: number;
  page_size: number;
}

interface ListApplicationOptions {
  search?: string;
  status?: ApplicationStatus | "";
  sortBy?: ApplicationSortField;
  sortOrder?: "asc" | "desc";
  page?: number;
  pageSize?: number;
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

async function authenticatedRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const session = loadAuthSession();

  if (!session) {
    throw new Error("Your session has expired. Please sign in again.");
  }

  let response: Response;

  try {
    response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.accessToken}`,
        ...init.headers,
      },
    });
  } catch {
    throw new Error("Unable to reach the backend API. Make sure FastAPI is running on port 8000.");
  }

  if (response.status === 401) {
    clearAuthSession();

    if (typeof window !== "undefined") {
      window.location.assign("/");
    }

    throw new Error("Your session has expired. Please sign in again.");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(getErrorMessage(body, `Request failed with status ${response.status}.`));
  }

  return body as T;
}

export async function listApplications(
  options: ListApplicationOptions = {},
): Promise<ApplicationPage> {
  const params = new URLSearchParams();

  if (options.search?.trim()) {
    params.set("search", options.search.trim());
  }

  if (options.status) {
    params.set("status", options.status);
  }

  params.set("sort_by", options.sortBy ?? "applied_at");

  params.set("sort_order", options.sortOrder ?? "desc");

  params.set("page", String(options.page ?? 1));

  params.set("page_size", String(options.pageSize ?? 20));

  return authenticatedRequest<ApplicationPage>(`/applications?${params.toString()}`);
}

export async function createApplication(payload: ApplicationCreateInput): Promise<Application> {
  return authenticatedRequest<Application>("/applications", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getApplication(applicationId: string): Promise<Application> {
  return authenticatedRequest<Application>(`/applications/${applicationId}`);
}

export async function updateApplication(
  applicationId: string,
  payload: Partial<ApplicationCreateInput>,
): Promise<Application> {
  return authenticatedRequest<Application>(`/applications/${applicationId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteApplication(applicationId: string): Promise<void> {
  await authenticatedRequest<void>(`/applications/${applicationId}`, {
    method: "DELETE",
  });
}

export type TimelineEventType =
  | "application_submitted"
  | "status_changed"
  | "online_assessment_received"
  | "online_assessment_completed"
  | "interview_scheduled"
  | "interview_completed"
  | "offer_received"
  | "rejected"
  | "withdrawn"
  | "note";

export type TimelineEventSource = "manual" | "system" | "gmail" | "integration";

export interface ApplicationTimelineEvent {
  id: string;
  application_id: string;
  event_type: TimelineEventType;
  title: string;
  description: string | null;
  related_status: ApplicationStatus | null;
  source: TimelineEventSource;
  external_id: string | null;
  event_at: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineEventCreateInput {
  event_type: TimelineEventType;
  title: string;
  description?: string | null;
  related_status?: ApplicationStatus | null;
  event_at: string;
}

export interface TimelineEventUpdateInput {
  event_type?: TimelineEventType;
  title?: string;
  description?: string | null;
  related_status?: ApplicationStatus | null;
  event_at?: string;
}

export async function listApplicationTimeline(
  applicationId: string,
): Promise<ApplicationTimelineEvent[]> {
  return authenticatedRequest<ApplicationTimelineEvent[]>(
    `/applications/${applicationId}/timeline?order=asc`,
  );
}

export async function createApplicationTimelineEvent(
  applicationId: string,
  payload: TimelineEventCreateInput,
): Promise<ApplicationTimelineEvent> {
  return authenticatedRequest<ApplicationTimelineEvent>(`/applications/${applicationId}/timeline`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateApplicationTimelineEvent(
  applicationId: string,
  eventId: string,
  payload: TimelineEventUpdateInput,
): Promise<ApplicationTimelineEvent> {
  return authenticatedRequest<ApplicationTimelineEvent>(
    `/applications/${applicationId}/timeline/${eventId}`,
    {
      method: "PATCH",
      body: JSON.stringify(payload),
    },
  );
}

export async function deleteApplicationTimelineEvent(
  applicationId: string,
  eventId: string,
): Promise<void> {
  await authenticatedRequest<void>(`/applications/${applicationId}/timeline/${eventId}`, {
    method: "DELETE",
  });
}
