import axios, { AxiosError } from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export const TOKEN_STORAGE_KEY = "securevault_access_token";
export const REFRESH_STORAGE_KEY = "securevault_refresh_token";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json"
  }
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
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

      const refreshToken = localStorage.getItem(REFRESH_STORAGE_KEY);

      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken
          });

          localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
          localStorage.setItem(REFRESH_STORAGE_KEY, data.refresh_token);

          original.headers.Authorization = `Bearer ${data.access_token}`;

          return api(original);
        } catch {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
          localStorage.removeItem(REFRESH_STORAGE_KEY);
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