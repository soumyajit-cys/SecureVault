import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes
} from "react";

interface BaseFieldProps {
  label?: string;
  variant?: string;
  hint?: string;
  defaultShow?: boolean;
}

const baseField =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 shadow-sm outline-none transition-colors focus:border-brand-400 focus:ring-4 focus:ring-brand-100";

function fieldClass(hasError: boolean, extra = ""): string {
  return `${baseField} ${hasError ? "border-red-400 focus:border-red-500 focus:ring-red-500/20" : ""} ${extra}`;
}

function fieldId(label?: string): string | undefined {
  return label ? label.toLowerCase().trim().replace(/[^a-z0-9]/g, "-") : undefined;
}

function FieldShell({
  label,
  hint,
  required = false,
  error,
  children
}: {
  label?: string;
  hint?: string;
  required?: boolean;
  error?: string;
  children: ReactNode;
}) {
  const id = fieldId(label);
  return (
    <div className="space-y-1.5">
      {label && (
        <label
          htmlFor={id}
          className="block text-[13px] font-semibold text-slate-700"
        >
          {label}
          {required && <span className="text-red-500"> *</span>}
        </label>
      )}
      {children}
      {error ? (
        <p className="text-xs text-red-600">{error}</p>
      ) : hint ? (
        <p className="text-xs text-slate-500">{hint}</p>
      ) : null}
    </div>
  );
}

interface TextFieldProps
  extends BaseFieldProps,
    Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  error?: string;
  required?: boolean;
}

export function TextField({
  label,
  hint,
  error,
  required = false,
  className = "",
  id,
  ...props
}: TextFieldProps) {
  return (
    <FieldShell label={label} hint={hint} required={required} error={error}>
      <input
        id={id ?? fieldId(label)}
        className={fieldClass(Boolean(error), className)}
        required={required}
        {...props}
      />
    </FieldShell>
  );
}

interface TextAreaProps extends BaseFieldProps, TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string;
  required?: boolean;
}

export function TextArea({
  label,
  hint,
  error,
  required = false,
  className = "",
  id,
  ...props
}: TextAreaProps) {
  return (
    <FieldShell label={label} hint={hint} required={required} error={error}>
      <textarea
        id={id ?? fieldId(label)}
        className={`${fieldClass(Boolean(error), className)} min-h-[120px] resize-y`}
        {...props}
      />
    </FieldShell>
  );
}

interface SelectFieldProps extends BaseFieldProps, SelectHTMLAttributes<HTMLSelectElement> {
  error?: string;
  required?: boolean;
  children: ReactNode;
}

export function SelectField({
  label,
  hint,
  error,
  required = false,
  className = "",
  id,
  children,
  ...props
}: SelectFieldProps) {
  return (
    <FieldShell label={label} hint={hint} required={required} error={error}>
      <select
        id={id ?? fieldId(label)}
        className={fieldClass(Boolean(error), className)}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  );
}