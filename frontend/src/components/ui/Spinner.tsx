export default function Spinner({ className = "" }: { className?: string }) {
  return (
    <div
      className={`mx-auto h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-brand-600 ${className}`}
    />
  );
}

export function FullPageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Spinner className="mx-auto h-10 w-10" />
        <p className="mt-3 text-sm text-slate-500">Loading…</p>
      </div>
    </div>
  );
}