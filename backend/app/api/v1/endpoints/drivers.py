from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import Driver
from backend.app.schemas.entities import DriverCreate, DriverResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.core.deps import require_role
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("", response_model=PaginatedResponse[DriverResponse])
def list_drivers(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Driver)
    if active_only:
        query = query.filter(Driver.is_active == True)
    total = query.count()
    items = query.order_by(Driver.name).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/{id}", response_model=DriverResponse)
def get_driver(id: str, db: Session = Depends(get_db)):
    d = db.query(Driver).filter(Driver.id == id).first()
    if not d:
        raise WaylineError(code="DRIVER_NOT_FOUND", message=f"Driver {id} not found.", status_code=404)
    return d

@router.post("", response_model=DriverResponse, dependencies=[Depends(require_role(["admin"]))])
def create_driver(payload: DriverCreate, db: Session = Depends(get_db)):
    existing = db.query(Driver).filter(Driver.license_no == payload.license_no).first()
    if existing:
        raise WaylineError(code="DRIVER_EXISTS", message=f"Driver license {payload.license_no} already exists.")
    d = Driver(**payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d

