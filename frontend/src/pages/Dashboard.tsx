import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import { FullPageLoader } from "@/components/ui/Spinner";
import { files, keys, profile } from "@/lib/endpoints";
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
    to: "/decrypt-text",
    label: "Decrypt Text",
    icon: (
      <path d="M12 21a5 5 0 0 0 5-5v-2M7 21a7 7 0 0 0 7-7V8a5 5 0 0 0-10 0v8a9 9 0 0 0 9 10z" />
    ),
    desc: "Verify integrity and recover plaintext"
  },
  {
    to: "/file-manager",
    label: "File Manager",
    icon: <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />,
    desc: "Encrypt, store and download files at rest"
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

  if (loadingFiles || loadingKeys || !me) {
    return <FullPageLoader />;
  }

  const activeKeys = (keyPage?.items ?? []).filter((k: Key) => k.status === "active");

  const stats = [
    {
      label: "Assigned role",
      value: me.roles?.map((r) => r.name).join(", ") || "user",
      accent: "text-brand-600"
    },
    {
      label: "Stored files",
      value: String(fileSummary?.file_count ?? 0),
      sub: `${formatBytes(fileSummary?.original_bytes ?? 0)} original data`,
      accent: "text-slate-900"
    },
    {
      label: "Active keys",
      value: String(activeKeys.length),
      sub: `${keyPage?.total ?? 0} keys in rotation`,
      accent: "text-slate-900"
    }
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Welcome back, {me.username}
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Your vault is ready. All operations use AES-256-GCM authentication.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <Card key={s.label}>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
              {s.label}
            </p>
            <p className={`mt-2 text-2xl font-bold tracking-tight ${s.accent}`}>
              {s.value}
            </p>
            {s.sub && <p className="mt-1 text-xs text-slate-500">{s.sub}</p>}
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {quickActions.map((a) => (
          <Link
            key={a.label}
            to={a.to}
            className="group flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-card transition-all hover:border-brand-200 hover:shadow-md"
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 transition-colors group-hover:bg-brand-600 group-hover:text-white">
              <svg
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {a.icon}
              </svg>
            </span>
            <div>
              <p className="font-semibold text-slate-900">{a.label}</p>
              <p className="mt-0.5 text-sm text-slate-500">{a.desc}</p>
            </div>
          </Link>
        ))}
      </div>

      <Card
        title="Recent keys"
        action={
          <Link to="/keys" className="text-xs font-medium text-brand-600 hover:text-brand-700">
            View all
          </Link>
        }
      >
        <div className="divide-y divide-slate-100">
          {(keyPage?.items ?? []).slice(0, 5).map((k) => (
            <div key={k.id} className="flex items-center justify-between py-2.5">
              <div>
                <p className="text-sm font-medium text-slate-900">{k.name}</p>
                <p className="text-xs text-slate-500">
                  {k.algorithm}-{k.key_size} · {k.fingerprint?.slice(0, 16)}
                </p>
              </div>
              <Badge color={keyBadge[k.status]}>{k.status}</Badge>
            </div>
          ))}
          {(keyPage?.items ?? []).length === 0 && (
            <p className="py-4 text-sm text-slate-500">
              No keys yet — generate one in the Key Manager.
            </p>
          )}
        </div>
      </Card>
    </div>
  );
}