import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import Button from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { auth, profile } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { IconShield } from "@/components/layout/Sidebar";

const terminalLines = [
  "$ svault auth --verify-identity",
  "> argon2id [ok] · scrypt [ok] · rsa-4096 [ok]",
  "> session sealed · nonce generated · keys rotated",
  "$ vault status: OPERATIONAL"
];

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
    <div className="relative flex min-h-screen overflow-hidden bg-cyber">
      {/* Cyber grid + glow */}
      <div className="pointer-events-none absolute inset-0 cyber-bg" />
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-40 left-1/2 h-[520px] w-[900px] -translate-x-1/2 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-20 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute -right-24 top-10 h-96 w-96 rounded-full bg-brand-500/10 blur-3xl" />
      </div>

      <div className="relative mx-auto flex w-full max-w-6xl items-center justify-center px-6 py-16 lg:px-10">
        {/* Left brand panel */}
        <div className="relative hidden min-h-[560px] w-1/2 overflow-hidden rounded-3xl border border-cyber-line bg-surface-elevated/60 p-12 backdrop-blur-xl lg:flex lg:flex-col lg:justify-between">
          {/* scan line */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-3xl">
            <div className="absolute left-0 h-px w-full animate-scan-line bg-gradient-to-r from-transparent via-accent/60 to-transparent" />
          </div>
          <div className="pointer-events-none absolute inset-0 opacity-20">
            <div className="absolute -top-24 -right-24 h-96 w-96 animate-float-slow rounded-full bg-brand-500/20 blur-3xl" />
            <div className="absolute bottom-16 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-accent/20 blur-3xl" />
          </div>

          <div className="relative z-10 flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow">
              <IconShield />
            </span>
            <span className="text-lg font-bold tracking-tight text-ink">
              SecureVault
            </span>
          </div>

          <div className="relative z-10">
            <p className="term-label">Identity gateway</p>
            <h2 className="mt-3 text-4xl font-extrabold leading-tight tracking-tight text-ink">
              Enterprise-grade encryption,{" "}
              <span className="bg-brand-gradient-warm bg-clip-text text-transparent text-glow">
                without the complexity.
              </span>
            </h2>
            <ul className="mt-8 space-y-3.5 text-sm text-ink-soft">
              {[
                ["AES-256-GCM", "authenticated encryption for every payload"],
                ["Key rotation", "RS256 signatures and revocation trails"],
                ["Sealed at rest", "plaintext never touches the vault"]
              ].map(([k, v]) => (
                <li key={k} className="flex items-center gap-3.5">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-brand-400/40 bg-brand-500/10 text-xs text-brand-300">
                    ✓
                  </span>
                  <p>
                    <strong className="font-semibold text-ink">{k}</strong>
                    <span className="text-ink-faint"> — {v}</span>
                  </p>
                </li>
              ))}
            </ul>
          </div>

          {/* terminal */}
          <div className="relative z-10 rounded-xl border border-cyber-line bg-cyber/80 p-4 font-mono">
            <div className="mb-3 flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-amber-500/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/70" />
              <span className="ml-2 text-[11px] uppercase tracking-widest text-ink-faint">
                vault — self test
              </span>
            </div>
            {terminalLines.map((line) => (
              <p key={line} className="text-[11px] leading-6 text-accent/80">
                {line}
              </p>
            ))}
          </div>
        </div>

        {/* Form panel */}
        <div className="flex w-full items-center justify-center lg:w-1/2">
          <div className="w-full max-w-md animate-fade-up">
            <div className="mb-8 lg:hidden">
              <span className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow">
                <IconShield />
              </span>
            </div>

            <div className="rounded-3xl border border-cyber-line bg-surface-elevated/70 p-8 shadow-modal backdrop-blur-xl">
              <p className="term-label">Access control</p>
              <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-ink">
                Welcome back
              </h1>
              <p className="mt-1 text-sm text-ink-faint">
                Authenticate to unlock your encrypted workspace.
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
                  <div className="animate-fade-in rounded-xl border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-300">
                    {error}
                  </div>
                )}

                <Button type="submit" className="w-full py-3">
                  Sign in
                </Button>
              </form>
            </div>

            <p className="mt-6 text-center text-sm text-ink-faint">
              No account?{" "}
              <Link
                to="/register"
                className="font-semibold text-brand-400 transition-colors hover:text-brand-300"
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