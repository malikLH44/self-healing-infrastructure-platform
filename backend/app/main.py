from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import (
    authenticate_user,
    create_access_token,
    create_admin_user,
    get_current_user,
    get_db,
)
from app.database import init_db
from app.incidents import incident_manager
from app.monitoring import monitoring_manager
from app.policy_engine import policy_engine
from app.resource_alerts import resource_alert_manager
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import Response
from time import perf_counter

from app.prometheus_metrics import (
    CONTENT_TYPE_LATEST,
    generate_metrics,
    record_http_request,
    refresh_ship_metrics,
)



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    create_admin_user()
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


@app.middleware("http")
async def collect_prometheus_metrics(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    started_at = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")

        record_http_request(
            method=request.method,
            path=path,
            status_code=status_code,
            duration_seconds=perf_counter() - started_at,
        )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
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


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    refresh_ship_metrics(
        services=list(monitoring_manager.latest_status.values()),
        incidents=incident_manager.list_incidents(),
        alerts=resource_alert_manager.list_alerts(),
    )

    return Response(
        content=generate_metrics(),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )


@app.post("/auth/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.username)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/auth/me")
def read_current_user(
    current_user=Depends(get_current_user),
):
    return {
        "username": current_user.username,
        "is_active": current_user.is_active,
    }


@app.get("/services", dependencies=[Depends(get_current_user)])
def get_services():
    return {
        "services": list(monitoring_manager.latest_status.values())
    }


@app.get("/services/{service_name}", dependencies=[Depends(get_current_user)])
def get_service(service_name: str):
    result = monitoring_manager.latest_status.get(service_name)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No monitoring result available for '{service_name}'",
        )

    return result

@app.get("/incidents", dependencies=[Depends(get_current_user)])
def get_incidents():
    return {
        "incidents": incident_manager.list_incidents()
    }


@app.get("/resource-alerts", dependencies=[Depends(get_current_user)])
def get_resource_alerts():
    return {
        "alerts": resource_alert_manager.list_alerts()
    }


@app.get("/resource-alerts/active", dependencies=[Depends(get_current_user)])
def get_active_resource_alerts():
    return {
        "alerts": resource_alert_manager.get_active_alerts()
    }

@app.get("/dashboard/summary", dependencies=[Depends(get_current_user)])
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


@app.get("/incidents/{incident_id}/policy", dependencies=[Depends(get_current_user)])
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
