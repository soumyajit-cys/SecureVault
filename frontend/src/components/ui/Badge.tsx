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
  green: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  red: "bg-red-50 text-red-700 ring-red-600/20",
  amber: "bg-amber-50 text-amber-700 ring-amber-600/20",
  cyan: "bg-cyan-50 text-cyan-700 ring-cyan-600/20",
  purple: "bg-purple-50 text-purple-700 ring-purple-600/20",
  indigo: "bg-brand-50 text-brand-700 ring-brand-600/20",
  slate: "bg-slate-100 text-slate-600 ring-slate-500/20"
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