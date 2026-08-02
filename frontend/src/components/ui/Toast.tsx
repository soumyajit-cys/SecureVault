import { create } from "zustand";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastState {
  toasts: Toast[];
  push: (type: ToastType, message: string) => void;
  dismiss: (id: number) => void;
}

let nextId = 1;

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (type, message) => {
    const id = nextId++;
    set((s) => ({ toasts: [...s.toasts, { id, type, message }] }));
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
  },
  dismiss: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
}));

export function toastSuccess(message: string) {
  useToastStore.getState().push("success", message);
}
export function toastError(message: string) {
  useToastStore.getState().push("error", message);
}
export function toastInfo(message: string) {
  useToastStore.getState().push("info", message);
}

export function ToastHost() {
  const toasts = useToastStore((s) => s.toasts);
  const dismiss = useToastStore((s) => s.dismiss);

  const tones: Record<ToastType, string> = {
    success:
      "bg-emerald-50 text-emerald-800 ring-emerald-600/30",
    error: "bg-red-50 text-red-800 ring-red-600/30",
    info: "bg-brand-50 text-brand-800 ring-brand-600/30"
  };

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-80 flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          role="status"
          className={`pointer-events-auto flex items-start gap-2 rounded-lg bg-white px-4 py-3 text-sm font-medium shadow-modal ring-1 ${tones[t.type]}`}
          onClick={() => dismiss(t.id)}
        >
          <span aria-hidden="true">
            {t.type === "success" ? "✓" : t.type === "error" ? "✕" : "ℹ"}
          </span>
          <span>{t.message}</span>
        </div>
      ))}
    </div>
  );
}