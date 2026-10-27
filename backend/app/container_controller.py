import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class ContainerController(Protocol):
    """Interface for a restricted container controller."""

    def restart(self, service: str) -> None:
        """Restart an explicitly authorized service."""
        ...


class AllowlistedContainerController:
    """Validates service names before delegating container operations."""

    def __init__(
        self,
        delegate: ContainerController,
        allowed_services: dict[str, str],
    ) -> None:
        self._delegate = delegate
        self._allowed_services = allowed_services

    def restart(self, service: str) -> None:
        if service not in self._allowed_services:
            raise ValueError(
                f"Service is not authorized for remediation: {service}"
            )

        self._delegate.restart(service)
        logger.info("Authorized restart requested: service=%s", service)