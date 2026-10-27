import unittest
from unittest.mock import MagicMock, patch
from urllib.error import URLError

from app.docker_restart_backend import DockerRestartBackend


class TestDockerRestartBackend(unittest.TestCase):
    @patch("app.docker_restart_backend.urlopen")
    def test_restarts_container(self, mock_urlopen):
        response = MagicMock()
        response.status = 204
        response.__enter__.return_value = response
        mock_urlopen.return_value = response

        backend = DockerRestartBackend(
            base_url="http://docker-proxy:2375"
        )

        backend.restart_container("ship-demo-service")

        request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "http://docker-proxy:2375/containers/"
            "ship-demo-service/restart?t=10",
        )
        self.assertEqual(request.method, "POST")

    @patch("app.docker_restart_backend.urlopen")
    def test_rejects_empty_container_name(self, mock_urlopen):
        backend = DockerRestartBackend()

        with self.assertRaises(ValueError):
            backend.restart_container("")

        mock_urlopen.assert_not_called()

    @patch("app.docker_restart_backend.urlopen")
    def test_handles_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = URLError("connection refused")
        backend = DockerRestartBackend()

        with self.assertRaises(RuntimeError):
            backend.restart_container("ship-demo-service")


if __name__ == "__main__":
    unittest.main()