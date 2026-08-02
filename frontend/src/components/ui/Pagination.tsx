interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onChange }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));

  if (pages <= 1) return null;

  return (
    <nav className="flex items-center justify-between border-t border-vault-800 px-4 py-3">
      <p className="text-xs text-slate-500">
        Page {page} of {pages} · {total} total
      </p>
      <div className="flex gap-2">
        <button
          className="rounded border border-vault-600 px-3 py-1 text-xs text-slate-300 transition-colors hover:border-neon-cyan/60 disabled:opacity-40"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Prev
        </button>
        <button
          className="rounded border border-vault-600 px-3 py-1 text-xs text-slate-300 transition-colors hover:border-neon-cyan/60 disabled:opacity-40"
          disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Next
        </button>
      </div>
    </nav>
  );
}