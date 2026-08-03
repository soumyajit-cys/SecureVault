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
          ? "border border-brand-500/30 bg-brand-gradient shadow-glow-sm"
          : "border border-cyber-line bg-surface-elevated/60 backdrop-blur-xl"
      } rounded-2xl shadow-card ${
        elevated ? "shadow-card-hover" : ""
      } hover:border-accent/30 ${className}`}
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