import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { FullPageLoader } from "@/components/ui/Spinner";
import { admin, audit, files, keys, profile } from "@/lib/endpoints";
import { useAuthStore } from "@/store/authStore";
import type { Key } from "@/types";
import { formatBytes } from "@/lib/format";

const quickActions = [
  {
    to: "/encrypt-text",
    label: "Encrypt Text",
    icon: (
      <path d="M12 3v3m0 0a6 6 0 0 1 6 6v6a6 6 0 0 1-6 6 6 6 0 0 1-6-6v-6a6 6 0 0 1 6-6zm0 0a6 6 0 0 1 6 6m-6 6a6 6 0 0 1 6 6m-6-6 3 4" />
    ),
    desc: "AES-256-GCM authenticated encryption for sensitive text"
  },
  {
    to: "/file-manager",
    label: "File Manager",
    icon: <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />,
    desc: "Encrypt, store and download files at rest"
  },
  {
    to: "/folder-encryption",
    label: "Folder Tools",
    icon: (
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />
    ),
    desc: "Seal entire directories as single archives"
  },
  {
    to: "/keys",
    label: "Key Manager",
    icon: (
      <path d="M21 2l-5 5m-2 2l-3-3-6 6a4 4 0 0 0 6 6l6-6-3-3m-3 0l3 3" />
    ),
    desc: "Generate, rotate and revoke encryption keys"
  }
];

const keyBadge: Record<Key["status"], "green" | "red" | "amber"> = {
  active: "green",
  revoked: "red",
  expired: "amber"
};

export default function Dashboard() {
  const setUser = useAuthStore((s) => s.setUser);

  const { data: me } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: async () => {
      const r = await profile.me();
      setUser(r);
      return r;
    }
  });

  const { data: fileSummary, isLoading: loadingFiles } = useQuery({
    queryKey: ["files", "summary"],
    queryFn: () => files.summary()
  });

  const { data: keyPage, isLoading: loadingKeys } = useQuery({
    queryKey: ["keys", { page: 1, page_size: 5 }],
    queryFn: () => keys.list({ page: 1, page_size: 5 })
  });

  const isAdmin = me?.roles?.some(
    (r) => r.name.toLowerCase() === "admin"
  );

  const { data: storageUsage } = useQuery({
    queryKey: ["admin", "storage"],
    queryFn: () => admin.usage(),
    enabled: Boolean(isAdmin)
  });

  const { data: activityPage, isLoading: loadingActivity } = useQuery({
    queryKey: ["audit", { page: 1, page_size: 6 }],
    queryFn: () => audit.list({ page: 1, page_size: 6 }),
    enabled: Boolean(me)
  });

  if (loadingFiles || loadingKeys || !me) {
    return <FullPageLoader />;
  }

  const activeKeys = (keyPage?.items ?? []).filter((k: Key) => k.status === "active");
  const storagePercent = storageUsage
    ? Math.min(100, Math.round((storageUsage.storage_bytes / Math.max(1, storageUsage.storage_bytes + 1_000_000_000)) * 100))
    : null;

  const stats = [
    {
      label: "Stored items",
      value: String(fileSummary?.file_count ?? 0),
      sub: `${fileSummary?.folder_count ?? 0} folders sealed`,
      icon: <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" />,
      accent: "from-brand-500 to-brand-700"
    },
    {
      label: "Sealed capacity",
      value: formatBytes(fileSummary?.encrypted_bytes ?? 0),
      sub: `${formatBytes(fileSummary?.original_bytes ?? 0)} original data`,
      icon: <path d="M12 2v20M2 12h20" />,
      accent: "from-cyan-500 to-blue-700"
    },
    {
      label: "Active keys",
      value: String(activeKeys.length),
      sub: `${keyPage?.total ?? 0} keys in rotation`,
      icon: <path d="M21 2l-5 5m-2 2l-3-3-6 6a4 4 0 0 0 6 6l6-6-3-3m-3 0l3 3" />,
      accent: "from-emerald-500 to-teal-700"
    }
  ];

  return (
    <div className="space-y-6 animate-fade-up">
      {/* Welcome strip */}
      <div className="rounded-xl border border-cyber-line bg-surface-elevated p-6 shadow-card lg:p-8">
        <div className="flex flex-col items-start justify-between gap-6 lg:flex-row lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
              Welcome back
            </p>
            <h1 className="mt-1 text-2xl font-extrabold tracking-tight text-ink lg:text-3xl">
              {me.username}
            </h1>
            <p className="mt-2 max-w-lg text-sm text-ink-soft">
              Your vault is sealed and online. All work is authenticated
              with AES-256-GCM before it touches storage.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Badge color="green">
              <span className="flex items-center gap-1.5">
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                </span>
                System online
              </span>
            </Badge>
            <span className="inline-flex items-center rounded-md border border-cyber-line bg-surface-muted px-2.5 py-1 font-mono text-xs font-medium text-ink-soft">
              {me.roles?.map((r) => r.name).join(", ") || "User"}
            </span>
          </div>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        {stats.map((s) => (
          <Card
            key={s.label}
            className="surface-hover"
          >
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
                {s.label}
              </p>
              <span className={`flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br ${s.accent} text-white`}>
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {s.icon}
                </svg>
              </span>
            </div>
            <p className="mt-3 font-mono text-3xl font-extrabold tracking-tight text-ink">
              {s.value}
            </p>
            <p className="mt-1 text-xs text-ink-faint">{s.sub}</p>
          </Card>
        ))}
      </div>

      {/* Quick actions + activity */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <Card
            title="Quick actions"
            subtitle="Jump into the vault"
          >
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {quickActions.map((a) => (
                <Link
                  key={a.label}
                  to={a.to}
                  className="group flex items-start gap-3.5 rounded-lg border border-cyber-line bg-surface-elevated p-4 shadow-sm transition-all duration-200 hover:border-brand-300 hover:shadow-card-hover"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-brand-100 bg-brand-50 text-brand-600 transition-colors duration-200 group-hover:bg-brand-gradient group-hover:text-white">
                    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      {a.icon}
                    </svg>
                  </span>
                  <div>
                    <p className="font-semibold text-ink">{a.label}</p>
                    <p className="mt-0.5 text-xs leading-relaxed text-ink-faint">{a.desc}</p>
                  </div>
                </Link>
              ))}
            </div>
          </Card>
        </div>

        <Card
          title="Activity feed"
          subtitle="Latest security events"
          action={
            <Link to="/audit" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
              View all
            </Link>
          }
        >
          <div className="space-y-1">
            {loadingActivity ? (
              <div className="flex justify-center py-8">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-cyber-line border-t-accent" />
              </div>
            ) : (activityPage?.items ?? []).length === 0 ? (
              <p className="py-6 text-center text-sm text-ink-faint">No activity yet.</p>
            ) : (
              (activityPage?.items ?? []).slice(0, 6).map((log) => (
                <div key={log.id} className="flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-surface-muted">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-brand-100 bg-brand-50 text-brand-600">
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M4 19V9m5 10V5m5 14v-7m5 7V3" />
                    </svg>
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-ink">{log.action}</p>
                    <p className="truncate text-xs text-ink-faint">
                      {log.resource_type ?? "system"} · {relativeTime(log.created_at)}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Recent keys + resource usage */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
        <Card
          title="Recent keys"
          className="lg:col-span-2"
          action={
            <Link to="/keys" className="text-xs font-semibold text-brand-600 hover:text-brand-700">
              View all
            </Link>
          }
        >
          <div className="divide-y divide-cyber-line">
            {(keyPage?.items ?? []).slice(0, 5).map((k) => (
              <div key={k.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-ink">{k.name}</p>
                  <p className="font-mono text-xs text-ink-faint">
                    {k.algorithm}-{k.key_size} · {k.fingerprint?.slice(0, 16)}
                  </p>
                </div>
                <Badge color={keyBadge[k.status]}>{k.status}</Badge>
              </div>
            ))}
            {(keyPage?.items ?? []).length === 0 && (
              <p className="py-6 text-sm text-ink-faint">
                No keys yet — generate one in the Key Manager.
              </p>
            )}
          </div>
        </Card>

        {isAdmin && storageUsage && (
          <Card
            title="Resource usage"
            subtitle="Vault storage overview"
            gradient
          >
            <div className="space-y-5">
              <div>
                <div className="flex items-end justify-between">
                  <p className="text-sm font-semibold text-white">Encrypted storage</p>
                  <p className="font-mono text-lg font-bold text-white">
                    {formatBytes(storageUsage.storage_bytes)}
                  </p>
                </div>
                <div className="mt-3 h-2.5 overflow-hidden rounded-full bg-white/25">
                  <div
                    className="h-full rounded-full bg-white transition-all duration-700"
                    style={{ width: `${storagePercent}%` }}
                  />
                </div>
                <p className="mt-2 text-xs text-white/80">
                  {storageUsage.stored_file_count} stored files
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-white/10 p-3">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-white/70">
                    File records
                  </p>
                  <p className="mt-1 font-mono text-xl font-bold text-white">
                    {storageUsage.stored_file_count}
                  </p>
                </div>
                <div className="rounded-lg bg-white/10 p-3">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-white/70">
                    Temp files
                  </p>
                  <p className="mt-1 font-mono text-xl font-bold text-white">
                    {storageUsage.temp_file_count}
                  </p>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const diffMs = Date.now() - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export { relativeTime };
