import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import AuthField from "@/components/auth/AuthField";
import AuthLayout from "@/components/auth/AuthLayout";
import { getPasskeyAssertion, isWebAuthnAvailable } from "@/components/auth/webauthn";
import Button from "@/components/ui/Button";
import { auth, profile } from "@/lib/endpoints";
import { mapAuthError } from "@/lib/authErrors";
import { useAuthStore } from "@/store/authStore";

type Step = "credentials" | "mfa" | "forgot" | "forgot-sent";

function isEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);

  const [step, setStep] = useState<Step>("credentials");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [mfaToken, setMfaToken] = useState<string | null>(null);
  const [touched, setTouched] = useState({ email: false, password: false });
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [passkeyLoading, setPasskeyLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [showResend, setShowResend] = useState(false);

  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ??
    "/dashboard";
  const registered =
    (location.state as { registered?: boolean })?.registered === true;

  const emailError =
    touched.email && email.trim() !== "" && !isEmail(email)
      ? "Enter a valid email address."
      : null;
  const passwordError =
    touched.password && password === "" ? "Enter your password." : null;

  async function finish(accessToken: string) {
    setTokens(accessToken);
    try {
      const me = await profile.me();
      setUser(me);
    } catch {
      setUser(null);
    }
    navigate(from, { replace: true });
  }

  async function handleCredentials(e: FormEvent) {
    e.preventDefault();
    setTouched({ email: true, password: true });
    setError(null);
    setNotice(null);
    setShowResend(false);

    if (!isEmail(email)) {
      setError("Enter a valid email address to continue.");
      return;
    }
    if (!password) {
      setError("Enter your password to continue.");
      return;
    }

    setLoading(true);
    try {
      const res = await auth.login({
        email: email.trim(),
        password
      });
      if (res.mfa_required && res.mfa_token) {
        setMfaToken(res.mfa_token);
        setStep("mfa");
        return;
      }
      await finish(res.access_token);
    } catch (err) {
      const mapped = mapAuthError(err);
      setError(mapped.message);
      setShowResend(mapped.kind === "unverified");
    } finally {
      setLoading(false);
    }
  }

  async function handleMfa(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!mfaToken || code.trim().length < 6) {
      setError("Enter the 6-digit code from your authenticator app.");
      return;
    }
    setLoading(true);
    try {
      const res = await auth.verifyMfa({
        mfa_token: mfaToken,
        code: code.trim()
      });
      await finish(res.access_token);
    } catch (err) {
      setError(mapAuthError(err).message);
    } finally {
      setLoading(false);
    }
  }

  async function handlePasskey() {
    setError(null);
    setNotice(null);
    setPasskeyLoading(true);
    try {
      const { options } = await auth.passkeyLoginBegin(
        isEmail(email) ? { email: email.trim() } : {}
      );
      const assertion = await getPasskeyAssertion(options);
      const res = await auth.passkeyLoginComplete({ response: assertion });
      await finish(res.access_token);
    } catch (err) {
      setError(
        err instanceof Error && !("response" in (err as object))
          ? err.message
          : mapAuthError(err).message
      );
    } finally {
      setPasskeyLoading(false);
    }
  }

  async function handleForgot(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!isEmail(email)) {
      setError("Enter the email address for your account first.");
      return;
    }
    setLoading(true);
    try {
      await auth.requestPasswordReset({ email: email.trim() });
      setStep("forgot-sent");
    } catch (err) {
      setError(mapAuthError(err).message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setResending(true);
    try {
      await auth.resendVerification({ email: email.trim() });
      setNotice("Verification link re-sent — check your inbox.");
      setShowResend(false);
    } catch {
      setNotice("If that account is pending verification, a new link is on its way.");
      setShowResend(false);
    } finally {
      setResending(false);
    }
  }

  function backToCredentials() {
    setStep("credentials");
    setMfaToken(null);
    setCode("");
    setError(null);
    setNotice(null);
    setShowResend(false);
  }

  return (
    <AuthLayout
      eyebrow="Access control"
      title={step === "mfa" ? "Check your authenticator" : "Welcome back"}
      subtitle={
        step === "mfa"
          ? "Your account is protected with MFA. Enter the current code to finish signing in."
          : "Authenticate to unlock your encrypted workspace."
      }
      footer={
        step === "credentials" ? (
          <>
            No account?{" "}
            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:text-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Create one
            </Link>
          </>
        ) : undefined
      }
    >
      {registered && step === "credentials" && (
        <div
          role="status"
          className="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-2.5 text-sm text-emerald-700 dark:text-emerald-300"
        >
          Account created — sign in with your new credentials.
        </div>
      )}

      {step === "credentials" && (
        <form onSubmit={handleCredentials} className="space-y-4" noValidate>
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
          <div>
            <AuthField
              label="Password"
              type="password"
              required
              revealable
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onBlur={() => setTouched((t) => ({ ...t, password: true }))}
              placeholder="••••••••••••"
              error={passwordError}
            />
            <div className="mt-1.5 text-right">
              <button
                type="button"
                onClick={() => {
                  setStep("forgot");
                  setError(null);
                  setNotice(null);
                }}
                className="text-xs font-medium text-slate-500 transition-colors hover:text-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-slate-400 dark:hover:text-blue-400"
              >
                Forgot password?
              </button>
            </div>
          </div>

          {error && (
            <div
              role="alert"
              className="animate-fade-in rounded-lg border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-700 dark:text-red-300"
            >
              {error}
              {showResend && isEmail(email) && (
                <button
                  type="button"
                  onClick={handleResend}
                  disabled={resending}
                  className="ml-2 font-semibold underline underline-offset-2 hover:no-underline disabled:opacity-50"
                >
                  {resending ? "Sending…" : "Resend link"}
                </button>
              )}
            </div>
          )}
          {notice && (
            <div
              role="status"
              className="animate-fade-in rounded-lg border border-blue-500/30 bg-blue-500/10 px-3.5 py-2.5 text-sm text-blue-700 dark:text-blue-300"
            >
              {notice}
            </div>
          )}

          <Button type="submit" className="w-full py-3" loading={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </Button>

          {isWebAuthnAvailable() && (
            <>
              <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-500">
                <span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" aria-hidden="true" />
                or
                <span className="h-px flex-1 bg-slate-200 dark:bg-slate-800" aria-hidden="true" />
              </div>
              <Button
                type="button"
                variant="outline"
                className="w-full border-slate-300 bg-transparent py-3 text-slate-700 hover:border-slate-400 dark:border-slate-700 dark:text-slate-200 dark:hover:border-slate-600 dark:hover:bg-slate-800"
                onClick={handlePasskey}
                loading={passkeyLoading}
              >
                {passkeyLoading ? "Waiting for passkey…" : "Continue with passkey"}
              </Button>
            </>
          )}
        </form>
      )}

      {step === "mfa" && (
        <form onSubmit={handleMfa} className="space-y-4">
          <AuthField
            label="Authenticator code"
            required
            inputMode="numeric"
            autoComplete="one-time-code"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="000000"
            hint="Enter the 6-digit code from your authenticator app"
          />
          {error && (
            <div
              role="alert"
              className="animate-fade-in rounded-lg border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-700 dark:text-red-300"
            >
              {error}
            </div>
          )}
          <Button type="submit" className="w-full py-3" loading={loading}>
            {loading ? "Verifying…" : "Verify code"}
          </Button>
          <button
            type="button"
            onClick={backToCredentials}
            className="w-full text-center text-sm text-slate-500 transition-colors hover:text-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-slate-400 dark:hover:text-blue-400"
          >
            Back to sign in
          </button>
        </form>
      )}

      {step === "forgot" && (
        <form onSubmit={handleForgot} className="space-y-4" noValidate>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Enter your account email and we&apos;ll send a reset link. The link
            expires — check spam if it doesn&apos;t arrive.
          </p>
          <AuthField
            label="Email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
            error={email.trim() !== "" && !isEmail(email) ? "Enter a valid email address." : null}
          />
          {error && (
            <div
              role="alert"
              className="animate-fade-in rounded-lg border border-red-500/30 bg-red-500/10 px-3.5 py-2.5 text-sm text-red-700 dark:text-red-300"
            >
              {error}
            </div>
          )}
          <Button type="submit" className="w-full py-3" loading={loading}>
            {loading ? "Sending…" : "Send reset link"}
          </Button>
          <button
            type="button"
            onClick={backToCredentials}
            className="w-full text-center text-sm text-slate-500 transition-colors hover:text-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-slate-400 dark:hover:text-blue-400"
          >
            Back to sign in
          </button>
        </form>
      )}

      {step === "forgot-sent" && (
        <div className="space-y-4 text-center">
          <div
            role="status"
            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-3 text-sm text-emerald-700 dark:text-emerald-300"
          >
            If that email exists, a reset link is on its way to{" "}
            <span className="font-mono font-semibold">{email.trim()}</span>.
          </div>
          <button
            type="button"
            onClick={backToCredentials}
            className="w-full text-center text-sm text-slate-500 transition-colors hover:text-blue-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-500 dark:text-slate-400 dark:hover:text-blue-400"
          >
            Back to sign in
          </button>
        </div>
      )}
    </AuthLayout>
  );
}
