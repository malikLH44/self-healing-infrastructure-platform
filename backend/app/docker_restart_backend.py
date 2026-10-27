import logging
import os
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class DockerRestartBackend:
    """Request container restarts through a Docker API endpoint."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int = 5,
    ) -> None:
        self._base_url = (
            base_url or os.getenv(
                "DOCKER_API_URL",
                "http://docker-proxy:2375",
            )
        ).rstrip("/")
        self._timeout_seconds = timeout_seconds

    def restart_container(self, container_name: str) -> None:
        if not container_name:
            raise ValueError("Container name must not be empty")

        encoded_name = quote(container_name, safe="")
        url = (
            f"{self._base_url}/containers/"
            f"{encoded_name}/restart?t=10"
        )
        request = Request(url, method="POST")

        try:
            with urlopen(
                request,
                timeout=self._timeout_seconds,
            ) as response:
                if response.status != 204:
                    raise RuntimeError(
                        f"Unexpected Docker API status: {response.status}"
                    )
        except URLError as exc:
            logger.error(
                "Docker restart request failed for container=%s",
                container_name,
            )
            raise RuntimeError(
                "Docker restart request failed"
            ) from exc