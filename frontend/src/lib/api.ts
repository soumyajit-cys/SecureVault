import axios, { AxiosError } from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

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
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (typeof error.config & {
      _retried?: boolean;
    });

    const status = error.response?.status;

    if (
      status === 401 &&
      original &&
      !original._retried &&
      !original.url?.includes("/auth/login") &&
      !original.url?.includes("/auth/register")
    ) {
      original._retried = true;

      const csrf = getCsrfToken();

      if (csrf) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, null, {
            headers: { [CSRF_HEADER]: csrf },
            withCredentials: true
          });

          setAccessToken(data.access_token);

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