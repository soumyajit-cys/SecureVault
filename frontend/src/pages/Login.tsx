import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import Button from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { auth, profile } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

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
    <div className="grid-bg flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-neon-cyan text-3xl font-bold text-vault-950 shadow-glow">
            ▣
          </span>
          <h1 className="mt-4 text-2xl font-bold tracking-wide text-white">
            SECUREVAULT
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Enterprise-grade encryption. Secure by design.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-lg border border-vault-700 bg-vault-900/80 p-6 shadow-2xl backdrop-blur"
        >
          <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-300">
            Sign in
          </h2>

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
            <p className="rounded border border-neon-red/40 bg-neon-red/10 px-3 py-2 text-sm text-neon-red">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full">
            Authenticate
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          No account?{" "}
          <Link to="/register" className="text-neon-cyan hover:underline">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}