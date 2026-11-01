"""Manage persistent CPU and memory resource alerts."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.models import ResourceAlert


class ResourceAlertManager:
    """Detect, persist, update, and resolve resource alerts."""

    def __init__(self, session_factory=None) -> None:
        self._session_factory = session_factory or SessionLocal
        self._breach_counts: dict[tuple[str, str], int] = {}

    @staticmethod
    def _to_dict(alert: ResourceAlert) -> dict:
        return {
            "id": alert.id,
            "service": alert.service,
            "resource": alert.resource,
            "status": alert.status,
            "threshold_percent": alert.threshold_percent,
            "observed_percent": alert.observed_percent,
            "consecutive_checks": alert.consecutive_checks,
            "detected_at": alert.detected_at.isoformat(),
            "last_seen_at": alert.last_seen_at.isoformat(),
            "resolved_at": (
                alert.resolved_at.isoformat()
                if alert.resolved_at
                else None
            ),
            "duration_seconds": alert.duration_seconds,
        }

    def observe(
        self,
        service: str,
        resource: str,
        observed_percent: float | None,
        threshold_percent: float,
        required_checks: int = 3,
    ) -> dict | None:
        if resource not in ("cpu", "memory"):
            raise ValueError("Resource must be 'cpu' or 'memory'")

        if threshold_percent <= 0 or threshold_percent > 100:
            raise ValueError(
                "Resource threshold must be between 0 and 100"
            )

        if required_checks < 1:
            raise ValueError("required_checks must be positive")

        key = (service, resource)

        if observed_percent is None:
            self._breach_counts[key] = 0
            return None

        now = datetime.now(timezone.utc)

        with self._session_factory() as session:
            alert = session.scalar(
                select(ResourceAlert).where(
                    ResourceAlert.service == service,
                    ResourceAlert.resource == resource,
                    ResourceAlert.status == "open",
                )
            )

            # An existing alert is updated or resolved.
            if alert is not None:

                if observed_percent > threshold_percent:
                    alert.observed_percent = observed_percent
                    alert.threshold_percent = threshold_percent
                    alert.last_seen_at = now

                    session.commit()
                    session.refresh(alert)

                    return self._to_dict(alert)

                # Resource returned below its threshold.
                alert.status = "resolved"
                alert.resolved_at = now
                alert.last_seen_at = now

                detected_at = alert.detected_at

                if detected_at.tzinfo is None:
                    detected_at = detected_at.replace(
                        tzinfo=timezone.utc
                    )
                else:
                    detected_at = detected_at.astimezone(
                        timezone.utc
                    )

                alert.duration_seconds = round(
                    max(
                        0.0,
                        (now - detected_at).total_seconds(),
                    ),
                    2,
                )

                self._breach_counts[key] = 0

                session.commit()
                session.refresh(alert)

                return self._to_dict(alert)

            # No alert exists: reset the counter if usage is normal.
            if observed_percent <= threshold_percent:
                self._breach_counts[key] = 0
                return None

            # Count consecutive threshold breaches.
            count = self._breach_counts.get(key, 0) + 1
            self._breach_counts[key] = count

            if count < required_checks:
                return None

            # Create a new persistent resource alert.
            alert = ResourceAlert(
                id=str(uuid4()),
                service=service,
                resource=resource,
                status="open",
                threshold_percent=threshold_percent,
                observed_percent=observed_percent,
                consecutive_checks=count,
                detected_at=now,
                last_seen_at=now,
            )

            session.add(alert)
            session.commit()
            session.refresh(alert)

            self._breach_counts[key] = 0

            return self._to_dict(alert)

    def list_alerts(self) -> list[dict]:
        with self._session_factory() as session:
            alerts = session.scalars(
                select(ResourceAlert).order_by(
                    ResourceAlert.detected_at.desc()
                )
            ).all()

            return [self._to_dict(alert) for alert in alerts]

    def get_active_alerts(self) -> list[dict]:
        with self._session_factory() as session:
            alerts = session.scalars(
                select(ResourceAlert)
                .where(ResourceAlert.status == "open")
                .order_by(ResourceAlert.detected_at.desc())
            ).all()

            return [self._to_dict(alert) for alert in alerts]


resource_alert_manager = ResourceAlertManager()

