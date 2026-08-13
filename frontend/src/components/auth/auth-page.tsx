"use client";

import type { FormEvent, ReactNode } from "react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ArrowLeftIcon,
  ArrowRightIcon,
  ResumeIcon,
  TargetIcon,
} from "@/components/dashboard/icons";
import { login, requestSignupOtp, verifySignupOtp } from "@/lib/auth";
import { hasAuthSession, saveAuthSession } from "@/lib/auth-storage";

type AuthMode = "login" | "signup";

type SignupStage = "details" | "otp";

interface FieldProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  placeholder: string;
  autoComplete?: string;
  onChange: (value: string) => void;
  children?: ReactNode;
}

function Field({
  id,
  label,
  type = "text",
  value,
  placeholder,
  autoComplete,
  onChange,
  children,
}: FieldProps) {
  return (
    <div>
      <label htmlFor={id} className="text-sm font-semibold text-slate-700">
        {label}
      </label>

      <div className="relative mt-2">
        <input
          id={id}
          type={type}
          value={value}
          placeholder={placeholder}
          autoComplete={autoComplete}
          onChange={(event) => onChange(event.target.value)}
          required
          className="h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm text-slate-900 transition outline-none placeholder:text-slate-400 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
        />

        {children}
      </div>
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  if (!message) {
    return null;
  }

  return (
    <div
      role="alert"
      className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-5 text-red-700"
    >
      {message}
    </div>
  );
}

export function AuthPage() {
  const router = useRouter();

  const [mode, setMode] = useState<AuthMode>("login");

  const [signupStage, setSignupStage] = useState<SignupStage>("details");

  const [email, setEmail] = useState("");

  const [password, setPassword] = useState("");

  const [fullName, setFullName] = useState("");

  const [confirmPassword, setConfirmPassword] = useState("");

  const [otp, setOtp] = useState("");

  const [error, setError] = useState("");

  const [success, setSuccess] = useState("");

  const [loading, setLoading] = useState(false);

  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (hasAuthSession()) {
      router.replace("/dashboard");
    }
  }, [router]);

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setSignupStage("details");
    setError("");
    setSuccess("");
    setOtp("");
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const auth = await login(email.trim(), password);

      saveAuthSession(auth);

      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRequestOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 12) {
      setError("Password must contain at least 12 characters.");
      return;
    }

    setLoading(true);

    try {
      const response = await requestSignupOtp(fullName.trim(), email.trim(), password);

      setEmail(response.email);

      setSignupStage("otp");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to request verification code.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!/^\d{6}$/.test(otp)) {
      setError("Enter the 6-digit verification code.");
      return;
    }

    setLoading(true);

    try {
      const result = await verifySignupOtp(email, otp);

      setMode("login");
      setSignupStage("details");

      setOtp("");
      setPassword("");
      setConfirmPassword("");

      setError("");
      setSuccess(result.message || "Account created successfully. Please sign in.");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "OTP verification failed.");
    } finally {
      setLoading(false);
    }
  }

  async function resendOtp() {
    setError("");
    setLoading(true);

    try {
      await requestSignupOtp(fullName.trim(), email.trim(), password);

      setOtp("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to resend verification code.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-[1.05fr_0.95fr]">
      <section className="relative hidden min-h-screen overflow-hidden bg-slate-950 p-12 text-white lg:flex lg:flex-col">
        <div className="absolute -top-40 -left-32 size-[32rem] rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="absolute right-[-10rem] bottom-[-10rem] size-[32rem] rounded-full bg-violet-500/15 blur-3xl" />

        <div className="relative flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-xl bg-indigo-500 text-sm font-bold shadow-lg shadow-indigo-950/30">
            CI
          </div>

          <div>
            <p className="font-semibold">Career Intelligence</p>
            <p className="text-xs text-slate-400">AI Career OS</p>
          </div>
        </div>

        <div className="relative my-auto max-w-xl">
          <p className="text-sm font-semibold tracking-[0.18em] text-indigo-300 uppercase">
            Your career command center
          </p>

          <h1 className="mt-5 text-5xl font-bold tracking-tight">
            Turn every opportunity into an intelligent career decision.
          </h1>

          <p className="mt-6 max-w-lg text-base leading-8 text-slate-400">
            Manage resumes, applications, ATS optimization, skill gaps and AI-powered career
            workflows from one workspace.
          </p>

          <div className="mt-10 grid gap-4">
            <div className="flex items-start gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-300">
                <ResumeIcon className="size-5" />
              </div>

              <div>
                <p className="text-sm font-semibold">Resume Intelligence</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">
                  Parse, match and optimize resumes for every role.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-300">
                <TargetIcon className="size-5" />
              </div>

              <div>
                <p className="text-sm font-semibold">Application Intelligence</p>
                <p className="mt-1 text-sm leading-6 text-slate-400">
                  Track opportunities and make better job-search decisions.
                </p>
              </div>
            </div>
          </div>
        </div>

        <p className="relative text-xs text-slate-500">Career Intelligence Platform</p>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8 lg:px-12">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-600 text-xs font-bold text-white">
              CI
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-900">Career Intelligence</p>
              <p className="text-xs text-slate-500">AI Career OS</p>
            </div>
          </div>

          <p className="text-sm font-semibold text-indigo-600">Welcome</p>

          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            {mode === "login"
              ? "Sign in to your workspace"
              : signupStage === "details"
                ? "Create your account"
                : "Verify your email"}
          </h2>

          <p className="mt-3 text-sm leading-6 text-slate-500">
            {mode === "login"
              ? "Continue managing your career intelligence workspace."
              : signupStage === "details"
                ? "Create your Career Intelligence account securely."
                : `Enter the verification code for ${email}.`}
          </p>

          {signupStage === "details" ? (
            <div className="mt-8 grid grid-cols-2 rounded-xl bg-slate-100 p-1">
              <button
                type="button"
                onClick={() => changeMode("login")}
                className={[
                  "rounded-lg px-4 py-2.5 text-sm font-semibold transition",
                  mode === "login"
                    ? "bg-white text-slate-950 shadow-sm"
                    : "text-slate-500 hover:text-slate-800",
                ].join(" ")}
              >
                Sign in
              </button>

              <button
                type="button"
                onClick={() => changeMode("signup")}
                className={[
                  "rounded-lg px-4 py-2.5 text-sm font-semibold transition",
                  mode === "signup"
                    ? "bg-white text-slate-950 shadow-sm"
                    : "text-slate-500 hover:text-slate-800",
                ].join(" ")}
              >
                Sign up
              </button>
            </div>
          ) : null}

          {success ? (
            <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm leading-5 text-emerald-700">
              {success}
            </div>
          ) : null}

          <div className="mt-7">
            {mode === "login" ? (
              <form onSubmit={handleLogin} className="space-y-5">
                <Field
                  id="login-email"
                  label="Email address"
                  type="email"
                  value={email}
                  placeholder="you@example.com"
                  autoComplete="email"
                  onChange={setEmail}
                />

                <Field
                  id="login-password"
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  onChange={setPassword}
                >
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute top-1/2 right-3 -translate-y-1/2 text-xs font-semibold text-slate-500 hover:text-indigo-600"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </Field>

                <ErrorMessage message={error} />

                <button
                  type="submit"
                  disabled={loading}
                  className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Signing in..." : "Sign in"}

                  {!loading ? <ArrowRightIcon className="size-4" /> : null}
                </button>

                <p className="text-center text-sm text-slate-500">
                  New here?{" "}
                  <button
                    type="button"
                    onClick={() => changeMode("signup")}
                    className="font-semibold text-indigo-600 hover:text-indigo-700"
                  >
                    Create account
                  </button>
                </p>
              </form>
            ) : signupStage === "details" ? (
              <form onSubmit={handleRequestOtp} className="space-y-5">
                <Field
                  id="signup-name"
                  label="Full name"
                  value={fullName}
                  placeholder="Your full name"
                  autoComplete="name"
                  onChange={setFullName}
                />

                <Field
                  id="signup-email"
                  label="Email address"
                  type="email"
                  value={email}
                  placeholder="you@example.com"
                  autoComplete="email"
                  onChange={setEmail}
                />

                <Field
                  id="signup-password"
                  label="Password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  placeholder="Create a strong password"
                  autoComplete="new-password"
                  onChange={setPassword}
                >
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute top-1/2 right-3 -translate-y-1/2 text-xs font-semibold text-slate-500 hover:text-indigo-600"
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </Field>

                <p className="-mt-2 text-xs leading-5 text-slate-500">
                  Minimum 12 characters with uppercase, lowercase, number and special character.
                </p>

                <Field
                  id="confirm-password"
                  label="Confirm password"
                  type="password"
                  value={confirmPassword}
                  placeholder="Repeat your password"
                  autoComplete="new-password"
                  onChange={setConfirmPassword}
                />

                <ErrorMessage message={error} />

                <button
                  type="submit"
                  disabled={loading}
                  className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Sending code..." : "Continue with OTP"}

                  {!loading ? <ArrowRightIcon className="size-4" /> : null}
                </button>

                <p className="text-center text-sm text-slate-500">
                  Already have an account?{" "}
                  <button
                    type="button"
                    onClick={() => changeMode("login")}
                    className="font-semibold text-indigo-600 hover:text-indigo-700"
                  >
                    Sign in
                  </button>
                </p>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp} className="space-y-5">
                <button
                  type="button"
                  onClick={() => {
                    setSignupStage("details");
                    setError("");
                  }}
                  className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-indigo-600"
                >
                  <ArrowLeftIcon className="size-4" />
                  Change account details
                </button>

                <div>
                  <label htmlFor="signup-otp" className="text-sm font-semibold text-slate-700">
                    6-digit verification code
                  </label>

                  <input
                    id="signup-otp"
                    value={otp}
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    maxLength={6}
                    onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                    placeholder="000000"
                    required
                    className="mt-2 h-14 w-full rounded-xl border border-slate-200 bg-white px-4 text-center font-mono text-xl font-bold tracking-[0.45em] text-slate-950 transition outline-none placeholder:text-slate-300 focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
                  />
                </div>

                <ErrorMessage message={error} />

                <button
                  type="submit"
                  disabled={loading}
                  className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? "Verifying..." : "Verify & create account"}

                  {!loading ? <ArrowRightIcon className="size-4" /> : null}
                </button>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-500">Didn&apos;t get the code?</span>

                  <button
                    type="button"
                    disabled={loading}
                    onClick={resendOtp}
                    className="font-semibold text-indigo-600 hover:text-indigo-700 disabled:opacity-50"
                  >
                    Resend OTP
                  </button>
                </div>
              </form>
            )}
          </div>

          <p className="mt-8 text-center text-xs leading-5 text-slate-400">
            By continuing, you agree to use Career Intelligence responsibly and keep your account
            credentials secure.
          </p>
        </div>
      </section>
    </main>
  );
}
