from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.monitoring import monitoring_manager

from app.incidents import incident_manager

from app.policy_engine import policy_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
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
