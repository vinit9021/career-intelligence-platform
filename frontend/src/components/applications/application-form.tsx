"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import { CloseIcon } from "@/components/dashboard/icons";
import {
  createApplication,
  type Application,
  type ApplicationCreateInput,
  type ApplicationStatus,
} from "@/lib/applications";

interface ApplicationFormProps {
  onClose: () => void;

  onCreated: (application: Application) => void;
}

const statusOptions: Array<{
  value: ApplicationStatus;
  label: string;
}> = [
  {
    value: "applied",
    label: "Applied",
  },
  {
    value: "online_assessment",
    label: "Online Assessment",
  },
  {
    value: "interview",
    label: "Interview",
  },
  {
    value: "offer",
    label: "Offer",
  },
  {
    value: "rejected",
    label: "Rejected",
  },
  {
    value: "withdrawn",
    label: "Withdrawn",
  },
];

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function ApplicationForm({ onClose, onCreated }: ApplicationFormProps) {
  const [company, setCompany] = useState("");

  const [role, setRole] = useState("");

  const [location, setLocation] = useState("");

  const [jobUrl, setJobUrl] = useState("");

  const [appliedAt, setAppliedAt] = useState(today());

  const [status, setStatus] = useState<ApplicationStatus>("applied");

  const [notes, setNotes] = useState("");

  const [error, setError] = useState("");

  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setSaving(true);

    const payload: ApplicationCreateInput = {
      company: company.trim(),

      role: role.trim(),

      location: location.trim() || null,

      job_url: jobUrl.trim() || null,

      applied_at: appliedAt,

      status,

      notes: notes.trim() || null,
    };

    try {
      const application = await createApplication(payload);

      onCreated(application);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save the application.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-slate-950/45 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close application form"
      />

      <div className="relative h-full w-full max-w-xl overflow-y-auto bg-white shadow-2xl">
        <div className="sticky top-0 z-10 flex items-start justify-between border-b border-slate-200 bg-white/95 px-6 py-5 backdrop-blur">
          <div>
            <p className="text-sm font-semibold text-indigo-600">New application</p>

            <h2 className="mt-1 text-xl font-bold text-slate-950">Add job application</h2>

            <p className="mt-1 text-sm text-slate-500">
              Add an application manually to your career pipeline.
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="inline-flex size-10 items-center justify-center rounded-xl border border-slate-200 text-slate-500 transition hover:bg-slate-50"
            aria-label="Close"
          >
            <CloseIcon className="size-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 p-6">
          <div>
            <label htmlFor="company" className="text-sm font-semibold text-slate-700">
              Company *
            </label>

            <input
              id="company"
              value={company}
              onChange={(event) => setCompany(event.target.value)}
              placeholder="Google"
              required
              maxLength={160}
              className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
            />
          </div>

          <div>
            <label htmlFor="role" className="text-sm font-semibold text-slate-700">
              Role *
            </label>

            <input
              id="role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
              placeholder="Software Engineer"
              required
              maxLength={200}
              className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
            />
          </div>

          <div>
            <label htmlFor="location" className="text-sm font-semibold text-slate-700">
              Location
            </label>

            <input
              id="location"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              placeholder="Bengaluru, India"
              maxLength={160}
              className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
            />
          </div>

          <div>
            <label htmlFor="job-url" className="text-sm font-semibold text-slate-700">
              Job URL
            </label>

            <input
              id="job-url"
              type="url"
              value={jobUrl}
              onChange={(event) => setJobUrl(event.target.value)}
              placeholder="https://..."
              className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
            />
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <label htmlFor="applied-at" className="text-sm font-semibold text-slate-700">
                Applied date *
              </label>

              <input
                id="applied-at"
                type="date"
                value={appliedAt}
                onChange={(event) => setAppliedAt(event.target.value)}
                required
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 px-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <div>
              <label htmlFor="status" className="text-sm font-semibold text-slate-700">
                Status *
              </label>

              <select
                id="status"
                value={status}
                onChange={(event) => setStatus(event.target.value as ApplicationStatus)}
                className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-white px-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="notes" className="text-sm font-semibold text-slate-700">
              Notes
            </label>

            <textarea
              id="notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              placeholder="Referral, recruiter name, preparation notes..."
              rows={5}
              maxLength={5000}
              className="mt-2 w-full resize-none rounded-xl border border-slate-200 p-4 text-sm transition outline-none focus:border-indigo-400 focus:ring-4 focus:ring-indigo-50"
            />
          </div>

          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          <div className="flex gap-3 border-t border-slate-100 pt-5">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="h-11 flex-1 rounded-xl border border-slate-200 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={saving}
              className="h-11 flex-1 rounded-xl bg-indigo-600 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Saving..." : "Add application"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
