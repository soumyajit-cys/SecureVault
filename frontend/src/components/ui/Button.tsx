import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger" | "success" | "outline";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  children: ReactNode;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-brand-gradient text-white shadow-glow-sm hover:shadow-glow hover:brightness-110 focus-visible:outline-accent",
  outline:
    "border border-cyber-line bg-surface-elevated/60 text-ink-soft shadow-sm hover:border-accent/40 hover:bg-surface-elevated hover:text-ink hover:shadow-glow-cyan focus-visible:outline-accent",
  ghost: "text-ink-soft hover:bg-surface-muted hover:text-ink",
  danger:
    "bg-red-600/90 text-white shadow-sm hover:bg-red-600 hover:shadow-glow focus-visible:outline-red-500",
  success:
    "bg-emerald-600/90 text-white shadow-sm hover:bg-emerald-500 hover:shadow-glow focus-visible:outline-emerald-500"
};

const sizes: Record<Size, string> = {
  sm: "px-2.5 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-5 py-2.5 text-sm"
};

export default function Button({
  variant = "primary",
  size = "md",
  loading = false,
  className = "",
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 ease-in-out-soft focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-50 active:scale-[0.98] ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
}
