from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import Route, Vehicle, Incident

router = APIRouter(prefix="/reports", tags=["Reports & Analytics"])

@router.get("/on-time")
def get_on_time_performance(format: str = Query("json")):
    """On-time performance report (A-3)."""
    data = [
        {"route": "7A", "on_time_pct": 92.4, "avg_delay_min": 2.1, "total_trips": 64},
        {"route": "14", "on_time_pct": 88.5, "avg_delay_min": 3.8, "total_trips": 52},
        {"route": "21E", "on_time_pct": 94.0, "avg_delay_min": 1.6, "total_trips": 48},
        {"route": "5B", "on_time_pct": 86.2, "avg_delay_min": 4.5, "total_trips": 36},
        {"route": "AIR-1", "on_time_pct": 97.5, "avg_delay_min": 0.8, "total_trips": 28},
        {"route": "N1", "on_time_pct": 98.0, "avg_delay_min": 0.5, "total_trips": 16},
    ]
    if format == "csv":
        csv_text = "Route,OnTimePercent,AvgDelayMin,TotalTrips\n" + "\n".join(
            f"{d['route']},{d['on_time_pct']},{d['avg_delay_min']},{d['total_trips']}" for d in data
        )
        return Response(content=csv_text, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=on_time_report.csv"})
    return data

@router.get("/utilisation")
def get_fleet_utilisation():
    """Fleet utilisation statistics (A-3)."""
    return {
        "total_fleet": 16,
        "active_in_service": 14,
        "under_maintenance": 1,
        "retired": 1,
        "fleet_utilisation_pct": 87.5,
        "avg_operating_hours_per_vehicle": 9.4,
    }
