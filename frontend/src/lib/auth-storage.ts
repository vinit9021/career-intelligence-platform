import type { AuthResponse, AuthUser } from "@/lib/auth";

const STORAGE_KEY = "career-intelligence-auth";

const EXPIRY_SAFETY_MARGIN_MS = 5_000;

export interface StoredAuthSession {
  accessToken: string;
  refreshToken: string;
  accessExpiresAt: number;
  user: AuthUser;
}

function isStoredAuthSession(value: unknown): value is StoredAuthSession {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const session = value as Partial<StoredAuthSession>;

  return (
    typeof session.accessToken === "string" &&
    session.accessToken.length > 0 &&
    typeof session.refreshToken === "string" &&
    session.refreshToken.length > 0 &&
    typeof session.accessExpiresAt === "number" &&
    Number.isFinite(session.accessExpiresAt) &&
    typeof session.user === "object" &&
    session.user !== null
  );
}

function isSessionExpired(session: StoredAuthSession): boolean {
  return Date.now() + EXPIRY_SAFETY_MARGIN_MS >= session.accessExpiresAt;
}

export function saveAuthSession(auth: AuthResponse): void {
  if (typeof window === "undefined") {
    return;
  }

  const session: StoredAuthSession = {
    accessToken: auth.access_token,
    refreshToken: auth.refresh_token,
    accessExpiresAt: Date.now() + auth.expires_in * 1000,
    user: auth.user,
  };

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function loadAuthSession(): StoredAuthSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);

  if (!raw) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(raw);

    if (!isStoredAuthSession(parsed)) {
      clearAuthSession();

      return null;
    }

    if (isSessionExpired(parsed)) {
      clearAuthSession();

      return null;
    }

    return parsed;
  } catch {
    clearAuthSession();

    return null;
  }
}

export function hasAuthSession(): boolean {
  return loadAuthSession() !== null;
}

export function clearAuthSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);
}
