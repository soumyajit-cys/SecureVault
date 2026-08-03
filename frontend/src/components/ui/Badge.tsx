type BadgeColor =
  | "green"
  | "red"
  | "amber"
  | "cyan"
  | "purple"
  | "slate"
  | "indigo";

interface BadgeProps {
  color?: BadgeColor;
  children: React.ReactNode;
}

const colors: Record<BadgeColor, string> = {
  green: "bg-emerald-500/10 text-emerald-300 ring-emerald-400/30",
  red: "bg-red-500/10 text-red-300 ring-red-400/30",
  amber: "bg-amber-500/10 text-amber-300 ring-amber-400/30",
  cyan: "bg-cyan-500/10 text-cyan-300 ring-cyan-400/30",
  purple: "bg-purple-500/10 text-purple-300 ring-purple-400/30",
  indigo: "bg-brand-500/10 text-brand-300 ring-brand-400/30",
  slate: "bg-slate-500/10 text-slate-300 ring-slate-400/30"
};

export default function Badge({ children, color = "slate" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${colors[color]}`}
    >
      {children}
    </span>
  );
}