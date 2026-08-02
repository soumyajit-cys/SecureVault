import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Button from "@/components/ui/Button";
import { TextField } from "@/components/ui/Field";
import { auth } from "@/lib/endpoints";
import { extractDetail } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

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
            Provision a new vault account
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-lg border border-vault-700 bg-vault-900/80 p-6 shadow-2xl backdrop-blur"
        >
          <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-300">
            Create account
          </h2>

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
            hint="Min 12 characters"
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
            <p className="rounded border border-neon-red/40 bg-neon-red/10 px-3 py-2 text-sm text-neon-red">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" loading={registration.isPending}>
            {registration.isPending ? "Creating vault…" : "Create account"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="text-neon-cyan hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}