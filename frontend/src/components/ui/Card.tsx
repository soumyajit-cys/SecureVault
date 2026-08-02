import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export default function Card({
  title,
  subtitle,
  action,
  children,
  className = ""
}: CardProps) {
  return (
    <section
      className={`rounded-xl border border-slate-200 bg-white shadow-card ${className}`}
    >
      {(title || action) && (
        <header className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}