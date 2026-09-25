import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import AuthLayout from "@/components/auth/AuthLayout";
import Button from "@/components/ui/Button";
import { auth } from "@/lib/endpoints";
import { mapAuthError } from "@/lib/authErrors";

type Status = "idle" | "working" | "ok" | "failed";

/**
 * Handles the link emailed by the backend's verification flow:
 * `/verify-email?token=…` → `POST /auth/verify-email`.
 */
export default function VerifyEmail() {
  const [params] = useSearchParams();
  const token = (params.get("token") ?? "").trim();
  const [status, setStatus] = useState<Status>(token ? "working" : "idle");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    auth
      .verifyEmail({ token })
      .then((res) => {
        if (!cancelled) {
          setStatus("ok");
          setMessage(res.message || "Email verified. You can now sign in.");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setStatus("failed");
          setMessage(mapAuthError(err).message);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <AuthLayout
      eyebrow="Email verification"
      title="Verify your email"
      subtitle="One click confirms this address belongs to you."
      footer={
        <>
          <Link
            to="/login"
            className="font-semibold text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Back to sign in
          </Link>
        </>
      }
    >
      {!token && (
        <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">
          This link doesn&apos;t include a verification token. Open the link
          from your inbox on this device, or paste it here as{" "}
          <span className="font-mono text-xs">/verify-email?token=…</span>.
        </p>
      )}
      {status === "working" && (
        <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-400">
          <span
            className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"
            aria-hidden="true"
          />
          Verifying…
        </div>
      )}
      {status === "ok" && message && (
        <div className="space-y-4">
          <div
            role="status"
            className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3.5 py-3 text-sm text-emerald-700 dark:text-emerald-300"
          >
            {message}
          </div>
          <Link to="/login">
            <Button className="w-full py-3">Continue to sign in</Button>
          </Link>
        </div>
      )}
      {status === "failed" && message && (
        <div
          role="alert"
          className="rounded-lg border border-red-500/30 bg-red-500/10 px-3.5 py-3 text-sm text-red-700 dark:text-red-300"
        >
          {message} Try signing in — you can request a fresh link from there.
        </div>
      )}
    </AuthLayout>
  );
}
