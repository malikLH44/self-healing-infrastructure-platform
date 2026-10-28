
import unittest

from app.incidents import IncidentManager


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


if __name__ == "__main__":
    unittest.main()
