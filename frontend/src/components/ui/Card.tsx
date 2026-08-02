import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  elevated?: boolean;
  gradient?: boolean;
}

export default function Card({
  title,
  subtitle,
  action,
  children,
  className = "",
  elevated = false,
  gradient = false
}: CardProps) {
  return (
    <section
      className={`${gradient ? "bg-brand-gradient text-white" : "border border-slate-200/70 bg-white"} rounded-2xl shadow-card ${
        elevated ? "shadow-card-hover" : ""
      } hover:border-brand-200/70 ${className}`}
    >
      {(title || action) && (
        <header
          className={`flex items-center justify-between gap-4 ${
            gradient ? "border-white/10" : "border-slate-200/70"
          } border-b px-5 py-4`}
        >
          <div>
            <h2 className={`text-sm font-semibold ${gradient ? "text-white" : "text-slate-900"}`}>
              {title}
            </h2>
            {subtitle && (
              <p className={`mt-0.5 text-xs ${gradient ? "text-white/70" : "text-slate-500"}`}>
                {subtitle}
              </p>
            )}
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}