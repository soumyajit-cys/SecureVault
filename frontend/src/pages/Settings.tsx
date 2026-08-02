import { useState } from "react";
import { useNavigate } from "react-router-dom";

import Button from "@/components/ui/Button";
import Card from "@/components/ui/Card";
import { TextField } from "@/components/ui/Field";
import api, { extractDetail } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { toastSuccess } from "@/components/ui/Toast";

export default function Settings() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleChangePassword(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (next !== confirm) {
      setError("New passwords do not match.");
      return;
    }
    if (next.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }

    setLoading(true);
    try {
      await api.post("/auth/change-password", {
        current_password: current,
        new_password: next
      });
      toastSuccess("Password changed");
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setError(extractDetail(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await api.post("/auth/logout", { refresh_token: localStorage.getItem("securevault_refresh_token") });
    } catch {
      /* ignore */
    }
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card title="Change password">
        <form onSubmit={handleChangePassword} className="space-y-4">
          <TextField
            label="Current password"
            type="password"
            required
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
          />
          <TextField
            label="New password"
            type="password"
            required
            value={next}
            onChange={(e) => setNext(e.target.value)}
            hint="Minimum 12 characters"
          />
          <TextField
            label="Confirm new password"
            type="password"
            required
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
          />

          {error && (
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <Button type="submit" loading={loading} disabled={!current || !next}>
            Update password
          </Button>
        </form>
      </Card>

      <Card title="Sessions">
        <p className="mb-3 text-sm text-slate-500">
          Sign out of this device only. Tokens are rotated on every login.
        </p>
        <Button variant="outline" onClick={handleLogout}>
          Sign out of this device
        </Button>
      </Card>
    </div>
  );
}