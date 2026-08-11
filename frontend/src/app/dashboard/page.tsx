import {
  AnalyticsIcon,
  ApplicationsIcon,
  ArrowRightIcon,
  BriefcaseIcon,
  CalendarIcon,
  ResumeIcon,
  TargetIcon,
} from "@/components/dashboard/icons";
import { EmptyState } from "@/components/dashboard/empty-state";
import { SectionCard } from "@/components/dashboard/section-card";
import { StatCard } from "@/components/dashboard/stat-card";

const stats = [
  {
    title: "Applications",
    value: "?",
    detail: "Application tracking arrives on Day 23.",
    icon: BriefcaseIcon,
  },
  {
    title: "Interviews",
    value: "?",
    detail: "Interview activity will appear as your pipeline grows.",
    icon: TargetIcon,
  },
  {
    title: "Average ATS Score",
    value: "?",
    detail: "Scores will be populated from optimized resume workflows.",
    icon: ResumeIcon,
  },
  {
    title: "Upcoming Deadlines",
    value: "?",
    detail: "Application and assessment deadlines will appear here.",
    icon: CalendarIcon,
  },
];

export default function DashboardPage() {
  return (
    <div>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-indigo-600">Career Intelligence</p>

          <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-950 sm:text-4xl">
            Dashboard
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 sm:text-base">
            A single workspace for your applications, resume intelligence, deadlines, and career
            progress.
          </p>
        </div>

        <button
          type="button"
          disabled
          className="inline-flex h-11 cursor-not-allowed items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 text-sm font-semibold text-white opacity-70"
          title="Application creation will be implemented on Day 23"
        >
          Add application
          <ArrowRightIcon className="size-4" />
        </button>
      </div>

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </section>

      <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,0.8fr)]">
        <SectionCard
          title="Recent Applications"
          description="Track your latest job applications and their current stage."
        >
          <EmptyState
            icon={ApplicationsIcon}
            title="Application tracking is coming next"
            description="Day 23 will add the Applications page and connect this dashboard section to real application data."
          />
        </SectionCard>

        <SectionCard
          title="Upcoming Deadlines"
          description="Keep important application milestones visible."
        >
          <EmptyState
            icon={CalendarIcon}
            title="No deadlines yet"
            description="Assessment, interview, and follow-up deadlines will appear here as applications are added."
          />
        </SectionCard>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <SectionCard
          title="Application Pipeline"
          description="A quick view of progress across your job search."
        >
          <EmptyState
            icon={AnalyticsIcon}
            title="Pipeline analytics will appear here"
            description="Future dashboard milestones will visualize application stages and conversion rates."
          />
        </SectionCard>

        <SectionCard
          title="Career Intelligence"
          description="Insights produced by your AI career workflows."
        >
          <div className="grid gap-3">
            {[
              {
                title: "Resume intelligence",
                detail: "Resume parsing, matching, ATS optimization, and version intelligence.",
                icon: ResumeIcon,
              },
              {
                title: "Job matching",
                detail: "Match scores, missing skills, and role-specific recommendations.",
                icon: TargetIcon,
              },
              {
                title: "Application intelligence",
                detail: "Application history and timeline insights will connect during Week 4.",
                icon: BriefcaseIcon,
              },
            ].map((item) => {
              const Icon = item.icon;

              return (
                <div
                  key={item.title}
                  className="flex gap-4 rounded-xl border border-slate-100 bg-slate-50 p-4"
                >
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-white text-indigo-600 shadow-sm ring-1 ring-slate-200">
                    <Icon className="size-5" />
                  </div>

                  <div>
                    <p className="text-sm font-semibold text-slate-900">{item.title}</p>

                    <p className="mt-1 text-xs leading-5 text-slate-500">{item.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
