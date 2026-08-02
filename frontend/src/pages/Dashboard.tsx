import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import Card from "@/components/ui/Card";
import { FullPageLoader } from "@/components/ui/Spinner";
import { files, keys, profile } from "@/lib/endpoints";
import { useAuthStore } from "@/store/authStore";
import type { Key } from "@/types";
import { formatBytes } from "@/lib/format";

const quickActions = [
  { to: "/encrypt-text", label: "Encrypt Text", color: "border-neon-cyan/50 text-neon-cyan", desc: "Encrypt sensitive text with AES-256-GCM" },
  { to: "/decrypt-text", label: "Decrypt Text", color: "border-neon-purple/50 text-neon-purple", desc: "Recover and verify plaintext" },
  { to: "/file-manager", label: "File Manager", color: "border-neon-green/50 text-neon-green", desc: "Encrypt, store and download files" },
  { to: "/keys", label: "Key Manager", color: "border-neon-amber/50 text-neon-amber", desc: "Generate, rotate and revoke keys" }
];

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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">
          Welcome back, {me.username}
        </h1>
        <p className="text-sm text-slate-500">
          Your vault is ready. All operations are encrypted with AES-256-GCM.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card title="Role">
          <p className="text-2xl font-bold text-neon-cyan">
            {me.roles?.map((r) => r.name).join(", ") || "user"}
          </p>
          <p className="text-xs text-slate-500">Assigned role(s)</p>
        </Card>
        <Card title="Stored files">
          <p className="text-2xl font-bold text-neon-green">
            {fileSummary?.file_count ?? 0}
          </p>
          <p className="text-xs text-slate-500">
            {formatBytes(fileSummary?.original_bytes ?? 0)} original data
          </p>
        </Card>
        <Card title="Active keys">
          <p className="text-2xl font-bold text-neon-amber">{activeKeys.length}</p>
          <p className="text-xs text-slate-500">
            {keyPage?.total ?? 0} keys in rotation
          </p>
        </Card>
        <Card title="Account">
          <p className="text-sm font-semibold text-slate-100">
            {me.is_verified ? "Verified" : "Unverified"}
          </p>
          <p className="text-xs text-slate-500">{me.email}</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {quickActions.map((a) => (
          <Link
            key={a.label}
            to={a.to}
            className={`rounded-lg border bg-vault-900/70 p-6 transition-transform hover:scale-[1.02] ${a.color}`}
          >
            <p className="text-sm font-bold uppercase tracking-wider">{a.label}</p>
            <p className="mt-1 text-xs text-slate-500">
              {a.desc}
            </p>
          </Link>
        ))}
      </div>

      <Card title="Recent keys">
        <div className="space-y-2">
          {(keyPage?.items ?? []).slice(0, 5).map((k) => (
            <div
              key={k.id}
              className="flex items-center justify-between rounded border border-vault-700 px-3 py-2 text-sm"
            >
              <div>
                <p className="font-medium text-slate-200">{k.name}</p>
                <p className="text-xs text-slate-500">
                  {k.algorithm}-{k.key_size} · {k.fingerprint?.slice(0, 16)}
                </p>
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-xs ${
                  k.status === "active"
                    ? "bg-neon-green/15 text-neon-green"
                    : k.status === "revoked"
                      ? "bg-neon-red/15 text-neon-red"
                      : "bg-neon-amber/15 text-neon-amber"
                }`}
              >
                {k.status}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}