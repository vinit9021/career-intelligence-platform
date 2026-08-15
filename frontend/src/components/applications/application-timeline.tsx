"use client";

import type { FormEvent } from "react";
import { useEffect, useState } from "react";

import {
  createApplicationTimelineEvent,
  deleteApplicationTimelineEvent,
  listApplicationTimeline,
  type ApplicationTimelineEvent,
  type TimelineEventType,
  updateApplicationTimelineEvent,
} from "@/lib/applications";

interface ApplicationTimelineProps {
  applicationId: string;
}

interface EventDraft {
  eventType: TimelineEventType;
  title: string;
  description: string;
  eventAt: string;
}

const eventTypeOptions: Array<{
  value: TimelineEventType;
  label: string;
}> = [
  {
    value: "note",
    label: "General Note",
  },
  {
    value: "online_assessment_received",
    label: "Online Assessment Received",
  },
  {
    value: "online_assessment_completed",
    label: "Online Assessment Completed",
  },
  {
    value: "interview_scheduled",
    label: "Interview Scheduled",
  },
  {
    value: "interview_completed",
    label: "Interview Completed",
  },
  {
    value: "offer_received",
    label: "Offer Received",
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

const eventLabels: Record<TimelineEventType, string> = {
  application_submitted: "Application Submitted",
  status_changed: "Status Changed",
  online_assessment_received: "Online Assessment Received",
  online_assessment_completed: "Online Assessment Completed",
  interview_scheduled: "Interview Scheduled",
  interview_completed: "Interview Completed",
  offer_received: "Offer Received",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
  note: "Note",
};

function getLocalDateTime(): string {
  const now = new Date();

  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);

  return local.toISOString().slice(0, 16);
}

function toLocalDateTime(value: string): string {
  const date = new Date(value);

  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);

  return local.toISOString().slice(0, 16);
}

function emptyDraft(): EventDraft {
  return {
    eventType: "note",
    title: "",
    description: "",
    eventAt: getLocalDateTime(),
  };
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

function sourceLabel(source: ApplicationTimelineEvent["source"]): string {
  switch (source) {
    case "gmail":
      return "Gmail";

    case "integration":
      return "Integration";

    case "system":
      return "System";

    default:
      return "Manual";
  }
}

export function ApplicationTimeline({ applicationId }: ApplicationTimelineProps) {
  const [events, setEvents] = useState<ApplicationTimelineEvent[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [draft, setDraft] = useState<EventDraft>(emptyDraft);

  const [editing, setEditing] = useState<ApplicationTimelineEvent | null>(null);

  const [saving, setSaving] = useState(false);

  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;

    listApplicationTimeline(applicationId)
      .then((result) => {
        if (!active) {
          return;
        }

        setEvents(result);
        setError("");
      })
      .catch((caught: unknown) => {
        if (!active) {
          return;
        }

        setError(caught instanceof Error ? caught.message : "Unable to load application timeline.");
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [applicationId, reloadKey]);

  function refresh() {
    setLoading(true);

    setReloadKey((value) => value + 1);
  }

  function startAdd() {
    setEditing(null);

    setDraft(emptyDraft());

    setShowForm(true);
    setError("");
  }

  function startEdit(event: ApplicationTimelineEvent) {
    setEditing(event);

    setDraft({
      eventType: event.event_type,
      title: event.title,
      description: event.description ?? "",
      eventAt: toLocalDateTime(event.event_at),
    });

    setShowForm(true);
    setError("");
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);

    setDraft(emptyDraft());
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setSaving(true);
    setError("");

    const payload = {
      event_type: draft.eventType,

      title: draft.title.trim(),

      description: draft.description.trim() || null,

      event_at: new Date(draft.eventAt).toISOString(),
    };

    try {
      if (editing) {
        await updateApplicationTimelineEvent(applicationId, editing.id, payload);
      } else {
        await createApplicationTimelineEvent(applicationId, payload);
      }

      closeForm();
      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to save timeline event.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(event: ApplicationTimelineEvent) {
    const confirmed = window.confirm(`Delete "${event.title}"?`);

    if (!confirmed) {
      return;
    }

    setDeletingId(event.id);

    setError("");

    try {
      await deleteApplicationTimelineEvent(applicationId, event.id);

      refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete timeline event.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-col gap-4 border-b border-slate-100 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-950">Application Timeline</h2>

          <p className="mt-1 text-sm text-slate-500">
            Track application activity, assessments, interviews and other updates.
          </p>
        </div>

        <button
          type="button"
          onClick={startAdd}
          className="inline-flex h-10 items-center justify-center rounded-xl bg-indigo-600 px-4 text-sm font-semibold text-white transition hover:bg-indigo-700"
        >
          + Add event
        </button>
      </div>

      {error ? (
        <div className="mx-6 mt-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      {showForm ? (
        <form
          onSubmit={handleSubmit}
          className="m-6 rounded-2xl border border-indigo-100 bg-indigo-50/40 p-5"
        >
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-950">
              {editing ? "Edit timeline event" : "Add timeline event"}
            </h3>

            <button
              type="button"
              onClick={closeForm}
              className="text-sm font-semibold text-slate-500 hover:text-slate-900"
            >
              Cancel
            </button>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="timeline-type" className="text-sm font-semibold text-slate-700">
                Event type
              </label>

              <select
                id="timeline-type"
                value={draft.eventType}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,

                    eventType: event.target.value as TimelineEventType,
                  }))
                }
                className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
              >
                {eventTypeOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="timeline-date" className="text-sm font-semibold text-slate-700">
                Date & time
              </label>

              <input
                id="timeline-date"
                type="datetime-local"
                required
                value={draft.eventAt}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,

                    eventAt: event.target.value,
                  }))
                }
                className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
              />
            </div>

            <div className="md:col-span-2">
              <label htmlFor="timeline-title" className="text-sm font-semibold text-slate-700">
                Title
              </label>

              <input
                id="timeline-title"
                required
                maxLength={200}
                value={draft.title}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,

                    title: event.target.value,
                  }))
                }
                placeholder="Technical interview scheduled"
                className="mt-2 h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm"
              />
            </div>

            <div className="md:col-span-2">
              <label
                htmlFor="timeline-description"
                className="text-sm font-semibold text-slate-700"
              >
                Description
              </label>

              <textarea
                id="timeline-description"
                rows={4}
                maxLength={5000}
                value={draft.description}
                onChange={(event) =>
                  setDraft((current) => ({
                    ...current,

                    description: event.target.value,
                  }))
                }
                placeholder="Add useful details..."
                className="mt-2 w-full resize-none rounded-xl border border-slate-200 bg-white p-3 text-sm"
              />
            </div>
          </div>

          <div className="mt-5 flex justify-end gap-3">
            <button
              type="button"
              onClick={closeForm}
              disabled={saving}
              className="h-10 rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={saving}
              className="h-10 rounded-xl bg-indigo-600 px-4 text-sm font-semibold text-white disabled:opacity-50"
            >
              {saving ? "Saving..." : editing ? "Save changes" : "Add event"}
            </button>
          </div>
        </form>
      ) : null}

      {loading ? (
        <div className="flex min-h-52 items-center justify-center">
          <p className="text-sm text-slate-500">Loading timeline...</p>
        </div>
      ) : events.length === 0 ? (
        <div className="flex min-h-52 flex-col items-center justify-center px-6 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-indigo-50">
            <div className="size-3 rounded-full bg-indigo-600" />
          </div>

          <p className="mt-4 text-sm font-semibold text-slate-950">No timeline events yet</p>

          <p className="mt-1 text-sm text-slate-500">
            Add an event or change the application status.
          </p>
        </div>
      ) : (
        <div className="px-6 py-6">
          <div className="relative">
            <div className="absolute top-2 bottom-2 left-[7px] w-px bg-slate-200" />

            <div className="space-y-7">
              {events.map((event) => (
                <div key={event.id} className="relative pl-9">
                  <div className="absolute top-1.5 left-0 z-10 size-[15px] rounded-full bg-indigo-600 ring-4 ring-white" />

                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-950">{event.title}</h3>

                        <span className="rounded-lg bg-indigo-50 px-2 py-1 text-[11px] font-semibold text-indigo-700">
                          {eventLabels[event.event_type]}
                        </span>

                        <span className="rounded-lg bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">
                          {sourceLabel(event.source)}
                        </span>
                      </div>

                      <p className="mt-2 text-xs text-slate-500">
                        {formatDateTime(event.event_at)}
                      </p>

                      {event.description ? (
                        <p className="mt-3 text-sm leading-6 whitespace-pre-wrap text-slate-600">
                          {event.description}
                        </p>
                      ) : null}
                    </div>

                    {event.source === "manual" ? (
                      <div className="flex shrink-0 gap-1">
                        <button
                          type="button"
                          onClick={() => startEdit(event)}
                          className="rounded-lg px-3 py-2 text-xs font-semibold text-indigo-600 hover:bg-indigo-50"
                        >
                          Edit
                        </button>

                        <button
                          type="button"
                          disabled={deletingId === event.id}
                          onClick={() => void handleDelete(event)}
                          className="rounded-lg px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50"
                        >
                          {deletingId === event.id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
