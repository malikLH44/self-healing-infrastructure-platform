
import unittest
from unittest.mock import Mock

from app.remediation_executor import RemediationExecutor


class TestRemediationExecutor(unittest.TestCase):
    def setUp(self):
        self.controller = Mock()
        self.executor = RemediationExecutor(self.controller)

    def test_executes_restart(self):
        result = self.executor.execute("demo-service", "restart")

        self.controller.restart.assert_called_once_with("demo-service")
        self.assertTrue(result["success"])
        self.assertEqual(result["reason"], "action_executed")

    def test_rejects_unsupported_action(self):
        result = self.executor.execute("demo-service", "delete")

        self.controller.restart.assert_not_called()
        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "unsupported_action")

    def test_handles_controller_failure(self):
        self.controller.restart.side_effect = RuntimeError("simulated failure")

        result = self.executor.execute("demo-service", "restart")

        self.assertFalse(result["success"])
        self.assertEqual(result["reason"], "execution_failed")


if __name__ == "__main__":
    unittest.main()
