import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Button from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { auth } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { IconShield } from "@/components/layout/Sidebar";

export default function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  const registration = useMutation({
    mutationFn: () => auth.register({ email, username, password }),
    onSuccess: async () => {
      const res = await auth.login({ email, password });
      useAuthStore.getState().setTokens(res.access_token, res.refresh_token);
      useAuthStore.getState().setUser(null);
      navigate("/dashboard", { replace: true });
    },
    onError: (err) => setError(extractDetail(err))
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 12) {
      setError("Password must be at least 12 characters.");
      return;
    }

    registration.mutate();
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-cyber px-4 py-12">
      {/* Cyber grid + glow */}
      <div className="pointer-events-none absolute inset-0 cyber-bg" />
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -top-32 left-1/2 h-96 w-[800px] -translate-x-1/2 rounded-full bg-brand-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-24 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-md animate-fade-up">
        <div className="mb-8 text-center">
          <span className="relative mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-glow">
            <IconShield />
            <span className="absolute inset-0 animate-pulse-ring rounded-2xl border border-brand-400/50" />
          </span>
          <p className="term-label">Provision workspace</p>
          <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-ink">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-ink-faint">
            Provision a new encrypted vault workspace.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-3xl border border-cyber-line bg-surface-elevated/70 p-7 shadow-modal backdrop-blur-xl"
        >
          <TextField
            label="Email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
          <TextField
            label="Username"
            required
            minLength={3}
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="alice"
          />
          <TextField
            label="Password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            hint="Min 12 characters, mixed case, a number and a symbol"
            placeholder="••••••••••••"
          />
          <TextField
            label="Confirm password"
            type="password"
            required
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="••••••••••••"
          />

          {error && (
            <div className="animate-fade-in rounded-xl border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-300">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full py-3" loading={registration.isPending}>
            {registration.isPending ? "Creating vault…" : "Create account"}
          </Button>

          <p className="pt-1 text-center text-xs text-ink-faint">
            Passwords are hashed with Argon2id — never stored in plaintext.
          </p>
        </form>

        <p className="mt-6 text-center text-sm text-ink-faint">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-brand-400 transition-colors hover:text-brand-300"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}