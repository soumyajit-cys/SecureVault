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
    <div className="flex min-h-screen">
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-brand-900 p-12 text-white lg:flex">
        <div className="absolute -left-24 -top-24 h-96 w-96 rounded-full bg-brand-500/30 blur-3xl" />
        <div className="absolute -bottom-32 -right-16 h-96 w-96 rounded-full bg-brand-400/20 blur-3xl" />
        <div className="relative z-10 flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/20">
            <svg
              className="h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />
            </svg>
          </span>
          <span className="text-lg font-bold tracking-tight">SecureVault</span>
        </div>

        <div className="relative z-10">
          <h2 className="text-3xl font-bold leading-tight">
            Enterprise-grade encryption, without the complexity.
          </h2>
          <ul className="mt-6 space-y-3 text-sm text-brand-100">
            {[
              "AES-256-GCM authenticated encryption",
              "Key rotation, revocation and audit trails",
              "Files sealed at rest — never stored in plaintext"
            ].map((item) => (
              <li key={item} className="flex items-center gap-3">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/15 text-xs text-white">
                  ✓
                </span>
                {item}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative z-10 text-xs text-brand-200">
          SecureVault · Zero plaintext storage
        </p>
      </div>

      <div className="flex w-full items-center justify-center bg-slate-50 px-4 py-12 lg:w-1/2">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <span className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm lg:hidden">
              <svg
                className="h-6 w-6"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5" />
              </svg>
            </span>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Sign in
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Welcome back — secure your data again.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
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
              <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            )}

            <Button type="submit" className="w-full">
              Sign in
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            No account?{" "}
            <Link to="/register" className="font-medium text-brand-600 hover:text-brand-700">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}