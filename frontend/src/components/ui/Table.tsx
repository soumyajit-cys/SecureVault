import type { ReactNode } from "react";

interface TableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
}

interface TableProps<T> {
  columns: TableColumn<T>[];
  rows: T[];
  loading?: boolean;
  emptyMessage?: string;
}

export default function Table<T>({
  columns,
  rows,
  loading = false,
  emptyMessage = "No records found."
}: TableProps<T>) {
  if (loading) {
    return (
      <div className="flex justify-center py-10">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-cyber-line border-t-accent" />
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <div className="py-12 text-center">
        <div className="mx-auto mb-3 inline-flex h-11 w-11 items-center justify-center rounded-full border border-cyber-line bg-surface-muted/60 text-ink-faint">
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" />
          </svg>
        </div>
        <p className="text-sm font-medium text-ink-faint">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-cyber-line text-xs font-semibold uppercase tracking-wider text-ink-faint">
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-3">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-cyber-line">
          {rows.map((row, i) => (
            <tr
              key={i}
              className="text-ink-soft transition-colors hover:bg-accent/5 hover:text-ink"
            >
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-3">
                  {col.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}