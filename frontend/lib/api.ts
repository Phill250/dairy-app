const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";


export type UserRole = "farmer" | "admin";
export type BreedType = "holstein_friesian" | "ankole" | "ankole_friesian_cross" | "other";

export interface UserRead {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: UserRole;
}

export interface CowRead {
  id: string;
  farmer_id: string;
  name: string;
  breed: BreedType;
  created_at: string | null;
}

export interface CowCreatePayload {
  name: string;
  breed: BreedType;
}

export interface LogRead {
  id: string;
  cow_id: string;
  date: string;
  feed: number;
  milking_times: number;
  total_milk: number;
  status: string;
  color: string;
  advice: string;
  predicted_yield: number | null;
  used_ml_model: boolean;
  created_at: string | null;
}

export interface LogCreatePayload {
  cow_id: string;
  date: string;
  feed: number;
  milkingTimes: number;
  milkings: number[];
}

export interface PredictionResponse {
  expected_yield: number;
  model_used: boolean;
}

export interface MetricsRead {
  total_farmers: number;
  total_cows: number;
  total_logs: number;
  average_total_milk: number | null;
  average_feed: number | null;
  average_predicted_yield: number | null;
  ml_model_usage_rate: number;
  status_breakdown: Record<string, number>;
}


const ACCESS_TOKEN_KEY = "dairy_access_token";
const REFRESH_TOKEN_KEY = "dairy_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}


async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  _isRetry = false
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401 && !_isRetry) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return apiFetch<T>(path, options, true); // retry exactly once
    }
    clearTokens();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Session expired");
  }

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }

  if (res.status === 204) return undefined as T; // no-content responses (delete, logout)
  return res.json() as Promise<T>;
}

async function tryRefresh(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}


export async function registerFarmer(payload: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}): Promise<UserRead> {
  return apiFetch<UserRead>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(email: string, password: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Login failed: ${body}`);
  }
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken();
  clearTokens();
  if (refreshToken) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
    }
  }
}

export async function getMe(): Promise<UserRead> {
  return apiFetch<UserRead>("/api/users/me");
}


export async function fetchCows(): Promise<CowRead[]> {
  return apiFetch<CowRead[]>("/api/cows");
}

export async function createCow(payload: CowCreatePayload): Promise<CowRead> {
  return apiFetch<CowRead>("/api/cows", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}


export async function fetchLogs(): Promise<LogRead[]> {
  return apiFetch<LogRead[]>("/api/logs");
}

export async function createLog(payload: LogCreatePayload): Promise<LogRead> {
  return apiFetch<LogRead>("/api/logs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteLog(id: string): Promise<void> {
  return apiFetch<void>(`/api/logs/${id}`, { method: "DELETE" });
}

export async function predictYield(
  cow_id: string,
  feed: number,
  milking_times: number
): Promise<PredictionResponse> {
  return apiFetch<PredictionResponse>("/api/logs/predict", {
    method: "POST",
    body: JSON.stringify({ cow_id, feed, milking_times }),
  });
}


export async function fetchAdminMetrics(): Promise<MetricsRead> {
  return apiFetch<MetricsRead>("/api/admin/metrics");
}

export interface AdminUserSummary {
  id: string;
  created_at: string | null;
  cow_count: number;
  log_count: number;
}

export async function fetchAdminUsers(): Promise<AdminUserSummary[]> {
  return apiFetch<AdminUserSummary[]>("/api/admin/users");
}

export async function forgotPassword(email: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (res.status === 429) throw new Error("rate_limited");
  if (!res.ok) throw new Error("request_failed");
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!res.ok) throw new Error("Reset failed");
}