import type { ReactNode } from "react";

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}

export default function Modal({ open, title, onClose, children, footer }: ModalProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg animate-scale-in rounded-2xl border border-cyber-line bg-surface-elevated shadow-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex items-center justify-between border-b border-cyber-line px-5 py-4">
          <h3 className="text-base font-semibold text-ink">{title}</h3>
          <button
            className="rounded-lg p-1 text-ink-faint transition-colors hover:bg-surface-muted hover:text-ink"
            onClick={onClose}
            aria-label="Close"
          >
            <svg
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </header>
        <div className="max-h-[70vh] overflow-y-auto p-5">{children}</div>
        {footer && (
          <footer className="flex justify-end gap-2 border-t border-cyber-line px-5 py-4">
            {footer}
          </footer>
        )}
      </div>
    </div>
  );
}