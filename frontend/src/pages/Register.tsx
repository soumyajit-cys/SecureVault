import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthField from "@/components/auth/AuthField";
import AuthLayout from "@/components/auth/AuthLayout";
import PasswordStrength, {
  checkPassword
} from "@/components/auth/PasswordStrength";
import Button from "@/components/ui/Button";
import { auth } from "@/lib/endpoints";
import { mapAuthError } from "@/lib/authErrors";

function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

function isUsername(value: string): boolean {
  return /^[a-zA-Z0-9._-]{3,32}$/.test(value.trim());
}

export default function Register() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [touched, setTouched] = useState({
    email: false,
    username: false,
    confirm: false
  });
  const [error, setError] = useState<string | null>(null);
  const [breached, setBreached] = useState(false);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);

  const emailError =
    touched.email && email.trim() !== "" && !isEmail(email)
      ? "Enter a valid email address."
      : null;
  const usernameError =
    touched.username && username.trim() !== "" && !isUsername(username)
      ? "3–32 characters: letters, numbers, dots, dashes, underscores."
      : null;
  const confirmError =
    touched.confirm && confirm !== "" && confirm !== password
      ? "Passwords don't match yet."
      : null;

  const policy = checkPassword(password);
  const policyOk = policy.every((c) => c.pass);
  const formValid =
    isEmail(email) &&
    isUsername(username) &&
    policyOk &&
    confirm === password &&
    password !== "" &&
    accepted;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setTouched({ email: true, username: true, confirm: true });
    setError(null);
    setBreached(false);

    if (!isEmail(email)) {
      setError("Enter a valid email address to continue.");
      return;
    }
    if (!isUsername(username)) {
      setError(
        "Pick a username of 3–32 characters (letters, numbers, dots, dashes, underscores)."
      );
      return;
    }
    if (!policyOk) {
      setError(
        "Your password doesn't meet the policy yet — see the checklist below."
      );
      return;
    }
    if (confirm !== password) {
      setError("Passwords don't match. Re-enter them to continue.");
      return;
    }
    if (!accepted) {
      setError("Please accept the terms of service and privacy policy.");
      return;
    }

    setLoading(true);
    try {
      // The backend creates the account and replies
      // "Account created. Please sign in." — it does not log you in
      // and may require email verification first (see EMAIL_VERIFICATION_REQUIRED).
      await auth.register({
        email: email.trim(),
        username: username.trim(),
        password
      });
      setDone(true);
    } catch (err) {
      const mapped = mapAuthError(err);
      setError(mapped.message);
      setBreached(mapped.kind === "breached-password");
    } finally {
      setLoading(false);
    }
  }

  if (done) {
    return (
      <AuthLayout
        eyebrow="Workspace provisioned"
        title="Check your inbox"
        subtitle="Your vault account was created."
      >
        <div className="space-y-4">
          <div
            role="status"
            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-3 text-sm leading-relaxed text-emerald-700 dark:text-emerald-300"
          >
            Account created for{" "}
            <span className="font-mono font-semibold">{email.trim()}</span>.
            If email verification is enabled on this server, follow the link we
            sent before signing in.
          </div>
          <Button
            className="w-full py-3"
            onClick={() =>
              navigate("/login", { state: { registered: true }, replace: true })
            }
          >
            Continue to sign in
          </Button>
        </div>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      eyebrow="Provision workspace"
      title="Create your account"
      subtitle="One account seals files, folders and text — with full key control."
      footer={
        <>
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-blue-600 hover:text-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <AuthField
          label="Email"
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          onBlur={() => setTouched((t) => ({ ...t, email: true }))}
          placeholder="you@company.com"
          error={emailError}
        />
        <AuthField
          label="Username"
          required
          autoComplete="username"
          minLength={3}
          maxLength={32}
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          onBlur={() => setTouched((t) => ({ ...t, username: true }))}
          placeholder="alice"
          hint="Shown on shares and audit events. 3–32 characters."
          error={usernameError}
        />
        <div className="space-y-2">
          <AuthField
            label="Password"
            type="password"
            required
            revealable
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            hint="Min 12 characters, mixed case, a number and a symbol. Hashed with Argon2id — never stored."
          />
          <PasswordStrength password={password} />
        </div>
        <AuthField
          label="Confirm password"
          type="password"
          required
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          onBlur={() => setTouched((t) => ({ ...t, confirm: true }))}
          placeholder="••••••••••••"
          error={confirmError}
        />

        <label className="flex cursor-pointer items-start gap-2.5 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer accent-blue-600"
          />
          <span>
            I agree to the{" "}
            <span className="font-medium text-slate-800 dark:text-slate-200">
              terms of service
            </span>{" "}
            and{" "}
            <span className="font-medium text-slate-800 dark:text-slate-200">
              privacy policy
            </span>
            , and I understand SecureVault is server-side encrypted custody —
            not zero-knowledge.
          </span>
        </label>

        {error && (
          <div
            role="alert"
            className="animate-fade-in rounded-lg border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-700 dark:text-red-300"
          >
            {error}
            {breached && (
              <p className="mt-1 text-xs opacity-90">
                This check compares only a hash prefix against public breach
                data (HIBP k-anonymity) — your password never leaves this form
                except to create your account.
              </p>
            )}
          </div>
        )}

        <Button
          type="submit"
          className="w-full py-3"
          loading={loading}
          disabled={!formValid}
        >
          {loading ? "Creating vault…" : "Create account"}
        </Button>
      </form>
    </AuthLayout>
  );
}
