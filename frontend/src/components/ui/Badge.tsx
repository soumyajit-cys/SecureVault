interface BadgeProps {
  color?: "green" | "red" | "amber" | "cyan" | "purple" | "slate";
  children: React.ReactNode;
}

const colors: Record<BadgeProps["color"], string> = {
  green: "bg-neon-green/15 text-neon-green border-neon-green/40",
  red: "bg-neon-red/15 text-neon-red border-neon-red/40",
  amber: "bg-neon-amber/15 text-neon-amber border-neon-amber/40",
  cyan: "bg-neon-cyan/15 text-neon-cyan border-neon-cyan/40",
  purple: "bg-neon-purple/15 text-neon-purple border-neon-purple/40",
  slate: "bg-slate-500/15 text-slate-300 border-slate-500/40"
};

export default function Badge({
  children,
  color = "slate"
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${colors[color]}`}
    >
      {children}
    </span>
  );
}