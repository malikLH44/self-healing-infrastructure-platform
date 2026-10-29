from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.monitoring import monitoring_manager

from app.incidents import incident_manager

from app.policy_engine import policy_engine

from app.database import init_db

from fastapi.middleware.cors import CORSMiddleware



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    policy_engine.load_policies()
    await monitoring_manager.start()
    try:
        yield
    finally:
        await monitoring_manager.stop()



app = FastAPI(
    title="SHIP API",
    description="Self-Healing Infrastructure Platform",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "Welcome to SHIP",
        "version": "0.2.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ship-api",
    }


@app.get("/services")
def get_services():
    return {
        "services": list(monitoring_manager.latest_status.values())
    }


@app.get("/services/{service_name}")
def get_service(service_name: str):
    result = monitoring_manager.latest_status.get(service_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No monitoring result available for '{service_name}'",
        )

    return result

@app.get("/incidents")
def get_incidents():
    return {
        "incidents": incident_manager.list_incidents()
    }


@app.get("/incidents/active")
def get_active_incidents():
    return {
        "incidents": incident_manager.get_active_incidents()
    }


@app.get("/dashboard/summary")
def get_dashboard_summary():
    services = list(monitoring_manager.latest_status.values())
    incidents = incident_manager.list_incidents()

    healthy_services = sum(
        1 for service in services if service["status"] == "healthy"
    )
    unhealthy_services = len(services) - healthy_services

    active_incidents = sum(
        1 for incident in incidents if incident["status"] == "open"
    )
    resolved_incidents = sum(
        1 for incident in incidents if incident["status"] == "resolved"
    )

    remediation_attempts = [
        attempt
        for incident in incidents
        for attempt in incident.get("remediation_attempts", [])
    ]

    successful_remediations = sum(
        1 for attempt in remediation_attempts if attempt["success"]
    )
    total_remediations = len(remediation_attempts)

    return {
        "services": {
            "total": len(services),
            "healthy": healthy_services,
            "unhealthy": unhealthy_services,
        },
        "incidents": {
            "active": active_incidents,
            "resolved": resolved_incidents,
            "total": len(incidents),
        },
        "remediations": {
            "total": total_remediations,
            "successful": successful_remediations,
            "failed": total_remediations - successful_remediations,
            "success_rate": (
                round(successful_remediations / total_remediations * 100, 2)
                if total_remediations
                else None
            ),
        },
    }


@app.get("/incidents/{incident_id}/policy")
def evaluate_incident_policy(incident_id: str):
    incident = next(
        (
            item
            for item in incident_manager.list_incidents()
            if item["id"] == incident_id
        ),
        None,
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return policy_engine.evaluate(incident)
