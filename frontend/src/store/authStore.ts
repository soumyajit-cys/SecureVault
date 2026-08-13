import { create } from "zustand";

import type { User } from "@/types";
import { getAccessToken, setAccessToken, getCsrfToken, API_BASE } from "@/lib/api";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setTokens: (access: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: getAccessToken() !== null,

  setTokens: (access) => {
    setAccessToken(access);
    set({ isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    setAccessToken(null);
    set({ user: null, isAuthenticated: false });

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
  }
}));