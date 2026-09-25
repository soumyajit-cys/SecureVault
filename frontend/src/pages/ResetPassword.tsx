import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import AuthField from "@/components/auth/AuthField";
import AuthLayout from "@/components/auth/AuthLayout";
import PasswordStrength, {
  checkPassword
} from "@/components/auth/PasswordStrength";
import Button from "@/components/ui/Button";
import { auth } from "@/lib/endpoints";
import { mapAuthError } from "@/lib/authErrors";

/**
 * Completes the backend's reset flow: the emailed link lands here as
 * `/reset-password?token=…`, the user picks a new password, and we call
 * `POST /auth/password-reset/confirm`.
 */
export default function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = (params.get("token") ?? "").trim();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [breached, setBreached] = useState(false);
  const [loading, setLoading] = useState(false);

  const policyOk = checkPassword(password).every((c) => c.pass);
  const valid = token !== "" && policyOk && confirm === password && password !== "";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBreached(false);
    if (!policyOk) {
      setError("Your new password doesn't meet the policy yet.");
      return;
    }
    if (confirm !== password) {
      setError("Passwords don't match.");
      return;
    }
    setLoading(true);
    try {
      await auth.confirmPasswordReset({ token, new_password: password });
      navigate("/login", {
        state: { registered: false },
        replace: true
      });
    } catch (err) {
      const mapped = mapAuthError(err);
      setError(mapped.message);
      setBreached(mapped.kind === "breached-password");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout
      eyebrow="Password reset"
      title="Choose a new password"
      subtitle="It must meet the same policy as registration."
      footer={
        <>
          Remembered it?{" "}
          <Link
            to="/login"
            className="font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Sign in
          </Link>
        </>
      }
    >
      {token === "" ? (
        <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">
          This link doesn&apos;t include a reset token. Open the link from your
          inbox on this device — it looks like{" "}
          <span className="font-mono text-xs">/reset-password?token=…</span>.
        </p>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="space-y-2">
            <AuthField
              label="New password"
              type="password"
              required
              revealable
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
            />
            <PasswordStrength password={password} compact />
          </div>
          <AuthField
            label="Confirm new password"
            type="password"
            required
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="••••••••••••"
            error={
              confirm !== "" && confirm !== password
                ? "Passwords don't match yet."
                : null
            }
          />
          {error && (
            <div
              role="alert"
              className="animate-fade-in rounded-lg border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-700 dark:text-red-300"
            >
              {error}
              {breached && (
                <p className="mt-1 text-xs opacity-90">
                  That password appeared in public breach data — pick a fresh
                  passphrase instead.
                </p>
              )}
            </div>
          )}
          <Button
            type="submit"
            className="w-full py-3"
            loading={loading}
            disabled={!valid}
          >
            {loading ? "Resetting…" : "Reset password"}
          </Button>
        </form>
      )}
    </AuthLayout>
  );
}
