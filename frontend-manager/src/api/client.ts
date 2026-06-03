import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production"
    ? "https://unitrans-backend.onrender.com"
    : "http://localhost:8000");

// Normalize common mistaken host to the correct backend host so deployed bundles
// that still reference the old hostname continue to work until a full rebuild.
const NORMALIZED_BASE_URL = BASE_URL.replace(
  "https://unitrans.onrender.com",
  "https://unitrans-backend.onrender.com"
);

export const client = axios.create({
  baseURL: NORMALIZED_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

if (typeof window !== "undefined") {
  console.info("[manager] API BASE_URL (raw):", BASE_URL);
  console.info("[manager] API BASE_URL (normalized):", NORMALIZED_BASE_URL);
  if (!NORMALIZED_BASE_URL.includes("unitrans-backend")) {
    console.error("[manager] WARNING: BASE_URL does not point to unitrans-backend:", NORMALIZED_BASE_URL);
  }
}

// Log login request payloads and error responses for debugging
client.interceptors.request.use((config) => {
  if (config && config.url && config.url.includes('/api/auth/login')) {
    // eslint-disable-next-line no-console
    console.info('[manager] login request payload:', config.data);
  }
  return config;
});

client.interceptors.response.use(
  (resp) => resp,
  (err) => {
    try {
      if (err?.config?.url && err.config.url.includes('/api/auth/login')) {
        // eslint-disable-next-line no-console
        console.error('[manager] login error response:', err.response?.data);
      }
    } catch (e) {
      // ignore logging errors
    }
    return Promise.reject(err);
  }
);

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
