
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.database import SessionLocal
from app.models import Incident, RemediationAttempt


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(timestamp: str | datetime) -> datetime:
    if isinstance(timestamp, datetime):
        value = timestamp
    else:
        value = datetime.fromisoformat(timestamp)

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value


def incident_to_dict(incident: Incident) -> dict:
    return {
        "id": incident.id,
        "service": incident.service,
        "status": incident.status,
        "first_error": incident.first_error,
        "last_error": incident.last_error,
        "http_status": incident.http_status,
        "failed_checks": incident.failed_checks,
        "detected_at": incident.detected_at.isoformat(),
        "last_seen_at": incident.last_seen_at.isoformat(),
        "resolved_at": (
            incident.resolved_at.isoformat()
            if incident.resolved_at is not None
            else None
        ),
        "duration_seconds": incident.duration_seconds,
        "remediation_attempts": [
            {
                "attempted_at": attempt.attempted_at.isoformat(),
                "success": attempt.success,
                "reason": attempt.reason,
                "service": attempt.service,
                "action": attempt.action,
            }
            for attempt in incident.remediation_attempts
        ],
    }


class IncidentManager:
    def __init__(self, session_factory=None) -> None:
        self._session_factory = session_factory
        self._incidents: dict[str, dict] = {}
        self._active_by_service: dict[str, str] = {}

    def _observe_db(self, result: dict) -> dict | None:
        service_name = result["name"]
        status = result["status"]
        observed_at = parse_timestamp(result.get("checked_at", utc_now()))

        with self._session_factory() as session:
            incident = session.scalar(
                select(Incident).where(
                    Incident.service == service_name,
                    Incident.status == "open",
                )
            )

            if status != "healthy":
                if incident is None:
                    incident = Incident(
                        id=str(uuid4()),
                        service=service_name,
                        status="open",
                        first_error=result.get("error"),
                        last_error=result.get("error"),
                        http_status=result.get("http_status"),
                        failed_checks=1,
                        detected_at=observed_at,
                        last_seen_at=observed_at,
                    )
                    session.add(incident)
                else:
                    incident.failed_checks += 1
                    incident.last_seen_at = observed_at
                    incident.last_error = result.get("error")
                    incident.http_status = result.get("http_status")

                session.commit()
                session.refresh(incident)
                return incident_to_dict(incident)

            if incident is not None:
                incident.status = "resolved"
                incident.resolved_at = observed_at
                incident.duration_seconds = round(
                    max(
                        0.0,
                        (
                            observed_at
                            - parse_timestamp(incident.detected_at)
                        ).total_seconds(),
                    ),
                    2,
                )

                session.commit()
                session.refresh(incident)
                return incident_to_dict(incident)

        return None

    def _record_remediation_db(
        self,
        incident_id: str,
        result: dict,
    ) -> dict:
        with self._session_factory() as session:
            incident = session.get(Incident, incident_id)

            if incident is None:
                raise KeyError(f"Unknown incident: {incident_id}")

            attempt = RemediationAttempt(
                incident_id=incident_id,
                attempted_at=parse_timestamp(utc_now()),
                success=bool(result.get("success", False)),
                reason=result.get("reason", "unknown"),
                service=result.get("service", incident.service),
                action=result.get("action", "restart"),
            )

            session.add(attempt)
            session.commit()
            session.refresh(attempt)

            return {
                "attempted_at": attempt.attempted_at.isoformat(),
                "success": attempt.success,
                "reason": attempt.reason,
                "service": attempt.service,
                "action": attempt.action,
            }

    def observe(self, result: dict) -> dict | None:
        if self._session_factory is not None:
            return self._observe_db(result)

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
        if self._session_factory is not None:
            return self._record_remediation_db(incident_id, result)

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
        if self._session_factory is not None:
            with self._session_factory() as session:
                incidents = session.scalars(
                    select(Incident).order_by(Incident.detected_at.desc())
                ).all()
                return [incident_to_dict(item) for item in incidents]

        return [incident.copy() for incident in self._incidents.values()]

    def get_active_incidents(self) -> list[dict]:
        if self._session_factory is not None:
            with self._session_factory() as session:
                incidents = session.scalars(
                    select(Incident)
                    .where(Incident.status == "open")
                    .order_by(Incident.detected_at.desc())
                ).all()
                return [incident_to_dict(item) for item in incidents]

        return [
            incident.copy()
            for incident in self._incidents.values()
            if incident["status"] == "open"
        ]


incident_manager = IncidentManager(session_factory=SessionLocal)
