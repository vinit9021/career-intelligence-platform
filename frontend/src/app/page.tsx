import { env } from "@/lib/env";

const foundationItems = [
  "FastAPI backend",
  "Next.js App Router",
  "TypeScript",
  "Tailwind CSS",
  "React Query",
  "Environment validation",
  "Backend testing",
  "Linting and formatting",
];

export default function Home() {
  const apiDocsUrl = new URL("/docs", env.apiBaseUrl).toString();

  return (
    <main className="min-h-screen px-6 py-12 sm:px-10 lg:px-16">
      <div className="mx-auto max-w-6xl">
        <header className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm sm:p-12">
          <p className="mb-4 text-sm font-semibold tracking-widest text-indigo-600 uppercase">
            Development Foundation
          </p>

          <h1 className="max-w-4xl text-4xl font-bold tracking-tight text-slate-950 sm:text-6xl">
            Career Intelligence Platform
          </h1>

          <p className="mt-6 max-w-3xl text-lg leading-8 text-slate-600">
            An AI-powered operating system for resume intelligence, job matching, application
            tracking, online-assessment preparation, interview preparation, and recruiter
            communication.
          </p>

          <div className="mt-8 flex flex-wrap gap-4">
            <a
              href={apiDocsUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded-xl bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
            >
              Open API documentation
            </a>

            <span className="rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-700">
              Day 1 foundation
            </span>
          </div>
        </header>

        <section className="mt-8">
          <h2 className="text-2xl font-bold text-slate-950">Foundation configured</h2>

          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {foundationItems.map((item) => (
              <article
                key={item}
                className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="mb-4 flex size-9 items-center justify-center rounded-full bg-indigo-50 text-sm font-bold text-indigo-700">
                  ✓
                </div>

                <p className="font-semibold text-slate-800">{item}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
