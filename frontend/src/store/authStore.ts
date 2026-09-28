import { create } from "zustand";

import type { User } from "@/types";
import {
  ensureCsrfToken,
  getAccessToken,
  setAccessToken,
  setCsrfToken,
  API_BASE
} from "@/lib/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  sessionChecked: boolean;
  setTokens: (access: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
  restoreSession: () => Promise<void>;
}

/**
 * Tries to re-establish a session after a page reload.
 * The access token lives only in memory, so on startup
 * we hit an authenticated endpoint; the API client's
 * 401 interceptor transparently refreshes through the
 * HttpOnly cookie when one exists. The CSRF header comes
 * from memory, the readable cookie (same-origin dev), or
 * the /auth/csrf bootstrap (cross-origin reload) — and the
 * refresh response rotates it, captured here for next time.
 */
async function refreshSilently(): Promise<string | null> {
  const csrf = await ensureCsrfToken();
  if (!csrf) return null;

  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRF-Token": csrf }
    });
    if (!res.ok) return null;
    const body = (await res.json()) as {
      access_token?: unknown;
      csrf_token?: unknown;
    };
    if (typeof body.csrf_token === "string" && body.csrf_token) {
      setCsrfToken(body.csrf_token);
    }
    return typeof body.access_token === "string" ? body.access_token : null;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: getAccessToken() !== null,
  sessionChecked: false,

  setTokens: (access) => {
    setAccessToken(access);
    set({ isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    setAccessToken(null);
    setCsrfToken(null);
    set({ user: null, isAuthenticated: false, sessionChecked: true });

    // Best-effort server-side revocation of the
    // HttpOnly refresh cookie + token family. The
    // CSRF double-submit header protects the call.
    // ensureCsrfToken is async: fire-and-forget is fine here
    // because logout already cleared local state.
    void ensureCsrfToken().then((csrf) => {
      if (!csrf) return;
      return fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": csrf }
      }).catch(() => {});
    });
  },

  restoreSession: async () => {
    if (getAccessToken() !== null) {
      set({ sessionChecked: true });
      return;
    }

    const token = await refreshSilently();

    if (token) {
      setAccessToken(token);
    }

    let user: User | null = null;

    if (token) {
      try {
        const res = await fetch(`${API_BASE}/profile/me`, {
          credentials: "include",
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        user = res.ok ? ((await res.json()) as User) : null;
      } catch {
        user = null;
      }
    }

    set({
      user,
      isAuthenticated: token !== null,
      sessionChecked: true
    });
  }
}));