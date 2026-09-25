import { useId, useState, type InputHTMLAttributes } from "react";

interface AuthFieldProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, "size" | "id"> {
  label: string;
  error?: string | null;
  hint?: string;
  /** Shows a show/hide toggle for password inputs. */
  revealable?: boolean;
}

const inputClass = (hasError: boolean): string =>
  `w-full rounded-lg border bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition-all duration-200 placeholder:text-slate-400 focus:ring-4 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-500 ${
    hasError
      ? "border-red-500 focus:border-red-500 focus:ring-red-500/15 dark:border-red-500/70"
      : "border-slate-300 focus:border-blue-500 focus:ring-blue-500/15 dark:border-slate-700 dark:focus:border-blue-500"
  }`;

/**
 * Themed form field for the public auth pages (dark-first, light toggle).
 * Accessible by default: real <label>, aria-invalid, error linked via
 * aria-describedby, visible focus ring, keyboard-operable reveal toggle.
 */
export default function AuthField({
  label,
  error,
  hint,
  revealable = false,
  required = false,
  type = "text",
  ...props
}: AuthFieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const [revealed, setRevealed] = useState(false);

  const resolvedType =
    revealable && type === "password" && revealed ? "text" : type;

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block text-[13px] font-semibold text-slate-700 dark:text-slate-300"
      >
        {label}
        {required && (
          <span aria-hidden="true" className="text-blue-600 dark:text-blue-400">
            {" "}
            *
          </span>
        )}
      </label>
      <div className="relative">
        <input
          id={id}
          type={resolvedType}
          required={required}
          aria-invalid={Boolean(error)}
          aria-describedby={[errorId, hintId].filter(Boolean).join(" ") || undefined}
          className={`${inputClass(Boolean(error))} ${revealable ? "pr-16" : ""}`}
          {...props}
        />
        {revealable && (
          <button
            type="button"
            onClick={() => setRevealed((v) => !v)}
            aria-pressed={revealed}
            aria-label={revealed ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-0 rounded-r-lg px-3 text-xs font-semibold text-slate-500 transition-colors hover:text-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-blue-500 dark:text-slate-400 dark:hover:text-slate-100"
          >
            {revealed ? "Hide" : "Show"}
          </button>
        )}
      </div>
      {error ? (
        <p id={errorId} role="alert" className="text-xs text-red-600 dark:text-red-400">
          {error}
        </p>
      ) : hint ? (
        <p id={hintId} className="text-xs text-slate-500 dark:text-slate-500">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
