export interface PasswordCheck {
  id: string;
  label: string;
  pass: boolean;
}

export function checkPassword(password: string): PasswordCheck[] {
  return [
    {
      id: "length",
      label: "At least 12 characters",
      pass: password.length >= 12
    },
    {
      id: "upper",
      label: "One uppercase letter",
      pass: /[A-Z]/.test(password)
    },
    {
      id: "lower",
      label: "One lowercase letter",
      pass: /[a-z]/.test(password)
    },
    {
      id: "number",
      label: "One number",
      pass: /\d/.test(password)
    },
    {
      id: "special",
      label: "One symbol (!@#$…)",
      pass: /[!@#$%^&*()_\-+=[\]{};:,.<>?]/.test(password)
    }
  ];
}

export type Strength = 0 | 1 | 2 | 3 | 4;

export function strengthOf(password: string): {
  level: Strength;
  label: string;
} {
  if (password.length === 0) return { level: 0, label: "Enter a password" };
  let score = 0;
  if (password.length >= 12) score += 1;
  if (password.length >= 16) score += 1;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1;
  if (/\d/.test(password) && /[!@#$%^&*()_\-+=[\]{};:,.<>?]/.test(password))
    score += 1;
  const level = Math.min(4, score) as Strength;
  return {
    level,
    label: ["Too short", "Weak", "Fair", "Strong", "Excellent"][level]
  };
}

const barColor = (level: Strength, index: number): string => {
  if (index >= level) return "bg-slate-300 dark:bg-slate-700";
  if (level <= 1) return "bg-red-500";
  if (level === 2) return "bg-amber-500";
  if (level === 3) return "bg-blue-500";
  return "bg-emerald-500";
};

interface PasswordStrengthProps {
  password: string;
  /** Compact mode hides the per-rule checklist (used on reset-confirm). */
  compact?: boolean;
}

/**
 * Live password feedback aligned to the backend `PasswordPolicy`
 * (min 12, upper, lower, number, special). Purely advisory client-side —
 * the server re-validates and runs the HIBP breach screen.
 */
export default function PasswordStrength({
  password,
  compact = false
}: PasswordStrengthProps) {
  const { level, label } = strengthOf(password);
  const checks = checkPassword(password);

  if (password.length === 0) return null;

  return (
    <div aria-live="polite" className="space-y-2">
      <div className="flex items-center gap-2">
        <div
          className="flex flex-1 gap-1"
          role="img"
          aria-label={`Password strength: ${label}`}
        >
          {[0, 1, 2, 3].map((i) => (
            <span
              key={i}
              className={`h-1.5 flex-1 rounded-full transition-colors ${barColor(level, i + 1)}`}
            />
          ))}
        </div>
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
          {label}
        </span>
      </div>
      {!compact && (
        <ul className="grid grid-cols-1 gap-1 text-xs sm:grid-cols-2">
          {checks.map((c) => (
            <li
              key={c.id}
              className={
                c.pass
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-slate-500 dark:text-slate-500"
              }
            >
              <span aria-hidden="true">{c.pass ? "✓ " : "○ "}</span>
              {c.label}
              <span className="sr-only">{c.pass ? " (met)" : " (missing)"}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
