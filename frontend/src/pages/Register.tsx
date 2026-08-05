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
    <div className="flex min-h-screen items-center justify-center bg-surface-soft px-4 py-12">
      <div className="w-full max-w-md animate-fade-up">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-gradient text-white shadow-card">
            <IconShield />
          </span>
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
            Provision workspace
          </p>
          <h1 className="mt-2 text-2xl font-extrabold tracking-tight text-ink">
            Create your account
          </h1>
          <p className="mt-1 text-sm text-ink-faint">
            Provision a new encrypted vault workspace.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-cyber-line bg-surface-elevated p-7 shadow-modal"
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
            <div className="animate-fade-in rounded-lg border border-red-200 bg-red-50 px-3.5 py-2.5 text-sm text-red-700">
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
            className="font-semibold text-brand-600 transition-colors hover:text-brand-700"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
