import logging
import time
from threading import Lock

logger = logging.getLogger(__name__)


class RemediationWorker:
    """Controls remediation eligibility and execution limits."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._attempts: dict[str, int] = {}
        self._last_attempt: dict[str, float] = {}

    def check_limits(
        self,
        incident_id: str,
        service: str,
        cooldown_seconds: int,
        max_attempts: int,
    ) -> dict:
        key = f"{service}:{incident_id}"

        with self._lock:
            attempts = self._attempts.get(key, 0)
            last_attempt = self._last_attempt.get(key)

            if attempts >= max_attempts:
                return {
                    "allowed": False,
                    "reason": "max_attempts_reached",
                    "attempts": attempts,
                }

            if last_attempt is not None:
                elapsed = time.monotonic() - last_attempt
                remaining = cooldown_seconds - elapsed

                if remaining > 0:
                    return {
                        "allowed": False,
                        "reason": "cooldown_active",
                        "retry_after_seconds": round(remaining, 2),
                        "attempts": attempts,
                    }

            return {
                "allowed": True,
                "reason": "limits_satisfied",
                "attempts": attempts,
            }

    def record_attempt(self, incident_id: str, service: str) -> None:
        key = f"{service}:{incident_id}"

        with self._lock:
            self._attempts[key] = self._attempts.get(key, 0) + 1
            self._last_attempt[key] = time.monotonic()

        logger.info(
            "Remediation attempt recorded: service=%s incident=%s",
            service,
            incident_id,
        )
        


remediation_worker = RemediationWorker()