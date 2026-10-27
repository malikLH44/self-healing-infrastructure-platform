import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class ContainerRestartBackend(Protocol):
    """Interface for the component performing container restarts."""

    def restart_container(self, container_name: str) -> None:
        """Restart a container identified by its actual container name."""
        ...


class AllowlistedContainerController:
    """Allow restarts only for explicitly authorized services."""

    def __init__(
        self,
        delegate: ContainerRestartBackend,
        allowed_services: dict[str, str],
    ) -> None:
        self._delegate = delegate
        self._allowed_services = allowed_services

    def restart(self, service: str) -> None:
        container_name = self._allowed_services.get(service)

        if container_name is None:
            raise ValueError(
                f"Service is not authorized for remediation: {service}"
            )

        self._delegate.restart_container(container_name)

        logger.info(
            "Authorized restart requested: service=%s container=%s",
            service,
            container_name,
        )