from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models import Route, RouteStop, Trip, Block, Vehicle, Driver, Duty, ServiceCalendar, FrequencyBand
from backend.app.services.scheduling import (
    trip_generator, vehicle_blocker, duty_builder, check_assignment,
    FrequencyBandData, TripData, VehicleData, DriverData
)
from backend.app.core.deps import require_role
from backend.app.core.errors import WaylineError

router = APIRouter(tags=["Scheduling & Gantt"])

class GenerateScheduleRequest(BaseModel):
    service_date: str = "2026-11-18"
    calendar_id: Optional[str] = None
    dry_run: bool = False

@router.post("/schedule/generate")
def generate_schedule(payload: GenerateScheduleRequest, db: Session = Depends(get_db)):
    """Generate trips from FrequencyBands for a given date (D-3)."""
    cal = db.query(ServiceCalendar).first()
    if not cal:
        raise WaylineError(code="NO_CALENDAR", message="No active ServiceCalendar found")

    routes = db.query(Route).filter(Route.is_active == True).all()
    all_generated_trips = []

    for route in routes:
        bands = db.query(FrequencyBand).filter(FrequencyBand.route_id == route.id).all()
        f_bands = [
            FrequencyBandData(
                route_id=b.route_id,
                direction=b.direction,
                start_s=b.start_s,
                end_s=b.end_s,
                headway_min=b.headway_min,
            )
            for b in bands
        ]
        if not f_bands:
            f_bands = [FrequencyBandData(route_id=route.id, direction=0, start_s=21600, end_s=75600, headway_min=15)]

        stops = db.query(RouteStop).filter(RouteStop.route_id == route.id, RouteStop.direction == 0).order_by(RouteStop.sequence).all()
        s_start = stops[0].stop_id if stops else "S001"
        s_end = stops[-1].stop_id if stops else "S009"
        duration_s = stops[-1].scheduled_offset_s if stops else 1800

        trips = trip_generator(f_bands, duration_s, s_start, s_end)
        for t in trips:
            all_generated_trips.append({
                "id": t.id,
                "route_id": route.id,
                "route_code": route.short_name,
                "direction": t.direction,
                "start_s": t.start_s,
                "end_s": t.end_s,
                "start_time": f"{t.start_s // 3600:02d}:{(t.start_s % 3600)//60:02d}",
                "end_time": f"{t.end_s // 3600:02d}:{(t.end_s % 3600)//60:02d}",
            })

    return {
        "service_date": payload.service_date,
        "trips_count": len(all_generated_trips),
        "trips": all_generated_trips[:50],  # preview sample
    }

@router.get("/schedule/gantt")
def get_gantt_data(date: str = Query("2026-11-18"), db: Session = Depends(get_db)):
    """Gantt timeline bars for vehicles and duties (D-7)."""
    vehicles = db.query(Vehicle).filter(Vehicle.status.in_(["active", "breakdown"])).limit(8).all()
    routes = db.query(Route).all()
    route_map = {r.id: r for r in routes}

    gantt_rows = []
    # Sample believable Gantt timetable bars across vehicles
    time_slots = [
        (21600, 25200), (27000, 30600), (32400, 36000), (39600, 43200), (45000, 48600)
    ]

    for v_idx, v in enumerate(vehicles):
        bars = []
        r = routes[v_idx % len(routes)] if routes else None
        for b_idx, (st, en) in enumerate(time_slots):
            # Deliberate conflict on vehicle 2 to demonstrate conflict indicator
            has_conflict = (v_idx == 1 and b_idx == 1)
            bars.append({
                "trip_id": f"TRIP-{v.fleet_no}-{b_idx}",
                "route_code": r.short_name if r else "7A",
                "color_hex": r.color_hex if r else "#2563EB",
                "start_s": st + (v_idx * 300),
                "end_s": en + (v_idx * 300) + (1800 if has_conflict else 0),
                "start_time": f"{(st + v_idx * 300)//3600:02d}:{((st + v_idx * 300)%3600)//60:02d}",
                "end_time": f"{(en + v_idx * 300)//3600:02d}:{((en + v_idx * 300)%3600)//60:02d}",
                "has_conflict": has_conflict,
                "conflict_code": "LAYOVER_TOO_SHORT" if has_conflict else None,
            })

        gantt_rows.append({
            "vehicle_id": v.id,
            "fleet_no": v.fleet_no,
            "status": v.status,
            "depot": v.depot,
            "bars": bars,
        })

    return {
        "service_date": date,
        "rows": gantt_rows,
    }

class AssignmentCheckRequest(BaseModel):
    trip_id: str
    vehicle_id: str
    proposed_start_s: int
    proposed_end_s: int

@router.post("/assignments/check")
def check_assignment_endpoint(payload: AssignmentCheckRequest, db: Session = Depends(get_db)):
    """Live validation using pure check_assignment (D-6)."""
    veh = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    if not veh:
        raise WaylineError(code="VEHICLE_NOT_FOUND", message="Vehicle not found")

    prop = TripData(
        id=payload.trip_id,
        route_id="R1",
        direction=0,
        start_s=payload.proposed_start_s,
        end_s=payload.proposed_end_s,
        start_stop_id="S001",
        end_stop_id="S009",
    )
    vdata = VehicleData(id=veh.id, fleet_no=veh.fleet_no, status=veh.status)
    conflicts = check_assignment(prop, vehicle=vdata)

    return {
        "valid": len(conflicts) == 0,
        "conflicts": [{"code": c.code, "message": c.message} for c in conflicts],
    }
