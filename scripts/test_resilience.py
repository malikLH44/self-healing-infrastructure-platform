"""Run a controlled end-to-end SHIP self-healing test."""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.request import urlopen

API_BASE_URL = "http://localhost:8000"
SERVICE_NAME = "demo-service"
CONTAINER_NAME = "ship-demo-service"
TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 2


def get_json(path):
    """Fetch and decode a JSON response from the SHIP API."""
    url = f"{API_BASE_URL}{path}"
    with urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def container_is_running():
    """Return whether the target container is currently running."""
    result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}",
         CONTAINER_NAME],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def main():
    stop_requested = False
    test_passed = False

    try:
        health = get_json("/health")
        if health.get("status") != "healthy":
            raise RuntimeError("SHIP API is not healthy.")

        service = get_json(f"/services/{SERVICE_NAME}")
        if service.get("status") != "healthy":
            raise RuntimeError(
                f"{SERVICE_NAME} must be healthy before the test."
            )

        if not container_is_running():
            raise RuntimeError(
                f"{CONTAINER_NAME} is not running. Start the stack first."
            )

        baseline = get_json("/incidents").get("incidents", [])
        previous_ids = {item["id"] for item in baseline}

        started_at = datetime.now(timezone.utc)
        started_monotonic = time.monotonic()

        print(f"Injecting controlled failure into {CONTAINER_NAME}...")
        stop_requested = True
        result = subprocess.run(
            ["docker", "stop", CONTAINER_NAME],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Could not stop container: {result.stderr.strip()}"
            )

        print("Waiting for incident detection and automatic recovery...")

        deadline = time.monotonic() + TIMEOUT_SECONDS

        while time.monotonic() < deadline:
            incidents = get_json("/incidents").get("incidents", [])
            new_incidents = [
                item
                for item in incidents
                if item.get("id") not in previous_ids
                and item.get("service") == SERVICE_NAME
            ]

            if new_incidents:
                incident = max(
                    new_incidents,
                    key=lambda item: item.get("detected_at", ""),
                )
                service = get_json(f"/services/{SERVICE_NAME}")
                attempts = incident.get("remediation_attempts", [])
                successful_attempts = sum(
                    1 for attempt in attempts if attempt.get("success")
                )

                if (
                    incident.get("status") == "resolved"
                    and service.get("status") == "healthy"
                    and successful_attempts > 0
                ):
                    detected_at = datetime.fromisoformat(
                        incident["detected_at"].replace("Z", "+00:00")
                    )
                    detection_seconds = max(
                        0.0, (detected_at - started_at).total_seconds()
                    )
                    elapsed_seconds = time.monotonic() - started_monotonic

                    report = {
                        "result": "PASS",
                        "service": SERVICE_NAME,
                        "container": CONTAINER_NAME,
                        "incident_id": incident["id"],
                        "final_incident_status": incident["status"],
                        "final_service_status": service["status"],
                        "detection_latency_seconds": round(
                            detection_seconds, 2
                        ),
                        "incident_duration_seconds": incident.get(
                            "duration_seconds"
                        ),
                        "end_to_end_recovery_seconds": round(
                            elapsed_seconds, 2
                        ),
                        "remediation_attempts": len(attempts),
                        "successful_remediations": successful_attempts,
                    }

                    print(json.dumps(report, indent=2))
                    test_passed = True
                    return 0

            time.sleep(POLL_INTERVAL_SECONDS)

        raise TimeoutError(
            f"Self-healing did not complete within {TIMEOUT_SECONDS} seconds."
        )

    except Exception as error:
        print(f"RESILIENCE TEST FAILED: {error}", file=sys.stderr)
        return 1

    finally:
        if stop_requested and not test_passed:
            try:
                if not container_is_running():
                    print(
                        "Test did not pass. Attempting to restore the demo "
                        "container...",
                        file=sys.stderr,
                    )
                    subprocess.run(
                        ["docker", "start", CONTAINER_NAME],
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )
            except Exception as cleanup_error:
                print(
                    f"WARNING: Could not restore the container: "
                    f"{cleanup_error}",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    raise SystemExit(main())
