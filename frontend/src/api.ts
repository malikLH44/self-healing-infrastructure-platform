const API_BASE_URL = import.meta.env.PROD
  ? "/api"
  : "http://localhost:8000";

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
}

export interface ServicesResponse {
  services: MonitoredService[];
}

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function getDashboardSummary() {
  return fetchApi<DashboardSummary>("/dashboard/summary");
}

export function getServices() {
  return fetchApi<ServicesResponse>("/services");
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

export function getIncidents() {
  return fetchApi<IncidentsResponse>("/incidents");
}
