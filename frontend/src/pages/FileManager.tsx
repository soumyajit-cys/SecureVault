import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import Table from "@/components/ui/Table";
import Badge from "@/components/ui/Badge";
import Pagination from "@/components/ui/Pagination";
import Modal from "@/components/ui/Modal";
import { SelectField } from "@/components/ui/Field";import { extractDetail } from "@/lib/api";
import { files, keys } from "@/lib/endpoints";
import { toastError, toastSuccess } from "@/components/ui/Toast";
import { formatBytes, formatDate } from "@/lib/format";
import type { StoredFile } from "@/types";

export default function FileManager() {
  const queryClient = useQueryClient();
  const fileInput = useRef<HTMLInputElement>(null);

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [keyId, setKeyId] = useState("");
  const [preview, setPreview] = useState<StoredFile | null>(null);

  const pageSize = 10;

  const { data, isLoading } = useQuery({
    queryKey: ["files", { page, page_size: pageSize, search }],
    queryFn: () =>
      files.list({ page, page_size: pageSize, search: search || undefined })
  });

  const { data: keyPage } = useQuery({
    queryKey: ["keys", { page: 1, page_size: 100 }],
    queryFn: () => keys.list({ page: 1, page_size: 100 })
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => files.upload(file),
    onSuccess: () => {
      toastSuccess("File encrypted and stored");
      queryClient.invalidateQueries({ queryKey: ["files"] });
      if (fileInput.current) fileInput.current.value = "";
    },
    onError: (err) => toastError(extractDetail(err))
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => files.delete(id),
    onSuccess: () => {
      toastSuccess("File marked for deletion");
      queryClient.invalidateQueries({ queryKey: ["files"] });
    },
    onError: (err) => toastError(extractDetail(err))
  });

  function handleDownload(item: StoredFile) {
    files
      .download(item.id)
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = item.original_filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      })
      .catch((err) => toastError(extractDetail(err)));
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-end gap-4">
        <input
          ref={fileInput}
          type="file"
          hidden
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) uploadMutation.mutate(f);
          }}
        />
        <Button
          loading={uploadMutation.isPending}
          onClick={() => fileInput.current?.click()}
        >
          {uploadMutation.isPending ? "Encrypting…" : "Upload file"}
        </Button>
      </div>

      <Card
        title="Encrypted files"
        action={
          <div className="flex items-center gap-3">
            <input
              className="w-56 rounded-lg border border-cyber-line bg-surface-elevated px-3 py-1.5 text-sm text-ink placeholder:text-ink-faint outline-none transition-colors focus:border-accent/50 focus:ring-2 focus:ring-accent/20"
              placeholder="Search by filename…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
            />
          </div>
        }
      >
        <Table
          columns={[
            {
              key: "name",
              header: "Filename",
              render: (r: StoredFile) => (
                <button
                  className="text-left font-medium text-brand-600 hover:text-brand-700 hover:underline"
                  onClick={() => setPreview(r)}
                >
                  {r.original_filename}
                </button>
              )
            },
            {
              key: "size",
              header: "Size",
              render: (r: StoredFile) => (
                <span className="text-xs text-ink-faint">
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
              header: "Created",
              render: (r: StoredFile) => (
                <span className="text-xs text-ink-faint">{formatDate(r.created_at)}</span>
              )
            },
            {
              key: "actions",
              header: "Actions",
              render: (r: StoredFile) => (
                <div className="flex gap-2">
                  <Button variant="success" size="sm" onClick={() => handleDownload(r)}>
                    Download
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => deleteMutation.mutate(r.id)}>
                    Delete
                  </Button>
                </div>
              )
            }
          ]}
          rows={data?.items ?? []}
          loading={isLoading}
          emptyMessage="No files stored yet."
        />
        <Pagination
          page={page}
          pageSize={pageSize}
          total={data?.total ?? 0}
          onChange={setPage}
        />
      </Card>

      <Modal
        open={preview !== null}
        title="File details"
        onClose={() => setPreview(null)}
      >
        {preview && (
          <dl className="space-y-2 text-sm">
            {[
              ["Filename", preview.original_filename],
              ["MIME type", preview.mime_type],
              ["Original size", formatBytes(preview.original_size)],
              ["Encrypted size", formatBytes(preview.encrypted_size)],
              ["SHA-256", preview.sha256],
              ["Created", formatDate(preview.created_at)]
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4">
                <dt className="text-ink-faint">{k}</dt>
                <dd className="max-w-xs truncate text-right font-mono text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        )}
      </Modal>
    </div>
  );
}