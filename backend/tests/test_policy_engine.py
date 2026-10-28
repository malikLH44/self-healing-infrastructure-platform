
import unittest
from unittest.mock import patch

from app.policy_engine import PolicyEngine


class TestPolicyEngine(unittest.TestCase):
    def setUp(self):
        self.engine = PolicyEngine()
        self.engine._policies = {
            "demo-service": {
                "service": "demo-service",
                "enabled": True,
                "action": "restart",
                "trigger_after_failed_checks": 3,
                "cooldown_seconds": 60,
                "max_attempts": 3,
            }
        }

        self.incident = {
            "id": "incident-1",
            "service": "demo-service",
            "status": "open",
            "failed_checks": 3,
        }

    @patch("app.policy_engine.remediation_worker.check_limits")
    def test_allows_remediation_when_policy_and_limits_allow(self, mock_limits):
        mock_limits.return_value = {
            "allowed": True,
            "reason": "limits_satisfied",
            "attempts": 0,
        }

        result = self.engine.evaluate_remediation(self.incident)

        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "limits_satisfied")
        self.assertEqual(result["attempts"], 0)

    @patch("app.policy_engine.remediation_worker.check_limits")
    def test_blocks_remediation_during_cooldown(self, mock_limits):
        mock_limits.return_value = {
            "allowed": False,
            "reason": "cooldown_active",
            "attempts": 1,
            "retry_after_seconds": 45,
        }

        result = self.engine.evaluate_remediation(self.incident)

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "cooldown_active")
        self.assertEqual(result["retry_after_seconds"], 45)

    @patch("app.policy_engine.remediation_worker.check_limits")
    def test_blocks_remediation_when_max_attempts_reached(self, mock_limits):
        mock_limits.return_value = {
            "allowed": False,
            "reason": "max_attempts_reached",
            "attempts": 3,
        }

        result = self.engine.evaluate_remediation(self.incident)

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "max_attempts_reached")
        self.assertEqual(result["attempts"], 3)

    @patch("app.policy_engine.remediation_worker.check_limits")
    def test_does_not_check_limits_when_policy_rejects(self, mock_limits):
        self.incident["failed_checks"] = 1

        result = self.engine.evaluate_remediation(self.incident)

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "threshold_not_reached")
        mock_limits.assert_not_called()


    @patch("app.policy_engine.remediation_worker")
    def test_blocks_remediation_after_real_attempt_limit(self, mock_worker):
        mock_worker.check_limits.return_value = {
            "allowed": False,
            "reason": "max_attempts_reached",
            "attempts": 3,
        }

        result = self.engine.evaluate_remediation(self.incident)

        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "max_attempts_reached")
        self.assertEqual(result["attempts"], 3)


if __name__ == "__main__":
    unittest.main()
