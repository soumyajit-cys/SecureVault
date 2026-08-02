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

  const styles: Record<ToastType, string> = {
    success: "border-neon-green/60 text-neon-green",
    error: "border-neon-red/60 text-neon-red",
    info: "border-neon-cyan/60 text-neon-cyan"
  };

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-80 flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto rounded-md border bg-vault-900/95 px-4 py-3 text-sm shadow-lg backdrop-blur ${styles[t.type]}`}
          onClick={() => dismiss(t.id)}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}