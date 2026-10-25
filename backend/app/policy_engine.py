
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

POLICIES_PATH = Path("/app/config/remediation-policies.json")


class PolicyEngine:
    def __init__(self) -> None:
        self._policies: dict[str, dict] = {}

    def load_policies(self) -> None:
        with POLICIES_PATH.open("r", encoding="utf-8") as file:
            config = json.load(file)

        policies = config.get("policies")

        if not isinstance(policies, list):
            raise ValueError("'policies' must be a list")

        loaded: dict[str, dict] = {}

        for policy in policies:
            service = policy.get("service")
            action = policy.get("action")

            if not isinstance(service, str) or not service.strip():
                raise ValueError("Each policy needs a service name")

            if service in loaded:
                raise ValueError(f"Duplicate policy for service: {service}")

            if action != "restart":
                raise ValueError(
                    f"Unsupported action for service '{service}': {action}"
                )

            if not isinstance(policy.get("enabled"), bool):
                raise ValueError(
                    f"'enabled' must be boolean for service '{service}'"
                )

            for field in (
                "trigger_after_failed_checks",
                "cooldown_seconds",
                "max_attempts",
            ):
                value = policy.get(field)

                if type(value) is not int or value < 1:
                    raise ValueError(
                        f"'{field}' must be a positive integer "
                        f"for service '{service}'"
                    )

            loaded[service] = policy.copy()

        self._policies = loaded
        logger.info("Loaded %s remediation policies", len(loaded))

    def evaluate(self, incident: dict) -> dict:
        service = incident.get("service")
        policy = self._policies.get(service)

        if policy is None:
            return {
                "allowed": False,
                "reason": "no_policy",
                "service": service,
            }

        if not policy["enabled"]:
            return {
                "allowed": False,
                "reason": "policy_disabled",
                "service": service,
            }

        if incident.get("status") != "open":
            return {
                "allowed": False,
                "reason": "incident_not_open",
                "service": service,
            }

        failed_checks = incident.get("failed_checks", 0)

        if failed_checks < policy["trigger_after_failed_checks"]:
            return {
                "allowed": False,
                "reason": "threshold_not_reached",
                "service": service,
                "failed_checks": failed_checks,
                "required_failed_checks": (
                    policy["trigger_after_failed_checks"]
                ),
            }

        return {
            "allowed": True,
            "reason": "policy_matched",
            "service": service,
            "action": policy["action"],
            "cooldown_seconds": policy["cooldown_seconds"],
            "max_attempts": policy["max_attempts"],
        }


policy_engine = PolicyEngine()
