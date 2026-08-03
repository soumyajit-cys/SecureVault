import Badge from "@/components/ui/Badge";
import Card from "@/components/ui/Card";
import { useAuthStore } from "@/store/authStore";

export default function Profile() {
  const me = useAuthStore((s) => s.user);

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <Card title="Account details">
        <dl className="space-y-3 text-sm">
          {[
            ["Username", me?.username ?? "—"],
            ["Email", me?.email ?? "—"],
            ["Status", me?.is_active ? "Active" : "Disabled"],
            ["Verified", me?.is_verified ? "Yes" : "No"],
            ["User ID", me?.id ?? "—"]
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between gap-4">
              <dt className="text-ink-faint">{k}</dt>
              <dd className="font-mono text-sm text-ink">{v}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-4 flex flex-wrap gap-2">
          {me?.roles?.map((r) => (
            <Badge key={r.id} color="indigo">
              {r.name}
            </Badge>
          ))}
        </div>
      </Card>
    </div>
  );
}