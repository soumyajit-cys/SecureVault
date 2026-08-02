import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "danger" | "success" | "outline";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "sm" | "md";
  loading?: boolean;
  children: ReactNode;
}

const variants: Record<Variant, string> = {
  primary:
    "bg-neon-cyan/90 text-vault-950 hover:bg-neon-cyan shadow-glow font-semibold",
  outline:
    "border border-vault-600 text-slate-200 hover:border-neon-cyan/60 hover:text-neon-cyan",
  ghost: "text-slate-300 hover:text-white hover:bg-vault-800",
  danger: "bg-neon-red/90 text-vault-950 hover:bg-neon-red font-semibold",
  success:
    "bg-neon-green/90 text-vault-950 hover:bg-neon-green shadow-glow-green font-semibold"
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
      className={`inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${
        size === "sm" ? "px-2.5 py-1 text-xs" : "px-4 py-2 text-sm"
      } ${className}`}
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