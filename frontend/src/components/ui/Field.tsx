import type { InputHTMLAttributes, TextareaHTMLAttributes } from "react";

interface FieldProps {
  label?: string;
  hint?: string;
  required?: boolean;
  error?: string;
}

const baseField =
  "w-full rounded-md border border-vault-600 bg-vault-900 px-3 py-2 text-sm text-slate-100 placeholder:text-slate-500 outline-none transition-colors focus:border-neon-cyan/70 focus:ring-1 focus:ring-neon-cyan/40";

const labelClass =
  "mb-1 block text-xs font-medium uppercase tracking-wider text-slate-400";

export function Label({ children }: { children: string }) {
  return <span className={labelClass}>{children}</span>;
}

interface FieldShellProps extends InputProps {
  id: string;
  error?: string;
}

function FieldShell({ label, hint, required, error, children }: FieldShellProps & { children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      {label && (
        <label htmlFor={label.toLowerCase().replace(/\s+/g, "-")} className={labelClass}>
          {label}
          {required && <span className="text-neon-red"> *</span>}
        </label>
      )}
      {children}
      {error ? (
        <p className="text-xs text-neon-red">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}

interface TextFieldProps extends InputProps, InputHTMLAttributes<HTMLInputElement> {}

export function TextField({ label, hint, required, error, className = "", ...props }: TextFieldProps) {
  return (
    <FieldShell label={label} hint={hint} required={required} error={error}>
      <input className={`${baseField} ${error ? "border-neon-red" : ""} ${className}`} {...props} />
    </FieldShell>
  );
}

interface TextAreaProps extends InputProps, TextareaHTMLAttributes<HTMLTextAreaElement> {}

export function TextArea({ label, hint, required, error, className = "", ...props }: TextAreaProps) {
  return (
    <FieldShell label={label} hint={hint} required={required} error={error}>
      <textarea className={`${baseField} min-h-[120px] resize-y ${className}`} {...props} />
    </FieldShell>
  );
}

interface SelectFieldProps extends InputProps, React.SelectHTMLAttributes<HTMLSelectElement> {}

export function SelectField({
  label,
  hint,
  required,
  error,
  className = "",
  children,
  ...props
}: SelectFieldProps) {
  return (
    <FieldShell label={label} hint={hint} required={required} error={error}>
      <select className={`${baseField} ${className}`} {...props}>
        {children}
      </select>
    </FieldShell>
  );
}