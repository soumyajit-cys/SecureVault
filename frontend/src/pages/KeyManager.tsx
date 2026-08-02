import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import { TextField } from "@/components/ui/Field";
import Table from "@/components/ui/Table";
import Pagination from "@/components/ui/Pagination";
import { extractDetail } from "@/lib/api";
import { keys } from "@/lib/endpoints";
import { toastError, toastSuccess } from "@/components/ui/Toast";
import { formatDate } from "@/lib/format";
import type { Key } from "@/types";

const PAGE_SIZE = 10;

const statusColor: Record<Key["status"], "green" | "red" | "amber"> = {
  active: "green",
  revoked: "red",
  expired: "amber"
};

export default function KeyManager() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pubKey, setPubKey] = useState<string | null>(null);
  const [form, setForm] = useState({ name: "", algorithm: "AES-256-GCM", key_size: 256, expires_in_days: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["keys", { page, page_size: PAGE_SIZE }],
    queryFn: () => keys.list({ page, page_size: PAGE_SIZE })
  });

  const genMutation = useMutation({
    mutationFn: () =>
      keys.generate({
        name: form.name.trim() || "auto-generated",
        algorithm: form.algorithm,
        key_size: form.key_size,
        expires_in_days: form.expires_in_days ? Number(form.expires_in_days) : undefined
      }),
    onSuccess: (res) => {
      setPubKey(res.public_key_pem);
      toastSuccess("Key generated");
      queryClient.invalidateQueries({ queryKey: ["keys"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const rotateMutation = useMutation({
    mutationFn: (id: string) => keys.rotate(id),
    onSuccess: () => {
      toastSuccess("Key rotated");
      queryClient.invalidateQueries({ queryKey: ["keys"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => keys.revoke(id),
    onSuccess: () => {
      toastSuccess("Key revoked");
      queryClient.invalidateQueries({ queryKey: ["keys"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Key Manager</h1>
        <p className="text-sm text-slate-500">
          Keys are generated server-side and their private material is never exposed.
        </p>
      </div>

      <Card title="Generate new key">
        <div className="grid gap-4 sm:grid-cols-4">
          <TextField
            label="Name"
            placeholder="primary-2026"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            label="Expires in (days)"
            type="number"
            min={1}
            placeholder="365"
            value={form.expires_in_days}
            onChange={(e) => setForm({ ...form, expires_in_days: e.target.value })}
          />
          <div className="space-y-1">
            <span className="mb-1 block text-xs font-medium uppercase tracking-wider text-slate-400">
              Algorithm
            </span>
            <select
              className="w-full rounded border border-vault-600 bg-vault-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-neon-cyan/70"
              value={form.algorithm}
              onChange={(e) =>
                setForm({
                  ...form,
                  algorithm: e.target.value,
                  key_size: e.target.value === "AES-128-GCM" ? 128 : 256
                })
              }
            >
              <option>AES-256-GCM</option>
              <option>AES-128-GCM</option>
              <option>ChaCha20</option>
            </select>
          </div>
          <div className="flex items-end">
            <Button
              className="w-full"
              loading={genMutation.isPending}
              onClick={() => genMutation.mutate()}
            >
              Generate
            </Button>
          </div>
        </div>
        {revokeMutation.error && (
          <p className="mt-3 text-sm text-neon-red">{extractDetail(revokeMutation.error)}</p>
        )}
      </Card>

      <Card title="Manage keys">
        <Table
          columns={[
            {
              key: "name",
              header: "Key",
              render: (r: Key) => (
                <div>
                  <p className="font-medium text-slate-100">{r.name}</p>
                  <p className="text-xs text-slate-500">
                    {r.algorithm} · {r.key_size}-bit · {r.fingerprint?.slice(0, 12)}
                  </p>
                </div>
              )
            },
            {
              key: "status",
              header: "Status",
              render: (r: Key) => <Badge color={statusColor(r.status)}>{r.status}</Badge>
            },
            {
              key: "expires",
              header: "Expires",
              render: (r: Key) => (
                <span className="text-xs text-slate-400">{formatDate(r.expires_at)}</span>
              )
            },
            {
              key: "created",
              header: "Created",
              render: (r: Key) => (
                <span className="text-xs text-slate-400">{formatDate(r.created_at)}</span>
              )
            },
            {
              key: "actions",
              header: "Actions",
              render: (r: Key) => (
                <div className="flex gap-2">
                  {r.status === "active" && (
                    <Button size="sm" onClick={() => rotateMutation.mutate(r.id)}>
                      Rotate
                    </Button>
                  )}
                  {r.status === "active" && (
                    <Button size="sm" variant="danger" onClick={() => revokeMutation.mutate(r.id)}>
                      Revoke
                    </Button>
                  )}
                </div>
              )
            }
          ]}
          rows={data?.items ?? []}
          loading={isLoading}
          emptyMessage="No keys yet — generate your first one above."
        />
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={data?.total ?? 0}
          onChange={setPage}
        />
      </Card>

      <Modal
        open={pubKey !== null}
        title="Key generated"
        onClose={() => setPubKey(null)}
      >
        <p className="mb-3 text-sm text-slate-400">
          The wrapped key is stored securely. Below is the public RSA signing key for
          verification — store it if needed.
        </p>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg bg-vault-950 p-4 text-xs text-neon-green">
          {pubKey}
        </pre>
      </Modal>
    </div>
  );
}