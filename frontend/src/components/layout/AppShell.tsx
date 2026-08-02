import { ToastHost } from "@/components/ui/Toast";
import Sidebar from "@/components/layout/Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl p-6 lg:p-8">{children}</div>
      </main>
      <ToastHost />
    </div>
  );
}