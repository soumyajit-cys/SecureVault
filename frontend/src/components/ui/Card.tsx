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
      className={`rounded-lg border border-vault-700 bg-vault-900/70 shadow-lg backdrop-blur ${className}`}
    >
      {(title || action) && (
        <header className="flex items-center justify-between border-b border-vault-700 px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-100">
              {title}
            </h2>
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      <div className="p-5">{children}</div>
    </section>
  );
}