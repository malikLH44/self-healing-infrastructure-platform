
from datetime import datetime

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

REGISTRY = CollectorRegistry()

# HTTP instrumentation
HTTP_REQUESTS = Counter(
    "ship_http_requests_total",
    "Total HTTP requests handled by SHIP API.",
    ["method", "path", "status"],
    registry=REGISTRY,
)

HTTP_REQUEST_DURATION = Histogram(
    "ship_http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ["method", "path"],
    registry=REGISTRY,
)

# Service monitoring
SERVICE_UP = Gauge(
    "ship_service_up",
    "Whether a monitored service is healthy (1) or unhealthy (0).",
    ["service"],
    registry=REGISTRY,
)

SERVICE_CPU = Gauge(
    "ship_service_cpu_percent",
    "Container CPU usage percentage.",
    ["service"],
    registry=REGISTRY,
)

SERVICE_MEMORY = Gauge(
    "ship_service_memory_percent",
    "Container memory usage percentage.",
    ["service"],
    registry=REGISTRY,
)

SERVICE_LAST_CHECK = Gauge(
    "ship_service_last_check_timestamp_seconds",
    "Unix timestamp of the last service health check.",
    ["service"],
    registry=REGISTRY,
)

SERVICES = Gauge(
    "ship_services",
    "Current number of monitored services by status.",
    ["status"],
    registry=REGISTRY,
)

# Incidents and remediation
INCIDENTS = Gauge(
    "ship_incidents",
    "Current number of incidents by status.",
    ["status"],
    registry=REGISTRY,
)

REMEDIATION_ATTEMPTS = Gauge(
    "ship_remediation_attempts",
    "Recorded remediation attempts by outcome.",
    ["result"],
    registry=REGISTRY,
)

# Resource alerts
RESOURCE_ALERTS = Gauge(
    "ship_resource_alerts",
    "Recorded resource alerts by resource and status.",
    ["resource", "status"],
    registry=REGISTRY,
)


def record_http_request(
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    HTTP_REQUESTS.labels(
        method=method,
        path=path,
        status=str(status_code),
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=method,
        path=path,
    ).observe(duration_seconds)


def _parse_timestamp(value: str | None) -> float:
    if not value:
        return float("nan")

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).timestamp()
    except (TypeError, ValueError):
        return float("nan")


def refresh_ship_metrics(
    services: list[dict],
    incidents: list[dict],
    alerts: list[dict],
) -> None:
    """Refresh gauges using the current SHIP monitoring state."""

    healthy_services = sum(
        1 for service in services
        if service.get("status") == "healthy"
    )

    SERVICES.labels(status="total").set(len(services))
    SERVICES.labels(status="healthy").set(healthy_services)
    SERVICES.labels(status="unhealthy").set(
        len(services) - healthy_services
    )

    for service in services:
        name = service.get("name")

        if not name:
            continue

        SERVICE_UP.labels(service=name).set(
            1 if service.get("status") == "healthy" else 0
        )

        cpu = service.get("cpu_percent")
        memory = service.get("memory_percent")

        SERVICE_CPU.labels(service=name).set(
            cpu if cpu is not None else float("nan")
        )

        SERVICE_MEMORY.labels(service=name).set(
            memory if memory is not None else float("nan")
        )

        SERVICE_LAST_CHECK.labels(service=name).set(
            _parse_timestamp(service.get("checked_at"))
        )

    incident_counts = {
        "open": 0,
        "resolved": 0,
    }

    for incident in incidents:
        status = incident.get("status")
        if status in incident_counts:
            incident_counts[status] += 1

    INCIDENTS.labels(status="open").set(incident_counts["open"])
    INCIDENTS.labels(status="resolved").set(incident_counts["resolved"])
    INCIDENTS.labels(status="total").set(len(incidents))

    remediation_counts = {
        "success": 0,
        "failed": 0,
    }

    for incident in incidents:
        for attempt in incident.get("remediation_attempts", []):
            result = "success" if attempt.get("success") else "failed"
            remediation_counts[result] += 1

    REMEDIATION_ATTEMPTS.labels(result="success").set(
        remediation_counts["success"]
    )
    REMEDIATION_ATTEMPTS.labels(result="failed").set(
        remediation_counts["failed"]
    )

    alert_counts = {
        ("cpu", "open"): 0,
        ("cpu", "resolved"): 0,
        ("memory", "open"): 0,
        ("memory", "resolved"): 0,
    }

    for alert in alerts:
        key = (alert.get("resource"), alert.get("status"))

        if key in alert_counts:
            alert_counts[key] += 1

    for (resource, status), count in alert_counts.items():
        RESOURCE_ALERTS.labels(
            resource=resource,
            status=status,
        ).set(count)


def generate_metrics() -> bytes:
    return generate_latest(REGISTRY)
