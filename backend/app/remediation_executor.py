
import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class ContainerController(Protocol):
    """Interface for a restricted container-control implementation."""

    def restart(self, service: str) -> None:
        """Restart an explicitly authorized service."""
        ...


class RemediationExecutor:
    """Executes remediation through an injected container controller."""

    def __init__(self, controller: ContainerController) -> None:
        self._controller = controller

    def execute(self, service: str, action: str) -> dict:
        if action != "restart":
            return {
                "success": False,
                "reason": "unsupported_action",
                "service": service,
            }

        try:
            self._controller.restart(service)
        except Exception:
            logger.exception(
                "Remediation failed: service=%s action=%s",
                service,
                action,
            )
            return {
                "success": False,
                "reason": "execution_failed",
                "service": service,
                "action": action,
            }

        logger.info(
            "Remediation executed: service=%s action=%s",
            service,
            action,
        )

        return {
            "success": True,
            "reason": "action_executed",
            "service": service,
            "action": action,
        }
