import axios, { AxiosError } from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

if (
  typeof import.meta.env.VITE_API_BASE === "undefined" &&
  import.meta.env.PROD
) {
  // Production builds must set VITE_API_BASE to the absolute backend
  // origin (e.g. https://securevault-api.onrender.com/api/v1). The
  // relative fallback only works behind a same-origin proxy (vite dev
  // server or equivalent) and silently breaks auth on Vercel.
  console.warn(
    "[SecureVault] VITE_API_BASE is not set; falling back to '/api/v1'. " +
      "Set VITE_API_BASE in the Vercel dashboard for production."
  );
}

/**
 * Render's free tier sleeps after ~15 min idle; the first request
 * after sleep fails at the network level (refused/reset/timeout)
 * while the instance boots (~50 s). These helpers retry such
 * failures with backoff instead of surfacing a raw error.
 *
 * Only connection-level failures (no HTTP response) are retried,
 * and only for idempotent methods plus the auth bootstrap calls
 * the app explicitly wraps — never blindly for every POST, so a
 * processed-but-unanswered mutation can't execute twice.
 */
export function isNetworkError(error: unknown): boolean {
  return (
    (axios.isAxiosError(error) && !error.response) ||
    error instanceof TypeError // fetch() network failure
  );
}

const COLD_START_DELAYS_MS = [2000, 5000, 10000, 15000, 20000];

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function notifyColdStart(
  attempt: number,
  maxAttempts: number
): void {
  window.dispatchEvent(
    new CustomEvent("api:cold-start", {
      detail: { attempt, maxAttempts }
    })
  );
}

export function notifyColdStartDone(): void {
  window.dispatchEvent(new CustomEvent("api:cold-start-done"));
}

/**
 * Run fn, retrying network errors with backoff. Returns fn's
 * result, or rethrows the last error after maxAttempts.
 */
export async function withWakeUpRetry<T>(
  fn: () => Promise<T>,
  maxAttempts = COLD_START_DELAYS_MS.length + 1,
  onAttempt?: (attempt: number, maxAttempts: number) => void
): Promise<T> {
  let lastError: unknown = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const result = await fn();
      if (attempt > 1) notifyColdStartDone();
      return result;
    } catch (error) {
      lastError = error;
      if (!isNetworkError(error) || attempt >= maxAttempts) throw error;
      notifyColdStart(attempt, maxAttempts);
      onAttempt?.(attempt, maxAttempts);
      await sleep(COLD_START_DELAYS_MS[attempt - 1] ?? 20000);
    }
  }
  throw lastError;
}

/**
 * The access token lives in memory only; it is never
 * written to localStorage or sessionStorage so an XSS
 * payload cannot read it later. The refresh token stays
 * in an HttpOnly cookie managed by the server. The CSRF
 * token is likewise kept in memory: same-origin it could
 * be read from the readable cookie, but cross-origin
 * (Vercel -> Render) document.cookie never sees the
 * backend's cookies, so the server also delivers the token
 * in auth JSON bodies and the client captures it here.
 */
let accessToken: string | null = null;

let csrfToken: string | null = null;

const CSRF_COOKIE = "sv_csrf";
const CSRF_HEADER = "X-CSRF-Token";

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function getCsrfToken(): string | null {
  if (csrfToken) return csrfToken;
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${CSRF_COOKIE}=([^;]*)`)
  );
  return match ? decodeURIComponent(match[1]) : null;
}

/**
 * Fetch the current CSRF token from the server (holder of
 * the refresh cookie only). Needed after a page reload
 * cross-origin, when memory is empty and the cookie is
 * unreadable from JS.
 */
export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const { data } = await axios.get(`${API_BASE}/auth/csrf`, {
      withCredentials: true
    });
    const token =
      (data as { csrf_token?: unknown } | undefined)?.csrf_token;
    if (typeof token === "string" && token) {
      csrfToken = token;
      return token;
    }
  } catch {
    // No cookie / not authenticated: caller treats null
    // as "no session to refresh".
  }
  return null;
}

/**
 * Memory token if present, else cookie (same-origin dev),
 * else a server round-trip (cross-origin reload).
 */
export async function ensureCsrfToken(): Promise<string | null> {
  return getCsrfToken() ?? fetchCsrfToken();
}

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true
});

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    // Every token-issuing response carries the CSRF token in
    // its body (login, MFA verify, passkey, refresh). Capture
    // it globally so no caller has to remember.
    const token = (
      response.data as { csrf_token?: unknown } | undefined
    )?.csrf_token;
    if (typeof token === "string" && token) {
      csrfToken = token;
    }
    return response;
  },
  async (error: AxiosError) => {
    const original = error.config as (typeof error.config & {
      _retried?: boolean;
      _coldRetried?: boolean;
    });

    // Cold-start / unreachable server: retry idempotent reads
    // with backoff. Mutations are left to their callers (login
    // and session-restore opt in explicitly via withWakeUpRetry)
    // so a processed-but-unanswered write can't run twice.
    if (
      !error.response &&
      original &&
      !original._coldRetried &&
      ["get", "head", "options", "delete"].includes(
        (original.method ?? "get").toLowerCase()
      )
    ) {
      original._coldRetried = true;
      try {
        return await withWakeUpRetry(() => api(original));
      } catch (retryError) {
        return Promise.reject(retryError);
      }
    }

    const status = error.response?.status;

    if (
      status === 401 &&
      original &&
      !original._retried &&
      !original.url?.includes("/auth/login") &&
      !original.url?.includes("/auth/register")
    ) {
      original._retried = true;

      const csrf = getCsrfToken() ?? (await fetchCsrfToken());

      if (csrf) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, null, {
            headers: { [CSRF_HEADER]: csrf },
            withCredentials: true
          });

          setAccessToken(data.access_token);

          if (typeof data.csrf_token === "string" && data.csrf_token) {
            setCsrfToken(data.csrf_token);
          }

          original.headers.Authorization = `Bearer ${data.access_token}`;

          return api(original);
        } catch {
          setAccessToken(null);
          window.dispatchEvent(new CustomEvent("auth:logout"));
        }
      }
    }

    return Promise.reject(error);
  }
);

export function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data as { detail?: string } | undefined;
    if (detail?.detail) {
      return detail.detail;
    }
    return error.message;
  }
  return "An unexpected error occurred.";
}

export function extractDetail(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string | Array<{ msg?: string; code?: string }> }
      | undefined;
    if (typeof data?.detail === "string") {
      return data.detail;
    }
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      const first = data.detail[0];
      if (first?.msg) return first.msg;
      if (first?.code) return `Error code: ${first.code}`;
    }
  }
  return errorMessage(error);
}

export default api;