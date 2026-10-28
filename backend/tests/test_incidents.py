
import unittest
from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.incidents import IncidentManager
from app.models import Incident, RemediationAttempt


class TestIncidentManager(unittest.TestCase):
    def setUp(self):
        self.manager = IncidentManager()
        self.incident = self.manager.observe({
            "name": "demo-service",
            "status": "unhealthy",
            "http_status": 503,
        })

    def test_records_successful_remediation(self):
        attempt = self.manager.record_remediation(
            self.incident["id"],
            {
                "success": True,
                "reason": "action_executed",
                "service": "demo-service",
                "action": "restart",
            },
        )

        saved = self.manager.list_incidents()[0]

        self.assertTrue(attempt["success"])
        self.assertEqual(len(saved["remediation_attempts"]), 1)
        self.assertEqual(
            saved["remediation_attempts"][0]["reason"],
            "action_executed",
        )

    def test_records_failed_remediation(self):
        self.manager.record_remediation(
            self.incident["id"],
            {
                "success": False,
                "reason": "execution_failed",
                "service": "demo-service",
                "action": "restart",
            },
        )

        saved = self.manager.list_incidents()[0]
        self.assertFalse(saved["remediation_attempts"][0]["success"])

    def test_rejects_unknown_incident(self):
        with self.assertRaises(KeyError):
            self.manager.record_remediation(
                "unknown-id",
                {"success": True},
            )


class TestIncidentManagerPersistence(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)

        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        self.manager = IncidentManager(
            session_factory=self.session_factory,
        )

    def tearDown(self):
        self.engine.dispose()

    def test_persists_incident_and_remediation_attempt(self):
        incident = self.manager.observe({
            "name": "demo-service",
            "status": "unhealthy",
            "http_status": 503,
            "error": "Service unavailable",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        })

        self.assertIsNotNone(incident)
        self.assertEqual(incident["status"], "open")

        attempt = self.manager.record_remediation(
            incident["id"],
            {
                "success": True,
                "reason": "action_executed",
                "service": "demo-service",
                "action": "restart",
            },
        )

        self.assertTrue(attempt["success"])

        with self.session_factory() as session:
            saved_incident = session.get(Incident, incident["id"])
            saved_attempts = session.scalars(
                select(RemediationAttempt).where(
                    RemediationAttempt.incident_id == incident["id"]
                )
            ).all()

            self.assertIsNotNone(saved_incident)
            self.assertEqual(saved_incident.status, "open")
            self.assertEqual(len(saved_attempts), 1)
            self.assertEqual(
                saved_attempts[0].reason,
                "action_executed",
            )

    def test_resolves_incident_and_records_duration(self):
        detected_at = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        resolved_at = datetime(2026, 1, 1, 12, 0, 30, tzinfo=timezone.utc)

        incident = self.manager.observe({
            "name": "demo-service",
            "status": "unhealthy",
            "checked_at": detected_at.isoformat(),
        })

        resolved = self.manager.observe({
            "name": "demo-service",
            "status": "healthy",
            "checked_at": resolved_at.isoformat(),
        })

        self.assertEqual(resolved["id"], incident["id"])
        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(resolved["duration_seconds"], 30.0)

        with self.session_factory() as session:
            saved = session.get(Incident, incident["id"])
            self.assertEqual(saved.status, "resolved")
            self.assertEqual(saved.duration_seconds, 30.0)


if __name__ == "__main__":
    unittest.main()
