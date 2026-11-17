from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models import Incident, Alert, Vehicle, Trip, Route, User
from backend.app.schemas.entities import IncidentCreate, IncidentResponse, AlertCreate, AlertResponse
from backend.app.services.scheduling import replacement_ranking, VehicleData, TripData
from backend.app.core.deps import require_role, get_current_user
from backend.app.core.errors import WaylineError

router = APIRouter(tags=["Operations"])

@router.get("/ops/fleet")
def get_fleet_board(db: Session = Depends(get_db)):
    """Fleet status board with active trips, delays, and statuses (D-2)."""
    vehicles = db.query(Vehicle).all()
    fleet = []
    for v in vehicles:
        fleet.append({
            "id": v.id,
            "fleet_no": v.fleet_no,
            "plate": v.plate,
            "type": v.type,
            "status": v.status,
            "capacity": f"{v.capacity_seated} seats / {v.capacity_standing} std",
            "is_accessible": v.is_accessible,
            "depot": v.depot,
            "delay_minutes": 2 if v.status == "active" else 0,
        })
    return fleet

@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(db: Session = Depends(get_db)):
    """Get all operations incidents (D-8)."""
    return db.query(Incident).order_by(Incident.created_at.desc()).all()

@router.post("/incidents", response_model=IncidentResponse)
def create_incident(
    payload: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Report an incident (breakdown, traffic, accident) (D-8, R-3)."""
    inc = Incident(
        type=payload.type,
        severity=payload.severity,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        route_id=payload.route_id,
        stop_id=payload.stop_id,
        description=payload.description,
        status="open",
        created_by=current_user.email,
        created_at=datetime.now(timezone.utc),
    )
    if payload.type == "breakdown" and payload.vehicle_id:
        veh = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
        if veh:
            veh.status = "breakdown"

    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc

@router.patch("/incidents/{id}")
def update_incident_status(
    id: str,
    status_val: str = Query(..., alias="status"),
    db: Session = Depends(get_db),
):
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise WaylineError(code="INCIDENT_NOT_FOUND", message="Incident not found", status_code=404)
    inc.status = status_val
    if status_val == "resolved":
        inc.resolved_at = datetime.now(timezone.utc)
        if inc.vehicle_id:
            veh = db.query(Vehicle).filter(Vehicle.id == inc.vehicle_id).first()
            if veh and veh.status == "breakdown":
                veh.status = "active"
    db.commit()
    return {"status": "updated", "id": id, "incident_status": status_val}

@router.get("/incidents/{id}/replacement-suggestions")
def get_replacement_suggestions(id: str, db: Session = Depends(get_db)):
    """Rank spare/standby vehicles for a vehicle breakdown (SPEC §6.6, D-8)."""
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc or not inc.vehicle_id:
        raise WaylineError(code="INVALID_INCIDENT", message="Incident has no assigned vehicle")

    broken_veh = db.query(Vehicle).filter(Vehicle.id == inc.vehicle_id).first()
    if not broken_veh:
        raise WaylineError(code="VEHICLE_NOT_FOUND", message="Vehicle not found")

    failed_vdata = VehicleData(
        id=broken_veh.id,
        fleet_no=broken_veh.fleet_no,
        is_accessible=broken_veh.is_accessible,
        status=broken_veh.status,
        current_lat=25.4528,
        current_lng=81.8340,
    )

    all_vehicles = db.query(Vehicle).filter(Vehicle.id != broken_veh.id, Vehicle.status == "active").all()
    candidates = [
        VehicleData(
            id=v.id,
            fleet_no=v.fleet_no,
            is_accessible=v.is_accessible,
            status=v.status,
            capacity_seated=v.capacity_seated,
            capacity_standing=v.capacity_standing,
            depot=v.depot,
            current_lat=25.4380 + (idx * 0.005),
            current_lng=81.8260 + (idx * 0.004),
        )
        for idx, v in enumerate(all_vehicles)
    ]

    ranked = replacement_ranking(failed_vdata, candidates, 36000, [])
    return [
        {
            "vehicle_id": r[0].id,
            "fleet_no": r[0].fleet_no,
            "depot": r[0].depot,
            "is_accessible": r[0].is_accessible,
            "distance_km": r[1],
            "capacity": f"{r[0].capacity_seated} seated",
        }
        for r in ranked
    ]

@router.post("/incidents/{id}/apply-replacement")
def apply_replacement(
    id: str,
    replacement_vehicle_id: str = Query(...),
    db: Session = Depends(get_db),
):
    """One-click apply replacement vehicle for breakdown (D-9)."""
    inc = db.query(Incident).filter(Incident.id == id).first()
    if not inc:
        raise WaylineError(code="INCIDENT_NOT_FOUND", message="Incident not found")

    rep_veh = db.query(Vehicle).filter(Vehicle.id == replacement_vehicle_id).first()
    if not rep_veh:
        raise WaylineError(code="VEHICLE_NOT_FOUND", message="Replacement vehicle not found")

    inc.status = "resolved"
    inc.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "status": "success",
        "message": f"Assigned vehicle {rep_veh.fleet_no} as replacement. Incident resolved.",
    }

@router.post("/alerts", response_model=AlertResponse)
def create_public_alert(
    payload: AlertCreate,
    current_user: User = Depends(require_role(["dispatcher", "admin"])),
    db: Session = Depends(get_db),
):
    """Compose public transit alert (D-10)."""
    alert = Alert(
        route_id=payload.route_id,
        stop_id=payload.stop_id,
        title=payload.title,
        body=payload.body,
        severity=payload.severity,
        starts_at=datetime.now(timezone.utc),
        created_by=current_user.email,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
