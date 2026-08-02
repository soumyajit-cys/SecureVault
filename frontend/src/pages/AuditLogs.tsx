import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import Pagination from "@/components/ui/Pagination";
import Table from "@/components/ui/Table";
import { SelectField } from "@/components/ui/Field";
import { audit } from "@/lib/endpoints";
import { formatDate } from "@/lib/format";
import type { AuditLog } from "@/types";

const PAGE_SIZE = 15;

const actionColors: Record<string, "green" | "red" | "amber" | "cyan" | "purple" | "slate"> =
  {
    user_registered: "cyan",
    user_logged_in: "green",
    user_logged_out: "slate",
    key_generated: "cyan",
    key_rotated: "amber",
    key_revoked: "red",
    key_activated: "green",
    file_uploaded: "green",
    file_downloaded: "cyan",
    file_deleted: "red",
    folder_encrypted: "purple",
    folder_restored: "green"
  };

export default function AuditLogs() {
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["audit", { page, page_size: 10, action }],
    queryFn: () => audit.list({ page, page_size: 10, action: action || undefined })
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
          <p className="text-sm text-slate-500">
            Every security-relevant action is immutably logged.
          </p>
        </div>
        <SelectField
          value={action}
          onChange={(e) => {
            setAction(e.target.value);
            setPage(1);
          }}
          className="w-56"
        >
          <option value="">All actions</option>
          {Object.keys(actionColor).map((a) => (
            <option key={a} value={a}>
              {a.replace(/_/g, " ")}
            </option>
          ))}
        </SelectField>
      </div>

      <Card title="Event stream">
        <Table
          columns={[
            {
              key: "action",
              header: "Action",
              render: (r: AuditLog) => (
                <Badge color={actionColor[r.action] ?? "slate"}>{r.action}</Badge>
              )
            },
            {
              key: "resource",
              header: "Resource",
              render: (r: AuditLog) => (
                <div className="text-xs text-slate-400">
                  {r.resource_type ?? "—"}
                  {r.resource_id ? ` · ${r.resource_id.slice(0, 8)}…` : ""}
                </div>
              )
            },
            {
              key: "details",
              header: "Details",
              render: (r: AuditLog) => (
                <span className="max-w-md truncate text-xs text-slate-400">
                  {r.details ?? "—"}
                </span>
              )
            },
            {
              key: "created",
              header: "Timestamp",
              render: (r: AuditLog) => (
                <span className="text-xs text-slate-400">{formatDate(r.created_at)}</span>
              )
            }
          ]}
          rows={data?.items ?? []}
          loading={isLoading}
          emptyMessage="No audit events yet."
        />
        <Pagination
          page={page}
          pageSize={10}
          total={data?.total ?? 0}
          onChange={setPage}
        />
      </Card>
    </div>
  );
}