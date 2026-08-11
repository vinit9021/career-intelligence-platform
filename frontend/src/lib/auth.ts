import { env } from "@/lib/env";

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
}

export interface SignupCompleteResponse {
  email: string;
  message: string;
}

export interface SignupOtpResponse {
  email: string;
  expires_in: number;
  resend_in: number;
}

interface ErrorDetail {
  msg?: string;
}

function errorMessage(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (
      body as {
        detail?: string | ErrorDetail[];
      }
    ).detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail) && detail.length > 0) {
      return detail[0]?.msg ?? fallback;
    }
  }

  return fallback;
}

async function apiRequest<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...init.headers,
      },
    });
  } catch {
    throw new Error("Unable to reach the backend API. Make sure FastAPI is running on port 8000.");
  }

  const body = (await response.json().catch(() => null)) as unknown;

  if (!response.ok) {
    throw new Error(errorMessage(body, `Request failed with status ${response.status}.`));
  }

  return body as T;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });
}

export async function requestSignupOtp(
  fullName: string,
  email: string,
  password: string,
): Promise<SignupOtpResponse> {
  return apiRequest<SignupOtpResponse>("/auth/signup/request-otp", {
    method: "POST",
    body: JSON.stringify({
      full_name: fullName,
      email,
      password,
    }),
  });
}

export async function verifySignupOtp(email: string, otp: string): Promise<SignupCompleteResponse> {
  return apiRequest<SignupCompleteResponse>("/auth/signup/verify-otp", {
    method: "POST",
    body: JSON.stringify({
      email,
      otp,
    }),
  });
}
