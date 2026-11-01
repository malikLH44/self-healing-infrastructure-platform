
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.resource_alerts import ResourceAlertManager


class ResourceAlertManagerTests(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        Base.metadata.create_all(bind=self.engine)

        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )

        self.manager = ResourceAlertManager(
            session_factory=self.SessionLocal
        )

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def observe_cpu(self, value):
        return self.manager.observe(
            service="demo-service",
            resource="cpu",
            observed_percent=value,
            threshold_percent=80,
            required_checks=3,
        )

    def test_alert_created_after_three_consecutive_breaches(self):
        self.assertIsNone(self.observe_cpu(85))
        self.assertIsNone(self.observe_cpu(90))

        alert = self.observe_cpu(88)

        self.assertIsNotNone(alert)
        self.assertEqual(alert["status"], "open")
        self.assertEqual(alert["resource"], "cpu")
        self.assertEqual(alert["consecutive_checks"], 3)
        self.assertEqual(alert["observed_percent"], 88)

    def test_below_threshold_resets_consecutive_checks(self):
        self.assertIsNone(self.observe_cpu(85))
        self.assertIsNone(self.observe_cpu(70))
        self.assertIsNone(self.observe_cpu(85))
        self.assertIsNone(self.observe_cpu(85))

        self.assertEqual(self.manager.get_active_alerts(), [])

        alert = self.observe_cpu(90)

        self.assertIsNotNone(alert)
        self.assertEqual(alert["status"], "open")

    def test_open_alert_is_updated_when_threshold_is_exceeded(self):
        self.observe_cpu(85)
        self.observe_cpu(90)
        alert = self.observe_cpu(88)

        updated_alert = self.observe_cpu(94)

        self.assertEqual(updated_alert["id"], alert["id"])
        self.assertEqual(updated_alert["status"], "open")
        self.assertEqual(updated_alert["observed_percent"], 94)

        self.assertEqual(len(self.manager.get_active_alerts()), 1)

    def test_alert_resolved_when_resource_returns_below_threshold(self):
        self.observe_cpu(85)
        self.observe_cpu(90)
        alert = self.observe_cpu(88)

        resolved = self.observe_cpu(65)

        self.assertEqual(resolved["id"], alert["id"])
        self.assertEqual(resolved["status"], "resolved")
        self.assertIsNotNone(resolved["resolved_at"])
        self.assertIsNotNone(resolved["duration_seconds"])

        self.assertEqual(self.manager.get_active_alerts(), [])
        self.assertEqual(len(self.manager.list_alerts()), 1)

    def test_missing_metric_does_not_resolve_open_alert(self):
        self.observe_cpu(85)
        self.observe_cpu(90)
        alert = self.observe_cpu(88)

        result = self.manager.observe(
            service="demo-service",
            resource="cpu",
            observed_percent=None,
            threshold_percent=80,
            required_checks=3,
        )

        self.assertIsNone(result)

        active_alerts = self.manager.get_active_alerts()
        self.assertEqual(len(active_alerts), 1)
        self.assertEqual(active_alerts[0]["id"], alert["id"])

    def test_cpu_and_memory_alerts_are_independent(self):
        self.assertIsNone(self.observe_cpu(85))
        self.assertIsNone(self.observe_cpu(85))
        cpu_alert = self.observe_cpu(85)

        memory_alert = self.manager.observe(
            service="demo-service",
            resource="memory",
            observed_percent=90,
            threshold_percent=80,
            required_checks=1,
        )

        self.assertIsNotNone(cpu_alert)
        self.assertIsNotNone(memory_alert)
        self.assertEqual(cpu_alert["resource"], "cpu")
        self.assertEqual(memory_alert["resource"], "memory")

        self.assertEqual(len(self.manager.get_active_alerts()), 2)


if __name__ == "__main__":
    unittest.main()
    