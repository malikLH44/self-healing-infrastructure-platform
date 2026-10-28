
from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp)


class IncidentManager:
    def __init__(self) -> None:
        self._incidents: dict[str, dict] = {}
        self._active_by_service: dict[str, str] = {}

    def observe(self, result: dict) -> dict | None:
        service_name = result["name"]
        status = result["status"]
        observed_at = result.get("checked_at", utc_now())

        active_id = self._active_by_service.get(service_name)

        if status != "healthy":
            if active_id is None:
                incident_id = str(uuid4())

                incident = {
                    "id": incident_id,
                    "service": service_name,
                    "status": "open",
                    "first_error": result.get("error"),
                    "last_error": result.get("error"),
                    "http_status": result.get("http_status"),
                    "failed_checks": 1,
                    "detected_at": observed_at,
                    "last_seen_at": observed_at,
                    "resolved_at": None,
                    "duration_seconds": None,
                    "remediation_attempts": [],
                }

                self._incidents[incident_id] = incident
                self._active_by_service[service_name] = incident_id

            else:
                incident = self._incidents[active_id]
                incident["failed_checks"] += 1
                incident["last_seen_at"] = observed_at
                incident["last_error"] = result.get("error")
                incident["http_status"] = result.get("http_status")

            return incident.copy()

        if active_id is not None:
            incident = self._incidents[active_id]
            incident["status"] = "resolved"
            incident["resolved_at"] = observed_at

            detected_at = parse_timestamp(incident["detected_at"])
            resolved_at = parse_timestamp(observed_at)

            incident["duration_seconds"] = round(
                max(0.0, (resolved_at - detected_at).total_seconds()),
                2,
            )

            del self._active_by_service[service_name]
            return incident.copy()

        return None


    def record_remediation(
        self,
        incident_id: str,
        result: dict,
    ) -> dict:
        incident = self._incidents.get(incident_id)

        if incident is None:
            raise KeyError(f"Unknown incident: {incident_id}")

        attempt = {
            "attempted_at": utc_now(),
            "success": bool(result.get("success", False)),
            "reason": result.get("reason", "unknown"),
            "service": result.get("service", incident["service"]),
            "action": result.get("action", "restart"),
        }

        incident.setdefault("remediation_attempts", []).append(attempt)

        return attempt.copy()


    def list_incidents(self) -> list[dict]:
        return [incident.copy() for incident in self._incidents.values()]

    def get_active_incidents(self) -> list[dict]:
        return [
            incident.copy()
            for incident in self._incidents.values()
            if incident["status"] == "open"
        ]


incident_manager = IncidentManager()
