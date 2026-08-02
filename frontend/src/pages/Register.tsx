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
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-12">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm">
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
            Create your account
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Provision a new vault workspace.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-xl border border-slate-200 bg-white p-6 shadow-card"
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
            <p className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" loading={registration.isPending}>
            {registration.isPending ? "Creating vault…" : "Create account"}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-brand-600 hover:text-brand-700">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}