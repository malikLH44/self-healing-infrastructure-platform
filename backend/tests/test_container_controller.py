import unittest
from unittest.mock import Mock

from app.container_controller import AllowlistedContainerController


class TestAllowlistedContainerController(unittest.TestCase):
    def setUp(self):
        self.delegate = Mock()
        self.controller = AllowlistedContainerController(
            delegate=self.delegate,
            allowed_services={
                "demo-service": "ship-demo-service",
            },
        )

    def test_allows_authorized_service(self):
        self.controller.restart("demo-service")

        self.delegate.restart.assert_called_once_with("demo-service")

    def test_rejects_unknown_service(self):
        with self.assertRaises(ValueError):
            self.controller.restart("unknown-service")

        self.delegate.restart.assert_not_called()


if __name__ == "__main__":
    unittest.main()