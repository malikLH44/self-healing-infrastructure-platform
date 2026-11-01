
import asyncio
import json
import logging
import os
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from app.resource_alerts import resource_alert_manager


from app.container_controller import AllowlistedContainerController
from app.docker_restart_backend import DockerRestartBackend
from app.incidents import incident_manager
from app.policy_engine import policy_engine
from app.remediation_executor import RemediationExecutor
from app.remediation_worker import remediation_worker
from app.docker_stats_backend import DockerStatsBackend

logger = logging.getLogger(__name__)
docker_stats_backend = DockerStatsBackend()

CONFIG_PATH = Path("/app/config/services.json")
MONITORING_INTERVAL = int(
    os.getenv("SHIP_MONITORING_INTERVAL_SECONDS", "15")
)

# Explicit allowlist: logical service name -> authorized container name.
remediation_executor = RemediationExecutor(
    AllowlistedContainerController(
        DockerRestartBackend(),
        allowed_services={
            "demo-service": "ship-demo-service",
        },
    )
)


def load_services() -> list[dict]:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = json.load(file)

    services = config["services"]

    if not isinstance(services, list):
        raise ValueError("'services' must be a list")

    for service in services:
        if not all(key in service for key in ("name", "url")):
            raise ValueError("Each service must have a name and a URL")

    return services


def check_service(service: dict) -> dict:
    try:
        with urlopen(
            service["url"],
            timeout=service.get("timeout_seconds", 3),
        ) as response:
            healthy = 200 <= response.status < 400

            return {
                "name": service["name"],
                "status": "healthy" if healthy else "unhealthy",
                "http_status": response.status,
            }

    except HTTPError as error:
        return {
            "name": service["name"],
            "status": "unhealthy",
            "http_status": error.code,
        }

    except (URLError, TimeoutError, OSError) as error:
        return {
            "name": service["name"],
            "status": "unhealthy",
            "error": str(error),
        }


class MonitoringManager:
    def __init__(self) -> None:
        self.latest_status: dict[str, dict] = {}
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("Monitoring manager started")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        logger.info("Monitoring manager stopped")

    async def _remediate(self, incident: dict) -> None:
        decision = policy_engine.evaluate_remediation(incident)

        if not decision["allowed"]:
            logger.debug(
                "Remediation not allowed: service=%s reason=%s",
                incident["service"],
                decision["reason"],
            )
            return

        # Record the attempt before execution so failures count toward
        # the cooldown and maximum-attempt limits.
        remediation_worker.record_attempt(
            incident_id=incident["id"],
            service=decision["service"],
        )

        result = await asyncio.to_thread(
            remediation_executor.execute,
            decision["service"],
            decision["action"],
        )


        incident_manager.record_remediation(
            incident_id=incident["id"],
            result=result,
        )

        logger.info(
            "Remediation result: incident=%s service=%s success=%s reason=%s",
            incident["id"],
            incident["service"],
            result["success"],
            result["reason"],
        )


    async def check_all_services(self) -> None:
        try:
            services = load_services()
        except (OSError, ValueError, KeyError, TypeError) as error:
            logger.error(
                "Unable to load service configuration: %s", error
            )
            return

        for service in services:
            try:
                # 1. Perform the HTTP health check.
                result = await asyncio.to_thread(check_service, service)

                # 2. Collect Docker CPU and memory statistics.
                try:
                    resource_stats = await asyncio.to_thread(
                        docker_stats_backend.get_stats,
                        service["name"],
                    )

                    if resource_stats:
                        result.update(resource_stats)

                except Exception:
                    logger.warning(
                        "Unable to collect resource metrics for service %s",
                        service["name"],
                        exc_info=True,
                    )

                # 3. Evaluate configured resource thresholds.
                thresholds = service.get("resource_thresholds", {})

                if thresholds:
                    for resource, metric_key in (
                        ("cpu", "cpu_percent"),
                        ("memory", "memory_percent"),
                    ):
                        threshold_percent = thresholds.get(metric_key)

                        if threshold_percent is None:
                            continue

                        try:
                            alert = resource_alert_manager.observe(
                                service=service["name"],
                                resource=resource,
                                observed_percent=result.get(metric_key),
                                threshold_percent=threshold_percent,
                                required_checks=thresholds.get(
                                    "consecutive_checks", 3
                                ),
                            )

                            if alert and alert["status"] == "resolved":
                                logger.info(
                                    "Resource alert resolved: "
                                    "service=%s resource=%s",
                                    service["name"],
                                    resource,
                                )

                        except Exception:
                            logger.exception(
                                "Resource alert evaluation failed: "
                                "service=%s resource=%s",
                                service["name"],
                                resource,
                            )

                # 4. Update monitoring results.
                result["checked_at"] = datetime.now(
                    timezone.utc
                ).isoformat()

                self.latest_status[service["name"]] = result

                # 5. Preserve the existing HTTP incident mechanism.
                incident = incident_manager.observe(result)

                logger.info(
                    "Service check completed: name=%s status=%s",
                    result["name"],
                    result["status"],
                )

                if (
                    result["status"] != "healthy"
                    and incident is not None
                    and incident["status"] == "open"
                ):
                    await self._remediate(incident)

            except Exception:
                logger.exception(
                    "Unexpected error while checking service %s",
                    service.get("name", "<unknown>"),
                )

    async def _monitor_loop(self) -> None:
        while True:
            await self.check_all_services()
            await asyncio.sleep(MONITORING_INTERVAL)


monitoring_manager = MonitoringManager()
