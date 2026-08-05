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
      className={`${
        gradient
          ? "border border-brand-600/20 bg-brand-gradient shadow-card"
          : "border border-cyber-line bg-surface-elevated shadow-card"
      } rounded-xl ${elevated ? "shadow-card-hover" : ""} ${className}`}
    >
      {(title || action) && (
        <header
          className={`flex items-center justify-between gap-4 border-b ${
            gradient ? "border-white/15" : "border-cyber-line"
          } px-5 py-4`}
        >
          <div>
            <h2 className="text-sm font-semibold text-ink">{title}</h2>
            {subtitle && (
              <p className={`mt-0.5 text-xs ${gradient ? "text-white/70" : "text-ink-faint"}`}>
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