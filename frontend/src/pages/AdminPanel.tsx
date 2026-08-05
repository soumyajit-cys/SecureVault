import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import Pagination from "@/components/ui/Pagination";
import Table from "@/components/ui/Table";
import { extractDetail } from "@/lib/api";
import { admin, files } from "@/lib/endpoints";
import { toastError, toastSuccess } from "@/components/ui/Toast";
import { formatBytes } from "@/lib/format";
import type { User } from "@/types";

const PAGE_SIZE = 10;

export default function AdminPanel() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [gcResult, setGcResult] = useState<string | null>(null);

  const { data: summary } = useQuery({
    queryKey: ["files", "summary"],
    queryFn: () => files.summary()
  });

  const { data: usage } = useQuery({
    queryKey: ["admin", "usage"],
    queryFn: () => admin.usage()
  });

  const { data: users, isLoading } = useQuery({
    queryKey: ["admin", "users", { page, page_size: PAGE_SIZE }],
    queryFn: () => admin.users({ page, page_size: PAGE_SIZE })
  });

  const gcMutation = useMutation({
    mutationFn: () => admin.gc(),
    onSuccess: (res) => {
      setGcResult(JSON.stringify(res, null, 2));
      toastSuccess("Garbage collection completed");
      queryClient.invalidateQueries({ queryKey: ["admin"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const userAction = useMutation({
    mutationFn: ({ id, deactivate }: { id: string; deactivate: boolean }) =>
      deactivate ? admin.deactivateUser(id) : admin.activateUser(id),
    onSuccess: () => {
      toastSuccess("User status updated");
      queryClient.invalidateQueries({ queryKey: ["admin", "users"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const stats = [
    {
      label: "Storage used",
      value: formatBytes(usage?.storage_bytes ?? 0),
      sub: `${usage?.stored_file_count ?? 0} stored · ${usage?.temp_file_count ?? 0} temp`,
      tone: "text-brand-600"
    },
    {
      label: "Files vs folders",
      value: String(summary?.file_count ?? 0),
      sub: `files · ${summary?.folder_count ?? 0} folder archives`,
      tone: "text-brand-700"
    },
    {
      label: "Deduplication saving",
      value: formatBytes(
        Math.max(0, (summary?.original_bytes ?? 0) - (summary?.encrypted_bytes ?? 0))
      ),
      sub: `original ${formatBytes(summary?.original_bytes ?? 0)}`,
      tone: "text-ink"
    }
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <Card key={s.label}>
            <p className="text-xs font-medium uppercase tracking-wide text-ink-faint">
              {s.label}
            </p>
            <p className={`mt-2 text-2xl font-bold tracking-tight ${s.tone}`}>{s.value}</p>
            <p className="mt-1 text-xs text-ink-faint">{s.sub}</p>
          </Card>
        ))}
      </div>

      <Card
        title="Garbage collection"
        action={
          <Button variant="danger" loading={gcMutation.isPending} onClick={() => gcMutation.mutate()}>
            Run GC now
          </Button>
        }
      >
        <p className="text-sm text-ink-faint">
          Purge soft-deleted files, orphaned container blobs, missing records and stray
          temporary files.
        </p>
        <Modal open={gcResult !== null} title="GC report" onClose={() => setGcResult(null)}>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-lg border border-cyber-line bg-cyber p-4 text-xs text-emerald-300">
            {gcResult}
          </pre>
        </Modal>
      </Card>

      <Card title="Users">
        <Table
          columns={[
            {
              key: "user",
              header: "User",
              render: (r: User) => (
                <div>
                  <p className="font-medium text-ink">{r.username}</p>
                  <p className="text-xs text-ink-faint">{r.email}</p>
                </div>
              )
            },
            {
              key: "roles",
              header: "Roles",
              render: (r: User) => (
                <div className="flex flex-wrap gap-1">
                  {r.roles.map((role) => (
                    <Badge key={role.id} color="indigo">
                      {role.name}
                    </Badge>
                  ))}
                </div>
              )
            },
            {
              key: "status",
              header: "Status",
              render: (r: User) => (
                <Badge color={r.is_active ? "green" : "red"}>
                  {r.is_active ? "Active" : "Disabled"}
                </Badge>
              )
            },
            {
              key: "verified",
              header: "Verified",
              render: (r: User) => (
                <Badge color={r.is_verified ? "green" : "slate"}>
                  {r.is_verified ? "Yes" : "No"}
                </Badge>
              )
            },
            {
              key: "actions",
              header: "Actions",
              render: (r: User) => (
                <Button
                  size="sm"
                  variant={r.is_active ? "danger" : "success"}
                  loading={userAction.isPending}
                  onClick={() => userAction.mutate({ id: r.id, deactivate: r.is_active })}
                >
                  {r.is_active ? "Deactivate" : "Activate"}
                </Button>
              )
            }
          ]}
          rows={users?.items ?? []}
          loading={isLoading}
          emptyMessage="No users found."
        />
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={users?.total ?? 0}
          onChange={setPage}
        />
      </Card>
    </div>
  );
}