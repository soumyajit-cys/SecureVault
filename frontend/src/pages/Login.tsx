import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import Button from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { auth, profile } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { IconShield } from "@/components/layout/Sidebar";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? "/dashboard";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      const res = await auth.login({ email, password });
      setTokens(res.access_token, res.refresh_token);

      try {
        const me = await profile.me();
        setUser(me);
      } catch {
        setUser(null);
      }

      navigate(from, { replace: true });
    } catch (err) {
      setError(extractDetail(err));
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-surface-soft px-4 py-12">
      <div className="w-full max-w-md animate-fade-up">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-card">
            <IconShield />
          </span>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
            Access control
          </p>
          <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-ink">
            Welcome back
          </h1>
          <p className="mt-1 text-sm text-ink-faint">
            Authenticate to unlock your encrypted workspace.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-5 rounded-2xl border border-cyber-line bg-surface-elevated p-8 shadow-modal"
        >
          <TextField
            label="Email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />

          <TextField
            label="Password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
          />

          {error && (
            <div className="animate-fade-in rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full py-3">
            Sign in
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-faint">
          No account?{" "}
          <Link
            to="/register"
            className="font-semibold text-brand-600 transition-colors hover:text-brand-700"
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
