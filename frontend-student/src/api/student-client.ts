import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "production"
    ? "https://unitrans.onrender.com"
    : "http://localhost:8000");

const NORMALIZED_BASE_URL = BASE_URL;

export const studentClient = axios.create({
  baseURL: NORMALIZED_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

studentClient.interceptors.request.use((config) => {
  return config;
});

studentClient.interceptors.response.use(
  (resp) => resp,
  (err) => Promise.reject(err)
);

// ─── Token helpers ────────────────────────────────────────────────────────────

export const getStudentAccessToken = (): string | null =>
  typeof window !== "undefined"
    ? localStorage.getItem("student_access_token")
    : null;

export const getStudentRefreshToken = (): string | null =>
  typeof window !== "undefined"
    ? localStorage.getItem("student_refresh_token")
    : null;

export const setStudentTokens = (access: string, refresh?: string) => {
  localStorage.setItem("student_access_token", access);
  if (refresh) localStorage.setItem("student_refresh_token", refresh);
};

export const clearStudentTokens = () => {
  localStorage.removeItem("student_access_token");
  localStorage.removeItem("student_refresh_token");
};

// ─── Request interceptor ─────────────────────────────────────────────────────

studentClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getStudentAccessToken();
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

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

studentClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    const refresh = getStudentRefreshToken();
    if (!refresh) {
      clearStudentTokens();
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        pendingQueue.push({ resolve, reject });
      }).then((token) => {
        if (original.headers) original.headers.Authorization = `Bearer ${token}`;
        return studentClient(original);
      });
    }

    original._retry = true;
    isRefreshing = true;

    try {
      const { data } = await axios.post<{ access: string; refresh: string }>(
        `${NORMALIZED_BASE_URL}/api/auth/token/refresh/`,
        { refresh }
      );
      setStudentTokens(data.access, data.refresh);
      processQueue(null, data.access);
      if (original.headers)
        original.headers.Authorization = `Bearer ${data.access}`;
      return studentClient(original);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearStudentTokens();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);
