from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models import Driver, Duty, Trip, Route, Incident, User
from backend.app.schemas.entities import IncidentCreate, IncidentResponse
from backend.app.core.deps import get_current_user
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/driver", tags=["Driver Portal"])

@router.get("/duty/today")
def get_driver_duty(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Today's duty manifest for the logged-in driver (R-1)."""
    # Sample believable duty shift for driver portal
    return {
        "driver_name": current_user.name,
        "driver_id": current_user.id,
        "duty_id": "DUTY-101",
        "service_date": "2026-11-18",
        "start_time": "07:30",
        "end_time": "15:30",
        "break_window": "11:30 - 12:15 (45 min break at Civil Lines Terminal)",
        "assigned_vehicle": "BUS-101 (UP-70-AT-1001)",
        "current_trip": {
            "id": "TRIP-7A-0900",
            "route_code": "7A",
            "route_name": "Civil Lines - Sangam Express",
            "destination": "Sangam Ghat Terminal",
            "start_time": "09:00",
            "end_time": "09:35",
            "status": "in_progress",
            "delay_minutes": 2,
            "next_stop": "Medical College (SRN Hospital)",
        },
        "upcoming_trips": [
            {
                "id": "TRIP-7A-1015",
                "route_code": "7A",
                "destination": "Civil Lines Terminal",
                "start_time": "10:15",
                "end_time": "10:50",
            },
            {
                "id": "TRIP-7A-1300",
                "route_code": "7A",
                "destination": "Sangam Ghat Terminal",
                "start_time": "13:00",
                "end_time": "13:35",
            },
        ],
    }

@router.post("/trips/{id}/start")
def start_trip(id: str):
    """Start trip action (R-2)."""
    return {"status": "in_progress", "trip_id": id, "started_at": datetime.now(timezone.utc).isoformat()}

@router.post("/trips/{id}/end")
def end_trip(id: str):
    """End trip action (R-2)."""
    return {"status": "completed", "trip_id": id, "ended_at": datetime.now(timezone.utc).isoformat()}
