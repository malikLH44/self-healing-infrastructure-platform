import asyncio
import json
import logging
import os
from contextlib import suppress
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from app.incidents import incident_manager

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("/app/config/services.json")
MONITORING_INTERVAL = int(
    os.getenv("SHIP_MONITORING_INTERVAL_SECONDS", "15")
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

    async def check_all_services(self) -> None:
        try:
            services = load_services()
        except (OSError, ValueError, KeyError, TypeError) as error:
            logger.error("Unable to load service configuration: %s", error)
            return

        for service in services:
            try:
                # The HTTP check is blocking, so run it in a worker thread.
                result = await asyncio.to_thread(check_service, service)
                result["checked_at"] = (
                    __import__("datetime").datetime.now(
                        __import__("datetime").timezone.utc
                    ).isoformat()
                )
                self.latest_status[service["name"]] = result
                incident_manager.observe(result)

                logger.info(
                    "Service check completed: name=%s status=%s",
                    result["name"],
                    result["status"],
                )
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