"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { ApplicationForm } from "@/components/applications/application-form";
import { ApplicationsIcon, BriefcaseIcon, SearchIcon } from "@/components/dashboard/icons";
import {
  deleteApplication,
  listApplications,
  type Application,
  type ApplicationSortField,
  type ApplicationStatus,
  updateApplication,
} from "@/lib/applications";

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

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

export function ApplicationsPage() {
  const [applications, setApplications] = useState<Application[]>([]);

  const [total, setTotal] = useState(0);

  const [search, setSearch] = useState("");

  const [status, setStatus] = useState<ApplicationStatus | "">("");

  const [sortBy, setSortBy] = useState<ApplicationSortField>("applied_at");

  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const [page, setPage] = useState(1);

  const pageSize = 20;

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [showForm, setShowForm] = useState(false);

  const [reloadKey, setReloadKey] = useState(0);

  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    const timer = window.setTimeout(() => {
      listApplications({
        search,
        status,
        sortBy,
        sortOrder,
        page,
        pageSize,
      })
        .then((result) => {
          if (!active) {
            return;
          }

          setApplications(result.items);

          setTotal(result.total);

          setError("");
        })
        .catch((caught: unknown) => {
          if (!active) {
            return;
          }

          setError(caught instanceof Error ? caught.message : "Unable to load applications.");
        })
        .finally(() => {
          if (active) {
            setLoading(false);
          }
        });
    }, 250);

    return () => {
      active = false;

      window.clearTimeout(timer);
    };
  }, [page, reloadKey, search, sortBy, sortOrder, status]);

  function refreshApplications() {
    setLoading(true);

    setReloadKey((value) => value + 1);
  }

  async function handleStatusChange(application: Application, nextStatus: ApplicationStatus) {
    setUpdatingId(application.id);

    try {
      const updated = await updateApplication(application.id, {
        status: nextStatus,
      });

      setApplications((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to update application.");
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleDelete(application: Application) {
    const confirmed = window.confirm(`Delete ${application.company} | ${application.role}?`);

    if (!confirmed) {
      return;
    }

    setUpdatingId(application.id);

    try {
      await deleteApplication(application.id);

      refreshApplications();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to delete application.");
    } finally {
      setUpdatingId(null);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <>
      <div>
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-indigo-600">Application Intelligence</p>

            <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
              Applications
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">
              Track every opportunity from application to offer in one workspace.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700"
          >
            <span className="text-lg leading-none">+</span>
            Add application
          </button>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                <BriefcaseIcon className="size-5" />
              </div>

              <div>
                <p className="text-xs font-medium text-slate-500">Total applications</p>

                <p className="text-2xl font-bold text-slate-950">{total}</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Interviews</p>

            <p className="mt-2 text-2xl font-bold text-slate-950">
              {applications.filter((item) => item.status === "interview").length}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-xs font-medium text-slate-500">Offers</p>

            <p className="mt-2 text-2xl font-bold text-slate-950">
              {applications.filter((item) => item.status === "offer").length}
            </p>
          </div>
        </div>

        <section className="mt-6 rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="grid gap-3 border-b border-slate-100 p-4 lg:grid-cols-[minmax(260px,1fr)_200px_200px_150px]">
            <div className="relative">
              <SearchIcon className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />

              <input
                type="search"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);

                  setPage(1);
                  setLoading(true);
                }}
                placeholder="Search company, role or location..."
                className="h-11 w-full rounded-xl border border-slate-200 bg-slate-50 pr-4 pl-10 text-sm transition outline-none focus:border-indigo-400 focus:bg-white focus:ring-4 focus:ring-indigo-50"
              />
            </div>

            <select
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as ApplicationStatus | "");

                setPage(1);
                setLoading(true);
              }}
              className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none"
            >
              <option value="">All statuses</option>

              {statusOptions.map((item) => (
                <option key={item} value={item}>
                  {statusLabels[item]}
                </option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value as ApplicationSortField);

                setPage(1);
                setLoading(true);
              }}
              className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none"
            >
              <option value="applied_at">Applied date</option>

              <option value="created_at">Created date</option>

              <option value="company">Company</option>

              <option value="role">Role</option>

              <option value="status">Status</option>
            </select>

            <select
              value={sortOrder}
              onChange={(event) => {
                setSortOrder(event.target.value as "asc" | "desc");

                setPage(1);
                setLoading(true);
              }}
              className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none"
            >
              <option value="desc">Descending</option>

              <option value="asc">Ascending</option>
            </select>
          </div>

          {error ? (
            <div className="m-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          {loading ? (
            <div className="flex min-h-72 items-center justify-center">
              <div className="text-center">
                <div className="mx-auto size-9 animate-pulse rounded-xl bg-indigo-500" />

                <p className="mt-3 text-sm text-slate-500">Loading applications...</p>
              </div>
            </div>
          ) : applications.length === 0 ? (
            <div className="flex min-h-80 flex-col items-center justify-center px-6 text-center">
              <div className="flex size-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
                <ApplicationsIcon className="size-6" />
              </div>

              <h2 className="mt-4 text-base font-semibold text-slate-950">No applications found</h2>

              <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                Add your first job application or change the current search filters.
              </p>

              <button
                type="button"
                onClick={() => setShowForm(true)}
                className="mt-5 rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-semibold text-white"
              >
                Add application
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[900px] text-left">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/70 text-xs font-semibold tracking-wide text-slate-500 uppercase">
                    <th className="px-5 py-4">Company / Role</th>

                    <th className="px-5 py-4">Location</th>

                    <th className="px-5 py-4">Applied</th>

                    <th className="px-5 py-4">Status</th>

                    <th className="px-5 py-4">Source</th>

                    <th className="px-5 py-4 text-right">Actions</th>
                  </tr>
                </thead>

                <tbody>
                  {applications.map((application) => (
                    <tr
                      key={application.id}
                      className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60"
                    >
                      <td className="px-5 py-4">
                        <p className="font-semibold text-slate-950">{application.company}</p>

                        <p className="mt-1 text-sm text-slate-500">{application.role}</p>

                        {application.job_url ? (
                          <a
                            href={application.job_url}
                            target="_blank"
                            rel="noreferrer"
                            className="mt-1 inline-block text-xs font-semibold text-indigo-600 hover:text-indigo-700"
                          >
                            Open job posting
                          </a>
                        ) : null}
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-600">
                        {application.location || "Not specified"}
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-600">
                        {formatDate(application.applied_at)}
                      </td>

                      <td className="px-5 py-4">
                        <select
                          value={application.status}
                          disabled={updatingId === application.id}
                          onChange={(event) =>
                            void handleStatusChange(
                              application,
                              event.target.value as ApplicationStatus,
                            )
                          }
                          className="h-9 rounded-lg border border-slate-200 bg-white px-2 text-xs font-semibold text-slate-700 outline-none disabled:opacity-50"
                        >
                          {statusOptions.map((item) => (
                            <option key={item} value={item}>
                              {statusLabels[item]}
                            </option>
                          ))}
                        </select>
                      </td>

                      <td className="px-5 py-4">
                        <span className="rounded-lg bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 capitalize">
                          {application.source}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-right">
                        <div className="flex justify-end gap-1">
                          <Link
                            href={`/applications/${application.id}`}
                            className="rounded-lg px-3 py-2 text-xs font-semibold text-indigo-600 transition hover:bg-indigo-50"
                          >
                            View details
                          </Link>

                          <button
                            type="button"
                            disabled={updatingId === application.id}
                            onClick={() => void handleDelete(application)}
                            className="rounded-lg px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {total > pageSize ? (
            <div className="flex items-center justify-between border-t border-slate-100 px-5 py-4">
              <p className="text-sm text-slate-500">
                Page {page} of {totalPages}
              </p>

              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => {
                    setPage((value) => Math.max(1, value - 1));

                    setLoading(true);
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 disabled:opacity-40"
                >
                  Previous
                </button>

                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => {
                    setPage((value) => Math.min(totalPages, value + 1));

                    setLoading(true);
                  }}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </section>
      </div>

      {showForm ? (
        <ApplicationForm
          onClose={() => setShowForm(false)}
          onCreated={() => {
            setShowForm(false);

            refreshApplications();
          }}
        />
      ) : null}
    </>
  );
}
