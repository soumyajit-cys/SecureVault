import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Modal from "@/components/ui/Modal";
import Table from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import Pagination from "@/components/ui/Pagination";
import { SelectField } from "@/components/ui/Field";
import { extractDetail } from "@/lib/api";
import { folders, keys } from "@/lib/endpoints";
import { toastError, toastSuccess } from "@/components/ui/Toast";
import { formatBytes, formatDate } from "@/lib/format";
import type { StoredFile } from "@/types";

const PAGE_SIZE = 10;

interface RestoreInfo {
  restoredPath: string;
  files: number;
}

export default function FolderEncryption() {
  const queryClient = useQueryClient();
  const zipInput = useRef<HTMLInputElement>(null);
  const [page, setPage] = useState(1);
  const [keyId, setKeyId] = useState("");
  const [restoreInfo, setRestoreInfo] = useState<RestoreInfo | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["folders", { page, page_size: PAGE_SIZE }],
    queryFn: () => folders.list({ page, page_size: PAGE_SIZE })
  });

  const { data: keyPage } = useQuery({
    queryKey: ["keys", { page: 1, page_size: 100 }],
    queryFn: () => keys.list({ page: 1, page_size: 100 })
  });

  const uploadMutation = useMutation({
    mutationFn: (zip: File) => folders.upload(zip, keyId || undefined),
    onSuccess: () => {
      toastSuccess("Folder archive encrypted and stored");
      if (zipInput.current) zipInput.current.value = "";
      queryClient.invalidateQueries({ queryKey: ["folders"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const restoreMutation = useMutation({
    mutationFn: (id: string) => folders.restore(id),
    onSuccess: (res) => {
      setRestoreInfo({
        restoredPath: res.restored_path,
        files: res.restored_files
      });
      toastSuccess("Folder restored");
    },
    onError: (err) => toastError(extractDetail(err))
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Folder Tools</h1>
          <p className="mt-1 text-sm text-slate-500">
            Encrypt an entire folder (zip + AES-256-GCM) or restore a stored archive.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <SelectField
            value={keyId}
            onChange={(e) => setKeyId(e.target.value)}
            className="!w-44"
          >
            <option value="">Auto (active key)</option>
            {(keyPage?.items ?? [])
              .filter((k) => k.status === "active")
              .map((k) => (
                <option key={k.id} value={k.id}>
                  {k.name}
                </option>
              ))}
          </SelectField>
          <input
            ref={zipInput}
            type="file"
            accept=".zip,application/zip"
            hidden
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) uploadMutation.mutate(f);
            }}
          />
          <Button
            loading={uploadMutation.isPending}
            onClick={() => zipInput.current?.click()}
          >
            {uploadMutation.isPending ? "Encrypting…" : "Encrypt folder (.zip)"}
          </Button>
        </div>
      </div>

      <Card title="Stored folder archives">
        <Table
          columns={[
            {
              key: "name",
              header: "Archive",
              render: (r: StoredFile) => (
                <span className="font-medium text-slate-900">{r.original_filename}</span>
              )
            },
            {
              key: "files",
              header: "Files",
              render: (r: StoredFile) => (
                <span className="text-xs text-slate-500">{r.folder_file_count}</span>
              )
            },
            {
              key: "size",
              header: "Size",
              render: (r: StoredFile) => (
                <span className="text-xs text-slate-500">
                  {formatBytes(r.original_size)}
                </span>
              )
            },
            {
              key: "status",
              header: "Status",
              render: (r: StoredFile) => (
                <Badge color={r.status === "active" ? "green" : "slate"}>
                  {r.status}
                </Badge>
              )
            },
            {
              key: "created",
              header: "Encrypted",
              render: (r: StoredFile) => (
                <span className="text-xs text-slate-500">{formatDate(r.created_at)}</span>
              )
            },
            {
              key: "actions",
              header: "Actions",
              render: (r: StoredFile) => (
                <Button
                  variant="success"
                  size="sm"
                  loading={restoreMutation.isPending}
                  onClick={() => restoreMutation.mutate(r.id)}
                >
                  Restore
                </Button>
              )
            }
          ]}
          rows={data?.items ?? []}
          loading={isLoading}
          emptyMessage="No folder archives yet."
        />
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={data?.total ?? 0}
          onChange={setPage}
        />
      </Card>

      <Modal
        open={restoreInfo !== null}
        title="Folder restored"
        onClose={() => setRestoreInfo(null)}
      >
        <p className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          The archive was decrypted and expanded successfully.
        </p>
        <dl className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Paths</dt>
            <dd className="font-mono text-slate-800">{restoreInfo?.restoredPath}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">Files</dt>
            <dd className="font-mono text-slate-800">{restoreInfo?.files}</dd>
          </div>
        </dl>
      </Modal>
    </div>
  );
}