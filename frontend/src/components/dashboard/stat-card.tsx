import type { ComponentType, SVGProps } from "react";

interface StatCardProps {
  title: string;
  value: string;
  detail: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
}

export function StatCard({ title, value, detail, icon: Icon }: StatCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>

          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-950">{value}</p>
        </div>

        <div className="flex size-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
          <Icon className="size-5" />
        </div>
      </div>

      <p className="mt-4 text-xs leading-5 text-slate-500">{detail}</p>
    </article>
  );
}
