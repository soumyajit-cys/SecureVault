import axios from "axios";

import { extractDetail } from "@/lib/api";

export type AuthErrorKind =
  | "invalid-credentials"
  | "locked"
  | "rate-limited"
  | "unverified"
  | "deactivated"
  | "mfa"
  | "mfa-enforcement"
  | "conflict"
  | "weak-password"
  | "breached-password"
  | "generic";

export interface MappedAuthError {
  kind: AuthErrorKind;
  /** Short, user-facing message safe to render. */
  message: string;
  /** HTTP status when known. */
  status?: number;
}

const BREACH_HINT = "breach";

function statusOf(error: unknown): number | undefined {
  if (axios.isAxiosError(error)) return error.response?.status;
  return undefined;
}

/**
 * Map the backend's actual `{"detail": ...}` responses to friendly,
 * actionable UI copy. The backend raises several auth errors with empty
 * messages (`InvalidCredentialsError()`, `AccountLockedError()`), so an
 * empty detail still needs a sensible fallback rather than a blank alert.
 */
export function mapAuthError(error: unknown): MappedAuthError {
  const status = statusOf(error);
  const detail = extractDetail(error).trim();

  const lowered = detail.toLowerCase();

  if (lowered.includes(BREACH_HINT) || lowered.includes("pwned")) {
    return {
      kind: "breached-password",
      message:
        "That password has turned up in public breach data, so we can't accept it. " +
        "Try a longer passphrase unique to SecureVault — a password manager makes this easy.",
      status
    };
  }
  if (
    lowered.includes("at least") ||
    lowered.includes("uppercase") ||
    lowered.includes("lowercase") ||
    lowered.includes("special character") ||
    lowered.includes("number")
  ) {
    return {
      kind: "weak-password",
      message: detail,
      status
    };
  }
  if (lowered.includes("already exists")) {
    return {
      kind: "conflict",
      message:
        detail +
        " Try signing in instead — or reset your password if it might be yours.",
      status
    };
  }
  if (
    lowered.includes("locked") ||
    lowered.includes("too many attempts") ||
    status === 429
  ) {
    return {
      kind: status === 429 ? "rate-limited" : "locked",
      message:
        detail ||
        "This account is temporarily locked after too many failed attempts. " +
          "Wait a few minutes and try again, or reset your password.",
      status
    };
  }
  if (lowered.includes("verification required") || lowered.includes("not verified")) {
    return {
      kind: "unverified",
      message:
        "Your email address isn't verified yet. Check your inbox for the verification link.",
      status
    };
  }
  if (lowered.includes("deactivat")) {
    return {
      kind: "deactivated",
      message:
        "This account has been deactivated. Contact your workspace administrator.",
      status
    };
  }
  if (
    lowered.includes("mfa is required by policy") ||
    lowered.includes("enroll a passkey")
  ) {
    return {
      kind: "mfa-enforcement",
      message:
        "Your workspace requires multi-factor authentication. " +
        "Sign in once with your password, then enroll a passkey or authenticator app in Settings.",
      status
    };
  }
  if (
    lowered.includes("mfa") ||
    lowered.includes("authenticator") ||
    lowered.includes("invalid mfa")
  ) {
    return {
      kind: "mfa",
      message:
        detail ||
        "That code didn't match. Check your authenticator app and try again.",
      status
    };
  }
  if (
    lowered.includes("invalid") ||
    lowered.includes("credential") ||
    status === 401 ||
    detail === ""
  ) {
    return {
      kind: "invalid-credentials",
      message:
        detail ||
        "We couldn't sign you in with those details. Check your email and password and try again.",
      status
    };
  }
  return {
    kind: "generic",
    message: detail || "Something went wrong. Please try again.",
    status
  };
}
