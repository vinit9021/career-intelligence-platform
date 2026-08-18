import { clearAuthSession, loadAuthSession } from "@/lib/auth-storage";
import { env } from "@/lib/env";

export type NotificationType =
  "application_update" | "online_assessment" | "interview" | "offer" | "rejection" | "general";

export interface Notification {
  id: string;
  application_id: string | null;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  source: "system" | "gmail" | "integration";
  read_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationPage {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
}

interface UnreadCountResponse {
  unread_count: number;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
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
    throw new Error("Unable to reach the backend API.");
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
    if (typeof body === "object" && body !== null && "detail" in body) {
      const detail = (body as { detail?: unknown }).detail;

      if (typeof detail === "string") {
        throw new Error(detail);
      }
    }

    throw new Error(`Request failed with status ${response.status}.`);
  }

  return body as T;
}

export async function listNotifications(unreadOnly = false): Promise<NotificationPage> {
  return request<NotificationPage>(
    `/notifications?unread_only=${String(unreadOnly)}&page=1&page_size=20`,
  );
}

export async function getUnreadNotificationCount(): Promise<number> {
  const result = await request<UnreadCountResponse>("/notifications/unread-count");

  return result.unread_count;
}

export async function markNotificationRead(id: string): Promise<Notification> {
  return request<Notification>(`/notifications/${id}/read`, {
    method: "PATCH",
  });
}

export async function markNotificationUnread(id: string): Promise<Notification> {
  return request<Notification>(`/notifications/${id}/unread`, {
    method: "PATCH",
  });
}

export async function markAllNotificationsRead(): Promise<void> {
  await request<void>("/notifications/read-all", {
    method: "PATCH",
  });
}

export async function deleteNotification(id: string): Promise<void> {
  await request<void>(`/notifications/${id}`, {
    method: "DELETE",
  });
}

export function signalNotificationsChanged(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.dispatchEvent(new Event("career-notifications-changed"));
}
