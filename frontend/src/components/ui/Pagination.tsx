interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onChange: (page: number) => void;
}

export default function Pagination({ page, pageSize, total, onChange }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));

  if (pages <= 1) return null;

  const btn =
    "rounded-lg border border-cyber-line bg-surface-elevated/60 px-3 py-1.5 text-xs font-medium text-ink-soft transition-colors hover:border-accent/40 hover:text-ink disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:border-cyber-line disabled:hover:text-ink-soft";

  return (
    <nav className="flex items-center justify-between border-t border-cyber-line px-4 py-3">
      <p className="text-xs text-ink-faint">
        Page <span className="font-medium text-ink">{page}</span> of {pages} ·{" "}
        {total} total
      </p>
      <div className="flex gap-2">
        <button
          className={btn}
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          Previous
        </button>
        <button
          className={btn}
          disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          Next
        </button>
      </div>
    </nav>
  );
}