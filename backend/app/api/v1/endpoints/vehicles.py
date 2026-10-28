from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import Vehicle
from backend.app.schemas.entities import VehicleCreate, VehicleUpdate, VehicleResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.core.deps import require_role
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("", response_model=PaginatedResponse[VehicleResponse])
def list_vehicles(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = None,
    accessible_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Vehicle)
    if status:
        query = query.filter(Vehicle.status == status)
    if accessible_only:
        query = query.filter(Vehicle.is_accessible == True)
    total = query.count()
    items = query.order_by(Vehicle.fleet_no).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/{id}", response_model=VehicleResponse)
def get_vehicle(id: str, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter((Vehicle.id == id) | (Vehicle.fleet_no == id)).first()
    if not v:
        raise WaylineError(code="VEHICLE_NOT_FOUND", message=f"Vehicle {id} not found.", status_code=404)
    return v

@router.post("", response_model=VehicleResponse, dependencies=[Depends(require_role(["admin"]))])
def create_vehicle(payload: VehicleCreate, db: Session = Depends(get_db)):
    existing = db.query(Vehicle).filter(Vehicle.fleet_no == payload.fleet_no).first()
    if existing:
        raise WaylineError(code="VEHICLE_EXISTS", message=f"Vehicle {payload.fleet_no} already exists.")
    v = Vehicle(**payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v

@router.patch("/{id}", response_model=VehicleResponse, dependencies=[Depends(require_role(["admin", "dispatcher"]))])
def update_vehicle(id: str, payload: VehicleUpdate, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(Vehicle.id == id).first()
    if not v:
        raise WaylineError(code="VEHICLE_NOT_FOUND", message=f"Vehicle {id} not found.", status_code=404)
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(v, field, val)
    db.commit()
    db.refresh(v)
    return v

