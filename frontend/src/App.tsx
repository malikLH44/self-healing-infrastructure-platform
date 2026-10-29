
import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  ChevronDown,
  Clock3,
  LayoutDashboard,
  Network,
  RefreshCw,
  Server,
  Settings,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";
import "./App.css";

import { useCallback, useEffect, useState } from "react";
import {
  getDashboardSummary,
  getServices,
  getIncidents,
  type DashboardSummary,
  type MonitoredService,
  type Incident,
} from "./api";



function App() {
  const [incidents, setIncidents] = useState<Incident[]>([]);

    const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [services, setServices] = useState<MonitoredService[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);


const loadDashboard = useCallback(async () => {
  try {
    const [summaryData, servicesData, incidentsData] = await Promise.all([
      getDashboardSummary(),
      getServices(),
      getIncidents(),
    ]);

    setSummary(summaryData);
    setServices(servicesData.services);
    setIncidents(incidentsData.incidents);
    setLastUpdated(new Date());
    setError(null);
  } catch (err) {
    setError(
      err instanceof Error
        ? err.message
        : "Unable to connect to the SHIP API.",
    );
  } finally {
    setLoading(false);
  }
}, []);


  useEffect(() => {
    void loadDashboard();

    const interval = window.setInterval(() => {
      void loadDashboard();
    }, 15000);

    return () => window.clearInterval(interval);
  }, [loadDashboard]);


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={23} />
          </div>
          <div>
            <h1>SHIP</h1>
            <span>Infrastructure Control</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <nav className="navigation">
          <a className="nav-item active" href="#overview">
            <LayoutDashboard size={18} />
            Overview
          </a>
          <a className="nav-item" href="#services">
            <Server size={18} />
            Services
          </a>

            <a className="nav-item" href="#incidents">
              <AlertTriangle size={18} />
              Incidents
              <span className="nav-count">
                {summary ? summary.incidents.active : "—"}
              </span>
            </a>

          <a className="nav-item" href="#remediations">
            <Zap size={18} />
            Remediations
          </a>
        </nav>

        <div className="nav-label system-label">SYSTEM</div>
        <nav className="navigation">
          <a className="nav-item" href="#infrastructure">
            <Network size={18} />
            Infrastructure
          </a>
          <a className="nav-item" href="#logs">
            <Terminal size={18} />
            Activity logs
          </a>
          <a className="nav-item" href="#settings">
            <Settings size={18} />
            Settings
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="controller-status">
            <span className="status-dot" />
            <div>
              <strong>Controller online</strong>
              <span>Monitoring active</span>
            </div>
          </div>
          <div className="user-profile">
            <div className="avatar">MK</div>
            <div className="profile-info">
              <strong>SHIP Admin</strong>
              <span>Infrastructure operator</span>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>Overview</strong>
          </div>
          <div className="topbar-right">
            <span className="environment">
              <span className="status-dot" />
              LOCAL ENVIRONMENT
            </span>

        <button
          className="icon-button"
          aria-label="Refresh dashboard"
          onClick={() => void loadDashboard()}
          title="Refresh dashboard"
        >
          <RefreshCw size={17} />
        </button>

            <div className="avatar small-avatar">MK</div>
          </div>
        </header>

        <section className="page-heading">
          <div>
            <div className="eyebrow">
              <Activity size={14} /> INFRASTRUCTURE MONITORING
            </div>
            <h2>System overview</h2>
            <p>Monitor service health, incidents and automated recovery.</p>
          </div>

        <div className="updated-label">
          <Clock3 size={15} />
          {lastUpdated
            ? `Last updated: ${lastUpdated.toLocaleTimeString()}`
            : "Waiting for data..."}
        </div>

        </section>

        {loading && (
          <div className="api-notice">Loading SHIP metrics...</div>
        )}

        {error && (
          <div className="api-error" role="alert">
            API connection error: {error}
            <button onClick={() => void loadDashboard()}>
              Retry
            </button>
          </div>
        )}
        <section className="system-banner">
          <div className="banner-icon">
            <ShieldCheck size={23} />
          </div>

<div className="banner-copy">
  <strong>
    {loading
  ? "Loading service status..."
  : error
    ? "Unable to refresh infrastructure status"
    : !summary || summary.services.total === 0
      ? "No monitored services configured"
      : summary.services.unhealthy > 0
        ? "Some monitored services require attention"
        : "All monitored services are operational"}
  </strong>
  <span>
    {error
      ? "The API could not be reached. Check the backend and retry."
      : "Service health and recovery metrics from the SHIP controller."}
  </span>
</div>


        <span className="banner-badge">
          <span className="status-dot" />
          {loading
            ? "CHECKING"
            : error
              ? "API UNAVAILABLE"
              : !summary || summary.services.total === 0
                ? "NO SERVICES"
                : summary.services.unhealthy > 0
                  ? "ATTENTION REQUIRED"
                  : "SYSTEM HEALTHY"}
        </span>

        </section>

        <section className="section-heading">
          <div>
            <h3>Performance overview</h3>
            <p>Key infrastructure indicators</p>
          </div>
          <span className="period-label">CURRENT STATUS</span>
        </section>

        <section className="metrics-grid">
          <article className="metric-card">
            <div className="metric-top">
              <span>Total services</span>
              <div className="metric-icon neutral">
                <Server size={18} />
              </div>
            </div>
            <div className="metric-value">{summary ? String(summary.services.total).padStart(2, "0") : "—"}</div>
            <div className="metric-footer">
              <span className="muted">Configured services</span>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span>Healthy services</span>
              <div className="metric-icon green">
                <CheckCircle2 size={18} />
              </div>
            </div>
            <div className="metric-value">{summary ? String(summary.services.healthy).padStart(2, "0") : "—"}</div>
            <div className="metric-footer">
              <span className="positive">
                <ArrowUpRight size={14} /> {summary && summary.services.total > 0
                    ? `${Math.round(
                        (summary.services.healthy / summary.services.total) * 100,
                      )}%`
                    : "—"}
              </span>
              <span className="muted">Service availability</span>
            </div>
          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span>Active incidents</span>
              <div className="metric-icon red">
                <AlertTriangle size={18} />
              </div>
            </div>
            <div className="metric-value">{summary ? String(summary.incidents.active).padStart(2, "0") : "—"}</div>

<div className="metric-footer">
  <span
    className={
      summary?.incidents.active
        ? "negative"
        : "positive"
    }
  >
    {summary
      ? summary.incidents.active === 0
        ? "No active alerts"
        : `${summary.incidents.active} active alert${
            summary.incidents.active !== 1 ? "s" : ""
          }`
      : "Loading incidents..."}
  </span>
</div>

          </article>

          <article className="metric-card">
            <div className="metric-top">
              <span>Remediation success</span>
              <div className="metric-icon blue">
                <Zap size={18} />
              </div>
            </div>

         <div className="metric-value">
          {summary?.remediations.success_rate != null
            ? `${summary.remediations.success_rate}%`
            : "—"}
         </div>

            <div className="metric-footer">
              <span className="positive">
                <ArrowUpRight size={14} />  {summary ? `${summary.remediations.successful} successful` : "—"}
              </span>
              <span className="muted">Recorded attempts</span>
            </div>
          </article>
        </section>

        <section className="content-grid">
          <article className="panel services-panel" id="services">
            <div className="panel-header">
              <div>
                <h3>Monitored services</h3>
                <p>Health and availability at a glance</p>
              </div>
              <button className="text-button">
                View all <ArrowUpRight size={14} />
              </button>
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>SERVICE</th>
                    <th>STATUS</th>
                    <th>LATENCY</th>
                    <th>LAST CHECK</th>
                  </tr>
                </thead>
                <tbody>
                  {services.map((service) => (
                    <tr key={service.name}>
                      <td>
                        <div className="service-name">
                          <div className="service-icon">
                            <Server size={17} />
                          </div>
                          <div>
                            <strong>{service.name}</strong>
                            <span>Monitored HTTP service</span>
                          </div>
                        </div>
                      </td>
                      <td>

                      <span
                        className={`status-pill ${
                          service.status.toLowerCase() === "healthy"
                            ? "healthy"
                            : "unhealthy"
                        }`}
                      >
                        <span className="status-dot" />
                        {service.status}
                      </span>

                      </td>
                      <td className="latency">—</td>
                      <td className="muted">
                              {service.checked_at
                                ? new Date(service.checked_at).toLocaleTimeString()
                                : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="panel-footer">
             <span>
  <span className="status-dot" />
  {services.length} service{services.length !== 1 ? "s" : ""} monitored
</span>
            </div>
          </article>

          <article className="panel recovery-panel" id="remediations">
            <div className="panel-header">
              <div>
                <h3>Recovery performance</h3>
                <p>Automated remediation summary</p>
              </div>
              <div className="metric-icon green">
                <Activity size={18} />
              </div>
            </div>


<div className="recovery-score">
  <div>
    <span className="muted">Success rate</span>
    <div className="score-value">
      {summary?.remediations.success_rate != null
        ? `${summary.remediations.success_rate}%`
        : "—"}
    </div>
  </div>
  <span className="score-tag">
    {summary
      ? summary.remediations.total === 0
        ? "No attempts yet"
        : `${summary.remediations.total} recorded`
      : "Loading..."}
  </span>
</div>

<div className="progress-track">
  <div
    className="progress-fill"
    style={{
      width: `${Math.min(
        100,
        Math.max(0, summary?.remediations.success_rate ?? 0),
      )}%`,
    }}
  />
</div>

<div className="recovery-stats">
  <div>
    <span className="stat-indicator green-indicator" />
    <span>Successful</span>
    <strong>{summary?.remediations.successful ?? "—"}</strong>
  </div>
  <div>
    <span className="stat-indicator red-indicator" />
    <span>Failed</span>
    <strong>{summary?.remediations.failed ?? "—"}</strong>
  </div>
</div>

<div className="recovery-note">
  <CheckCircle2 size={16} />
  <span>
    {!summary
      ? "Loading remediation data..."
      : summary.remediations.total === 0
        ? "No remediation attempts have been recorded yet."
        : `${summary.remediations.successful} successful and ${summary.remediations.failed} failed attempts recorded.`}
  </span>
</div>

          </article>
        </section>

        <section className="panel incidents-panel" id="incidents">
          <div className="panel-header">
            <div>
              <h3>Recent incidents</h3>
              <p>Detection and recovery history</p>
            </div>
            <button className="text-button">
              Incident history <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>INCIDENT</th>
                  <th>SERVICE</th>
                  <th>EVENT</th>
                  <th>REMEDIATION</th>
                  <th>STATUS</th>
                  <th>TIME</th>
                </tr>
              </thead>

<tbody>
  {incidents.length === 0 ? (
    <tr>
      <td colSpan={6} className="muted">
        No incidents recorded.
      </td>
    </tr>
  ) : (
    incidents.map((incident) => {
      const recovered = incident.remediation_attempts.some(
        (attempt) => attempt.success,
      );
      const resolved = incident.status === "resolved";

      return (
        <tr key={incident.id}>
          <td className="incident-id">
            #{incident.id.slice(0, 8)}
          </td>
          <td>{incident.service}</td>
          <td>
            {resolved
              ? recovered
                ? "Recovered after remediation"
                : "Service recovered"
              : incident.last_error || "Health check failed"}
          </td>
          <td>
            <span
              className={
                recovered
                  ? "severity-medium"
                  : incident.remediation_attempts.length > 0
                    ? "severity-high"
                    : "severity-medium"
              }
            >
              {recovered
                ? "Succeeded"
                : incident.remediation_attempts.length > 0
                  ? "Failed"
                  : "Not attempted"}
            </span>
          </td>
          <td>
            <span
              className={`status-pill ${
                resolved ? "healthy" : "unhealthy"
              }`}
            >
              {resolved ? (
                <CheckCircle2 size={13} />
              ) : (
                <ArrowDownRight size={13} />
              )}
              {incident.status}
            </span>
          </td>
          <td className="muted">
            {new Date(incident.detected_at).toLocaleString()}
          </td>
        </tr>
      );
    })
  )}
</tbody>

            </table>
          </div>
        </section>

        <footer className="page-footer">
          <span>SHIP <span className="footer-divider">/</span> Self-Healing Infrastructure Platform</span>
          <span><span className="status-dot" /> Controller connected locally</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
