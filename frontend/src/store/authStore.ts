import { create } from "zustand";

import type { User } from "@/types";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  setTokens: (access: string, refresh: string) => void;
  setUser: (user: User | null) => void;
  logout: () => void;
}

function readStored(): string | null {
  return localStorage.getItem("securevault_access_token");
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: readStored() !== null,

  setTokens: (access, refresh) => {
    localStorage.setItem("securevault_access_token", access);
    localStorage.setItem("securevault_refresh_token", refresh);
    set({ isAuthenticated: true });
  },

  setUser: (user) => set({ user }),

  logout: () => {
    localStorage.removeItem("securevault_access_token");
    localStorage.removeItem("securevault_refresh_token");
    set({ user: null, isAuthenticated: false });
  }
}));