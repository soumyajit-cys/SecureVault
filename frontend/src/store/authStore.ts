import { create } from "zustand";

import type { User } from "@/types";
import { getAccessToken, setAccessToken, getCsrfToken, API_BASE } from "@/lib/api";

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
 * HttpOnly cookie when one exists.
 */
function refreshSilently(): Promise<string | null> {
  const csrf = getCsrfToken();
  if (!csrf) return Promise.resolve(null);

  return fetch(`${API_BASE}/auth/refresh`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrf }
  })
    .then((res) => (res.ok ? res.json() : null))
    .then((body) => (body?.access_token ? body.access_token : null))
    .catch(() => null);
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
    set({ user: null, isAuthenticated: false, sessionChecked: true });

    // Best-effort server-side revocation of the
    // HttpOnly refresh cookie + token family. The
    // CSRF double-submit header protects the call.
    const csrf = getCsrfToken();
    if (csrf) {
      void fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": csrf }
      }).catch(() => {});
    }
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

    set({ isAuthenticated: token !== null, sessionChecked: true });
  }
}));