import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production"
    ? "https://unitrans.onrender.com"
    : "http://localhost:8000");

// No normalization needed - use backend URL directly.
const NORMALIZED_BASE_URL = BASE_URL;

export const client = axios.create({
  baseURL: NORMALIZED_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Log login request payloads and error responses for debugging
// (No-op logging interceptor removed to avoid duplicate response handlers.)

// ─── Token helpers ────────────────────────────────────────────────────────────

const getAccessToken = (): string | null =>
  typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

const getRefreshToken = (): string | null =>
  typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;

const setTokens = (access: string, refresh?: string) => {
  localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
};

const clearTokens = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
};

// ─── Request interceptor — attach Bearer token ────────────────────────────────

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── Response interceptor — silent token refresh on 401 ──────────────────────

let isRefreshing = false;
let pendingQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (err: unknown, token: string | null) => {
  pendingQueue.forEach(({ resolve, reject }) =>
    err ? reject(err) : resolve(token!)
  );
  pendingQueue = [];
};

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    const refresh = getRefreshToken();
    if (!refresh) {
      clearTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      }).then((token) => {
        if (original.headers) original.headers.Authorization = `Bearer ${token}`;
        return client(original);
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post<{ access: string; refresh: string }>(
        `${NORMALIZED_BASE_URL}/api/auth/token/refresh/`,
        { refresh }
      );
      setTokens(data.access, data.refresh);
      processQueue(null, data.access);
      if (original.headers)
        original.headers.Authorization = `Bearer ${data.access}`;
      return client(original);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearTokens();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export { setTokens, clearTokens, getAccessToken };
