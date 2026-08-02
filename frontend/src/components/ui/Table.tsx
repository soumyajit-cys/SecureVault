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
      <div className="flex justify-center py-10 text-sm text-slate-400">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-vault-500 border-t-neon-cyan" />
      </div>
    );
  }

  if (rows.length === 0) {
    return <p className="py-10 text-center text-sm text-slate-500">{emptyMessage}</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-vault-700 text-xs uppercase tracking-wider text-slate-400">
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-3 font-medium">
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-vault-800">
          {rows.map((row, i) => (
            <tr key={i} className="text-slate-200 transition-colors hover:bg-vault-800/50">
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