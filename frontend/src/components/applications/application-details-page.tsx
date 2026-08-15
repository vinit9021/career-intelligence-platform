"use client";

import Link from "next/link";
import { ApplicationTimeline } from "@/components/applications/application-timeline";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  ApplicationsIcon,
  ArrowLeftIcon,
  BriefcaseIcon,
  CalendarIcon,
  TargetIcon,
} from "@/components/dashboard/icons";
import {
  deleteApplication,
  getApplication,
  type Application,
  type ApplicationStatus,
  updateApplication,
} from "@/lib/applications";

interface ApplicationDetailsPageProps {
  applicationId: string;
}

interface ApplicationDraft {
  company: string;
  role: string;
  location: string;
  jobUrl: string;
  appliedAt: string;
  status: ApplicationStatus;
  notes: string;
}

const statusLabels: Record<ApplicationStatus, string> = {
  applied: "Applied",
  online_assessment: "Online Assessment",
  interview: "Interview",
  offer: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

const statusOptions: ApplicationStatus[] = [
  "applied",
  "online_assessment",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];

const statusClasses: Record<ApplicationStatus, string> = {
  applied: "bg-blue-50 text-blue-700 ring-blue-200",

  online_assessment: "bg-violet-50 text-violet-700 ring-violet-200",

  interview: "bg-amber-50 text-amber-700 ring-amber-200",

  offer: "bg-emerald-50 text-emerald-700 ring-emerald-200",

  rejected: "bg-red-50 text-red-700 ring-red-200",

  withdrawn: "bg-slate-100 text-slate-600 ring-slate-200",
};

function createDraft(application: Application): ApplicationDraft {
  return {
    company: application.company,

    role: application.role,

    location: application.location ?? "",

    jobUrl: application.job_url ?? "",

    appliedAt: application.applied_at,

    status: application.status,

    notes: application.notes ?? "",
  };
}

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
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function sourceLabel(source: Application["source"]): string {
  if (source === "gmail") {
    return "Gmail";
  }

  if (source === "integration") {
    return "Integration";
  }

  return "Manual";
}

export function ApplicationDetailsPage({ applicationId }: ApplicationDetailsPageProps) {
  const router = useRouter();

  const [application, setApplication] = useState<Application | null>(null);

  const [draft, setDraft] = useState<ApplicationDraft | null>(null);

  const [loading, setLoading] = useState(true);

  const [editing, setEditing] = useState(false);

  const [saving, setSaving] = useState(false);

  const [deleting, setDeleting] = useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    getApplication(applicationId)
      .then((result) => {
        if (!active) {
          return;
        }

        setApplication(result);

        setDraft(createDraft(result));

        setError("");
      })
      .catch((caught: unknown) => {
        if (!active) {
          return;
        }

        setError(caught instanceof Error ? caught.message : "Unable to load application.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [applicationId]);

  function updateDraft(values: Partial<ApplicationDraft>) {
    setDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        ...values,
      };
    });
  }

  function cancelEditing() {
    if (!application) {
      return;
    }

    setDraft(createDraft(application));

    setEditing(false);
    setError("");
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!draft) {
      return;
    }

    setSaving(true);
    setError("");

    try {
      const updated = await updateApplication(applicationId, {
        company: draft.company.trim(),

        role: draft.role.trim(),

        location: draft.location.trim() || null,

        job_url: draft.jobUrl.trim() || null,

        applied_at: draft.appliedAt,

        status: draft.status,

        notes: draft.notes.trim() || null,
      });

      setApplication(updated);

      setDraft(createDraft(updated));

      setEditing(false);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update application.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!application) {
      return;
    }

    const confirmed = window.confirm(`Delete ${application.company} ? ${application.role}?`);

    if (!confirmed) {
      return;
    }

    setDeleting(true);
    setError("");

    try {
      await deleteApplication(application.id);

      router.replace("/applications");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete application.");

      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[65vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto size-10 animate-pulse rounded-xl bg-indigo-500" />

          <p className="mt-4 text-sm font-medium text-slate-500">Loading application...</p>
        </div>
      </div>
    );
  }

  if (error && !application) {
    return (
      <div className="mx-auto max-w-2xl py-12">
        <div className="rounded-2xl border border-red-200 bg-white p-8 text-center shadow-sm">
          <div className="mx-auto flex size-12 items-center justify-center rounded-2xl bg-red-50 text-red-600">
            <ApplicationsIcon className="size-5" />
          </div>

          <h1 className="mt-4 text-xl font-bold text-slate-950">Application unavailable</h1>

          <p className="mt-2 text-sm leading-6 text-slate-500">{error}</p>

          <Link
            href="/applications"
            className="mt-6 inline-flex h-11 items-center justify-center rounded-xl bg-slate-950 px-5 text-sm font-semibold text-white"
          >
            Back to Applications
          </Link>
        </div>
      </div>
    );
  }

  if (!application || !draft) {
    return null;
  }

  return (
    <div>
      <Link
        href="/applications"
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-indigo-600"
      >
        <ArrowLeftIcon className="size-4" />
        Back to Applications
      </Link>

      <div className="mt-5 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <span
              className={[
                "inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1",
                statusClasses[application.status],
              ].join(" ")}
            >
              {statusLabels[application.status]}
            </span>

            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
              {sourceLabel(application.source)}
            </span>
          </div>

          <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            {application.role}
          </h1>

          <p className="mt-2 text-lg font-semibold text-slate-600">{application.company}</p>
        </div>

        <div className="flex flex-wrap gap-3">
          {!editing ? (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="h-11 rounded-xl border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Edit application
            </button>
          ) : null}

          <button
            type="button"
            disabled={deleting}
            onClick={() => void handleDelete()}
            className="h-11 rounded-xl border border-red-200 bg-white px-5 text-sm font-semibold text-red-600 transition hover:bg-red-50 disabled:opacity-50"
          >
            {deleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      {error ? (
        <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <CalendarIcon className="size-5" />
          </div>

          <p className="mt-4 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Applied
          </p>

          <p className="mt-1 font-semibold text-slate-950">{formatDate(application.applied_at)}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <BriefcaseIcon className="size-5" />
          </div>

          <p className="mt-4 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Location
          </p>

          <p className="mt-1 font-semibold text-slate-950">
            {application.location || "Not specified"}
          </p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <ApplicationsIcon className="size-5" />
          </div>

          <p className="mt-4 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Source
          </p>

          <p className="mt-1 font-semibold text-slate-950">{sourceLabel(application.source)}</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
            <TargetIcon className="size-5" />
          </div>

          <p className="mt-4 text-xs font-semibold tracking-wide text-slate-500 uppercase">
            Last updated
          </p>

          <p className="mt-1 text-sm font-semibold text-slate-950">
            {formatDateTime(application.updated_at)}
          </p>
        </div>
      </div>

      {editing ? (
        <form
          onSubmit={handleSave}
          className="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm"
        >
          <div className="border-b border-slate-100 px-6 py-5">
            <h2 className="text-base font-semibold text-slate-950">Edit application</h2>

            <p className="mt-1 text-sm text-slate-500">
              Update the application details or current stage.
            </p>
          </div>

          <div className="grid gap-5 p-6 md:grid-cols-2">
            <div>
              <label htmlFor="detail-company" className="text-sm font-semibold text-slate-700">
                Company
              </label>

              <input
                id="detail-company"
                value={draft.company}
                onChange={(event) =>
                  updateDraft({
                    company: event.target.value,
                  })
                }
                required
                maxLength={160}
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <div>
              <label htmlFor="detail-role" className="text-sm font-semibold text-slate-700">
                Role
              </label>

              <input
                id="detail-role"
                value={draft.role}
                onChange={(event) =>
                  updateDraft({
                    role: event.target.value,
                  })
                }
                required
                maxLength={200}
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <div>
              <label htmlFor="detail-location" className="text-sm font-semibold text-slate-700">
                Location
              </label>

              <input
                id="detail-location"
                value={draft.location}
                onChange={(event) =>
                  updateDraft({
                    location: event.target.value,
                  })
                }
                maxLength={160}
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <div>
              <label htmlFor="detail-job-url" className="text-sm font-semibold text-slate-700">
                Job URL
              </label>

              <input
                id="detail-job-url"
                type="url"
                value={draft.jobUrl}
                onChange={(event) =>
                  updateDraft({
                    jobUrl: event.target.value,
                  })
                }
                placeholder="https://..."
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <div>
              <label htmlFor="detail-applied-at" className="text-sm font-semibold text-slate-700">
                Applied date
              </label>

              <input
                id="detail-applied-at"
                type="date"
                value={draft.appliedAt}
                onChange={(event) =>
                  updateDraft({
                    appliedAt: event.target.value,
                  })
                }
                required
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <div>
              <label htmlFor="detail-status" className="text-sm font-semibold text-slate-700">
                Status
              </label>

              <select
                id="detail-status"
                value={draft.status}
                onChange={(event) =>
                  updateDraft({
                    status: event.target.value as ApplicationStatus,
                  })
                }
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              >
                {statusOptions.map((item) => (
                  <option key={item} value={item}>
                    {statusLabels[item]}
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              <label htmlFor="detail-notes" className="text-sm font-semibold text-slate-700">
                Notes
              </label>

              <textarea
                id="detail-notes"
                value={draft.notes}
                onChange={(event) =>
                  updateDraft({
                    notes: event.target.value,
                  })
                }
                rows={5}
                maxLength={5000}
                className="mt-2 w-full resize-none rounded-xl border border-slate-200 p-4 text-sm outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 border-t border-slate-100 px-6 py-5">
            <button
              type="button"
              disabled={saving}
              onClick={cancelEditing}
              className="h-11 rounded-xl border border-slate-200 px-5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={saving}
              className="h-11 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save changes"}
            </button>
          </div>
        </form>
      ) : (
        <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_minmax(320px,0.7fr)]">
          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 py-5">
              <h2 className="text-base font-semibold text-slate-950">Application details</h2>
            </div>

            <div className="divide-y divide-slate-100">
              <div className="grid gap-2 px-6 py-4 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-medium text-slate-500">Company</p>

                <p className="text-sm font-semibold text-slate-950">{application.company}</p>
              </div>

              <div className="grid gap-2 px-6 py-4 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-medium text-slate-500">Role</p>

                <p className="text-sm font-semibold text-slate-950">{application.role}</p>
              </div>

              <div className="grid gap-2 px-6 py-4 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-medium text-slate-500">Status</p>

                <p className="text-sm font-semibold text-slate-950">
                  {statusLabels[application.status]}
                </p>
              </div>

              <div className="grid gap-2 px-6 py-4 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-medium text-slate-500">Job posting</p>

                {application.job_url ? (
                  <a
                    href={application.job_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-sm font-semibold break-all text-indigo-600 hover:text-indigo-700"
                  >
                    Open job posting ?
                  </a>
                ) : (
                  <p className="text-sm text-slate-500">Not provided</p>
                )}
              </div>

              <div className="grid gap-2 px-6 py-4 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-medium text-slate-500">External ID</p>

                <p className="text-sm text-slate-700">
                  {application.external_id || "Not available"}
                </p>
              </div>

              <div className="grid gap-2 px-6 py-4 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-medium text-slate-500">Created</p>

                <p className="text-sm text-slate-700">{formatDateTime(application.created_at)}</p>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-6 py-5">
              <h2 className="text-base font-semibold text-slate-950">Notes</h2>
            </div>

            <div className="p-6">
              <p className="text-sm leading-7 whitespace-pre-wrap text-slate-600">
                {application.notes || "No notes have been added."}
              </p>
            </div>
          </section>
        </div>
      )}

      
      <ApplicationTimeline key={application.updated_at} applicationId={application.id} />
    </div>
  );
}
