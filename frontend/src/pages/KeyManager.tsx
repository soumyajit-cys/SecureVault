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
  const [form, setForm] = useState({
    name: "",
    validity_days: ""
  });

  const { data, isLoading } = useQuery({
    queryKey: ["keys", { page, page_size: PAGE_SIZE }],
    queryFn: () => keys.list({ page, page_size: PAGE_SIZE })
  });

  const genMutation = useMutation({
    mutationFn: () =>
      keys.generate({
        name: form.name.trim() || "secret-auto",
        validity_days: form.validity_days ? Number(form.validity_days) : undefined
      }),
    onSuccess: (res) => {
      setPubKey(res.public_key_pem);
      toastSuccess("Key generated");
      queryClient.invalidateQueries({ queryKey: ["keys"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const rotateMutation = useMutation({
    mutationFn: (id: string) => keys.rotate({ current_key_id: id }),
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
      <Card title="Generate new key">
        <div className="grid gap-4 sm:grid-cols-4">
          <TextField
            label="Title"
            placeholder="e.g. primary-2026"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            label="Validity (days)"
            type="number"
            min={1}
            placeholder="90"
            value={form.validity_days}
            onChange={(e) => setForm({ ...form, validity_days: e.target.value })}
          />
          <div className="flex items-end">
            <Button
              className="w-full"
              loading={genMutation.isPending}
              onClick={() => genMutation.mutate()}
              disabled={!form.name.trim()}
            >
              Generate
            </Button>
          </div>
        </div>
        {genMutation.error && (
          <p className="mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
            {extractDetail(genMutation.error)}
          </p>
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
                  <p className="font-medium text-ink">{r.name}</p>
                  <p className="text-xs text-ink-faint">
                    {r.algorithm} · {r.key_size}-bit · {r.fingerprint?.slice(0, 12)}
                  </p>
                </div>
              )
            },
            {
              key: "status",
              header: "Status",
              render: (r: Key) => <Badge color={statusColor[r.status]}>{r.status}</Badge>
            },
            {
              key: "expires",
              header: "Expires",
              render: (r: Key) => (
                <span className="text-xs text-ink-faint">{formatDate(r.expires_at)}</span>
              )
            },
            {
              key: "created",
              header: "Created",
              render: (r: Key) => (
                <span className="text-xs text-ink-faint">{formatDate(r.created_at)}</span>
              )
            },
            {
              key: "actions",
              header: "Actions",
              render: (r: Key) => (
                <div className="flex gap-2">
                  {r.status === "active" && (
                    <Button
                      size="sm"
                      loading={rotateMutation.isPending}
                      onClick={() => rotateMutation.mutate(r.id)}
                    >
                      Rotate
                    </Button>
                  )}
                  {r.status === "active" && (
                    <Button
                      size="sm"
                      variant="danger"
                      loading={revokeMutation.isPending}
                      onClick={() => revokeMutation.mutate(r.id)}
                    >
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
        <p className="mb-3 text-sm text-ink-faint">
          The public part of the new key pair (for verification):
        </p>
        <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg border border-cyber-line bg-cyber p-4 text-xs text-emerald-300">
          {pubKey}
        </pre>
      </Modal>
    </div>
  );
}