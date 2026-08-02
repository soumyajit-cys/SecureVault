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
    <div className="relative flex min-h-screen overflow-hidden">
      {/* Ambient background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-brand-200/40 blur-3xl" />
        <div className="absolute -bottom-40 -left-20 h-96 w-96 rounded-full bg-brand-300/30 blur-3xl" />
        <div className="absolute -right-24 top-10 h-96 w-96 rounded-full bg-brand-200/30 blur-3xl" />
      </div>

      <div className="relative mx-auto flex w-full max-w-6xl items-center justify-center px-6 py-16 lg:px-10">
        {/* Left brand panel */}
        <div className="relative hidden min-h-[560px] w-1/2 overflow-hidden rounded-3xl bg-brand-gradient p-12 text-white shadow-glow lg:flex lg:flex-col lg:justify-between">
          <div className="pointer-events-none absolute inset-0 opacity-20">
            <div className="absolute -top-24 -right-24 h-96 w-96 animate-float-slow rounded-full bg-white/20 blur-3xl" />
            <div className="absolute bottom-16 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-brand-300/40 blur-3xl" />
          </div>

          <div className="relative z-10 flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/15 ring-1 ring-white/25 backdrop-blur">
              <IconShield />
            </span>
            <span className="text-lg font-bold tracking-tight">SecureVault</span>
          </div>

          <div className="relative z-10">
            <h2 className="text-4xl font-extrabold leading-tight tracking-tight">
              Enterprise-grade encryption,{" "}
              <span className="text-brand-200">without the complexity.</span>
            </h2>
            <ul className="mt-8 space-y-3.5 text-sm text-brand-100">
              {[
                ["AES-256-GCM", "authenticated encryption for every payload"],
                ["Key rotation", "revocation and full audit trails"],
                ["Sealed at rest", "plaintext is never written to the vault"]
              ].map(([k, v]) => (
                <li key={k} className="flex items-center gap-3.5">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white/15 text-xs text-white">
                    ✓
                  </span>
                  <p>
                    <strong className="font-semibold text-white">{k}</strong>
                    <span className="text-brand-100/90"> — {v}</span>
                  </p>
                </li>
              ))}
            </ul>
          </div>

          <p className="relative z-10 text-xs text-brand-200/90">
            SecureVault · Zero plaintext storage · RBAC enforced server-side
          </p>
        </div>

        {/* Form panel */}
        <div className="flex w-full items-center justify-center lg:w-1/2">
          <div className="w-full max-w-md animate-fade-up">
            <div className="mb-8 lg:hidden">
              <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow-sm">
                <IconShield />
              </span>
            </div>

            <div className="rounded-3xl border border-slate-200/70 bg-white/80 p-8 shadow-modal backdrop-blur-xl">
              <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
                Welcome back
              </h1>
              <p className="mt-1 text-sm text-slate-500">
                Sign in to unlock your encrypted workspace.
              </p>

              <form onSubmit={handleSubmit} className="mt-8 space-y-5">
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
                  <div className="animate-fade-in rounded-xl border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <Button type="submit" className="w-full py-3">
                  Sign in
                </Button>
              </form>
            </div>

            <p className="mt-6 text-center text-sm text-slate-500">
              No account?{" "}
              <Link
                to="/register"
                className="font-semibold text-brand-600 transition-colors hover:text-brand-700"
              >
                Create one — it&apos;s free
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}