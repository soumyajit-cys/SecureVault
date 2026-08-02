import { ToastHost } from "@/components/ui/Toast";
import Sidebar, { IconShield } from "@/components/layout/Sidebar";
import { useAuthStore } from "@/store/authStore";
import { useLocation } from "react-router-dom";

const pageTitles: Record<string, { title: string; tagline: string }> = {
  "/dashboard": {
    title: "Dashboard",
    tagline: "Your secure workspace overview"
  },
  "/file-manager": {
    title: "File Manager",
    tagline: "Encrypt, store and download files"
  },
  "/folder-encryption": {
    title: "Folder Tools",
    tagline: "Encrypt and restore folder archives"
  },
  "/encrypt-text": {
    title: "Encrypt Text",
    tagline: "Protect sensitive text payloads"
  },
  "/decrypt-text": {
    title: "Decrypt Text",
    tagline: "Recover text from ciphertext"
  },
  "/keys": {
    title: "Key Manager",
    tagline: "Generation, rotation and revocation"
  },
  "/audit": {
    title: "Audit Logs",
    tagline: "Immutable security event stream"
  },
  "/admin": {
    title: "Admin Panel",
    tagline: "Users, storage and system management"
  },
  "/profile": {
    title: "Profile",
    tagline: "Your account information"
  },
  "/settings": {
    title: "Settings",
    tagline: "Vault preferences"
  }
};

function PageHeader() {
  const location = useLocation();
  const meta = pageTitles[location.pathname];

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/60 bg-white/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6 lg:px-8">
        <div>
          <h1 className="text-base font-bold tracking-tight text-slate-900">
            {meta?.title ?? "SecureVault"}
          </h1>
          <p className="text-xs text-slate-500">{meta?.tagline}</p>
        </div>
        <TopbarRight />
      </div>
    </header>
  );
}

function TopbarRight() {
  const user = useAuthStore((s) => s.user);
  const roles = user?.roles?.map((r) => r.name).join(", ");

  return (
    <div className="flex items-center gap-3">
      <span className="chip hidden sm:inline-flex">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
        System online
      </span>
      {user && (
        <div className="flex items-center gap-2.5 rounded-xl border border-slate-200/80 bg-white px-3 py-1.5 shadow-sm">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-gradient text-xs font-bold text-white">
            {user.username?.slice(0, 2).toUpperCase()}
          </span>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold leading-tight text-slate-800">
              {user.username}
            </p>
            <p className="text-[11px] leading-tight text-slate-400">{roles}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-surface-soft">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <PageHeader />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl animate-fade-up p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
      <ToastHost />
    </div>
  );
}

export { IconShield };