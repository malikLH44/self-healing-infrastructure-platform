"""Read resource statistics through the restricted Docker proxy."""

import json
import os
from urllib.parse import quote
from urllib.request import urlopen


class DockerStatsBackend:
    """Collect CPU and memory metrics for authorized containers."""

    def __init__(self, timeout_seconds: int = 5) -> None:
        self._base_url = os.getenv(
            "DOCKER_API_URL",
            "http://docker-proxy:2375",
        ).rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._allowed_containers = {
            "demo-service": "ship-demo-service",
        }

    def get_stats(self, service_name: str) -> dict | None:
        container_name = self._allowed_containers.get(service_name)
        if container_name is None:
            return None

        url = (
            f"{self._base_url}/containers/"
            f"{quote(container_name, safe='')}/stats?stream=false"
        )

        with urlopen(url, timeout=self._timeout_seconds) as response:
            stats = json.loads(response.read().decode("utf-8"))

        cpu = stats.get("cpu_stats") or {}
        previous_cpu = stats.get("precpu_stats") or {}

        current_usage = (cpu.get("cpu_usage") or {}).get("total_usage", 0)
        previous_usage = (
            previous_cpu.get("cpu_usage") or {}
        ).get("total_usage", 0)

        current_system = cpu.get("system_cpu_usage", 0)
        previous_system = previous_cpu.get("system_cpu_usage", 0)

        online_cpus = cpu.get("online_cpus") or len(
            (cpu.get("cpu_usage") or {}).get("percpu_usage") or []
        )

        cpu_delta = current_usage - previous_usage
        system_delta = current_system - previous_system

        cpu_percent = (
            round(cpu_delta / system_delta * online_cpus * 100, 2)
            if cpu_delta >= 0 and system_delta > 0 and online_cpus > 0
            else None
        )

        memory = stats.get("memory_stats") or {}
        memory_usage = memory.get("usage")
        memory_limit = memory.get("limit")

        memory_percent = (
            round(memory_usage / memory_limit * 100, 2)
            if isinstance(memory_usage, (int, float))
            and isinstance(memory_limit, (int, float))
            and memory_limit > 0
            else None
        )

        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "memory_usage_bytes": memory_usage,
            "memory_limit_bytes": memory_limit,
        }

