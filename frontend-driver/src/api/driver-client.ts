import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production"
    ? "https://unitrans-backend.onrender.com"
    : "http://localhost:8000");

const NORMALIZED_BASE_URL = BASE_URL.replace(
  "https://unitrans.onrender.com",
  "https://unitrans-backend.onrender.com"
);

export const driverClient = axios.create({
  baseURL: NORMALIZED_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

if (typeof window !== "undefined") {
  console.info("[driver] API BASE_URL (raw):", BASE_URL);
  console.info("[driver] API BASE_URL (normalized):", NORMALIZED_BASE_URL);
  if (!NORMALIZED_BASE_URL.includes("unitrans-backend")) {
    console.error("[driver] WARNING: BASE_URL does not point to unitrans-backend:", NORMALIZED_BASE_URL);
  }
}

driverClient.interceptors.request.use((config) => {
  if (config && config.url && config.url.includes('/api/auth/login')) {
    console.info('[driver] login request payload:', config.data);
  }
  return config;
});

driverClient.interceptors.response.use(
  (resp) => resp,
  (err) => {
    try {
      if (err?.config?.url && err.config.url.includes('/api/auth/login')) {
        console.error('[driver] login error response:', err.response?.data);
      }
    } catch (e) {}
    return Promise.reject(err);
  }
);

export const getDriverAccessToken = (): string | null =>
  typeof window !== "undefined"
    ? localStorage.getItem("driver_access_token")
    : null;

export const getDriverRefreshToken = (): string | null =>
  typeof window !== "undefined"
    ? localStorage.getItem("driver_refresh_token")
    : null;

export const setDriverTokens = (access: string, refresh?: string) => {
  localStorage.setItem("driver_access_token", access);
  if (refresh) localStorage.setItem("driver_refresh_token", refresh);
};

export const clearDriverTokens = () => {
  localStorage.removeItem("driver_access_token");
  localStorage.removeItem("driver_refresh_token");
};

driverClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getDriverAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

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

driverClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    const refresh = getDriverRefreshToken();
    if (!refresh) {
      clearDriverTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      }).then((token) => {
        if (original.headers) original.headers.Authorization = `Bearer ${token}`;
        return driverClient(original);
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post<{ access: string; refresh: string }>(
        `${NORMALIZED_BASE_URL}/api/auth/token/refresh/`,
        { refresh }
      );
      setDriverTokens(data.access, data.refresh);
      processQueue(null, data.access);
      if (original.headers)
        original.headers.Authorization = `Bearer ${data.access}`;
      return driverClient(original);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearDriverTokens();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
