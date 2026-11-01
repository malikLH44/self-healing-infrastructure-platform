
const API_BASE_URL = import.meta.env.PROD
  ? "/api"
  : "http://localhost:8000";

const TOKEN_KEY = "ship_access_token";

// Authentication

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  username: string;
  is_active: boolean;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function getAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function saveAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

async function getErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // Use the default message when the response is not JSON.
  }

  return `API error: ${response.status}`;
}

export async function login(
  username: string,
  password: string,
): Promise<TokenResponse> {
  const formData = new URLSearchParams();
  formData.set("username", username);
  formData.set("password", password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!response.ok) {
    throw new ApiError(
      await getErrorMessage(response),
      response.status,
    );
  }

  return response.json() as Promise<TokenResponse>;
}

export function getCurrentUser() {
  return fetchApi<CurrentUser>("/auth/me");
}

// Dashboard types

export interface DashboardSummary {
  services: {
    total: number;
    healthy: number;
    unhealthy: number;
  };
  incidents: {
    active: number;
    resolved: number;
    total: number;
  };
  remediations: {
    total: number;
    successful: number;
    failed: number;
    success_rate: number | null;
  };
}

export interface MonitoredService {
  name: string;
  status: string;
  http_status: number | null;
  checked_at: string | null;
  cpu_percent: number | null;
  memory_percent: number | null;
  memory_usage_bytes: number | null;
  memory_limit_bytes: number | null;
}

export interface ServicesResponse {
  services: MonitoredService[];
}

export interface RemediationAttempt {
  attempted_at: string;
  success: boolean;
  reason: string;
  service: string;
  action: string;
}

export interface Incident {
  id: string;
  service: string;
  status: string;
  first_error: string;
  last_error: string;
  http_status: number | null;
  failed_checks: number;
  detected_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  duration_seconds: number | null;
  remediation_attempts: RemediationAttempt[];
}

export interface IncidentsResponse {
  incidents: Incident[];
}

export interface ResourceAlert {
  id: string;
  service: string;
  resource: "cpu" | "memory";
  status: "open" | "resolved";
  threshold_percent: number;
  observed_percent: number;
  consecutive_checks: number;
  detected_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  duration_seconds: number | null;
}

export interface ResourceAlertsResponse {
  alerts: ResourceAlert[];
}

// Authenticated API requests

async function fetchApi<T>(path: string): Promise<T> {
  const token = getAccessToken();

  const headers: HeadersInit = {};

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      clearAccessToken();
    }

    throw new ApiError(
      await getErrorMessage(response),
      response.status,
    );
  }

  return response.json() as Promise<T>;
}

// Dashboard API functions

export function getDashboardSummary() {
  return fetchApi<DashboardSummary>("/dashboard/summary");
}

export function getServices() {
  return fetchApi<ServicesResponse>("/services");
}

export function getIncidents() {
  return fetchApi<IncidentsResponse>("/incidents");
}

export function getResourceAlerts() {
  return fetchApi<ResourceAlertsResponse>("/resource-alerts");
}

export function getActiveResourceAlerts() {
  return fetchApi<ResourceAlertsResponse>("/resource-alerts/active");
}
