
import unittest
from unittest.mock import patch

from app.remediation_worker import RemediationWorker


class TestRemediationWorker(unittest.TestCase):
    def setUp(self):
        self.worker = RemediationWorker()

    def test_allows_first_attempt(self):
        result = self.worker.check_limits(
            "incident-1", "demo-service", 60, 3
        )

        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "limits_satisfied")

    def test_blocks_attempt_during_cooldown(self):
        self.worker.record_attempt("incident-1", "demo-service")

        result = self.worker.check_limits(
            "incident-1", "demo-service", 60, 3
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "cooldown_active")

    def test_blocks_after_max_attempts(self):
        for _ in range(3):
            self.worker.record_attempt("incident-1", "demo-service")

        result = self.worker.check_limits(
            "incident-1", "demo-service", 0, 3
        )

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "max_attempts_reached")

    def test_cooldown_expires(self):
        self.worker.record_attempt("incident-1", "demo-service")

        with patch("app.remediation_worker.time.monotonic") as clock:
            clock.return_value = 100
            self.worker._last_attempt["demo-service:incident-1"] = 100

            clock.return_value = 161
            result = self.worker.check_limits(
                "incident-1", "demo-service", 60, 3
            )

        self.assertTrue(result["allowed"])

    def test_attempts_are_independent_between_incidents(self):
        self.worker.record_attempt("incident-1", "demo-service")
        self.worker.record_attempt("incident-1", "demo-service")
        self.worker.record_attempt("incident-2", "demo-service")

        first_incident = self.worker.check_limits(
            "incident-1", "demo-service", 0, 3
        )
        second_incident = self.worker.check_limits(
            "incident-2", "demo-service", 0, 3
        )

        self.assertEqual(first_incident["attempts"], 2)
        self.assertEqual(second_incident["attempts"], 1)


if __name__ == "__main__":
    unittest.main()
