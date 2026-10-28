from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import Stop
from backend.app.schemas.entities import StopCreate, StopUpdate, StopResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.core.deps import require_role
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/stops", tags=["Stops"])

@router.get("", response_model=PaginatedResponse[StopResponse])
def list_stops(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    q: Optional[str] = None,
    accessible_only: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Stop)
    if q:
        query = query.filter(Stop.name.ilike(f"%{q}%") | Stop.code.ilike(f"%{q}%"))
    if accessible_only:
        query = query.filter(Stop.is_accessible == True)

    total = query.count()
    items = query.order_by(Stop.code).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/{id}", response_model=StopResponse)
def get_stop(id: str, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter((Stop.id == id) | (Stop.code == id)).first()
    if not stop:
        raise WaylineError(code="STOP_NOT_FOUND", message=f"Stop {id} not found.", status_code=404)
    return stop

@router.post("", response_model=StopResponse, dependencies=[Depends(require_role(["admin"]))])
def create_stop(payload: StopCreate, db: Session = Depends(get_db)):
    existing = db.query(Stop).filter(Stop.code == payload.code).first()
    if existing:
        raise WaylineError(code="STOP_EXISTS", message=f"Stop with code {payload.code} already exists.")
    stop = Stop(**payload.model_dump())
    db.add(stop)
    db.commit()
    db.refresh(stop)
    return stop

@router.patch("/{id}", response_model=StopResponse, dependencies=[Depends(require_role(["admin"]))])
def update_stop(id: str, payload: StopUpdate, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter(Stop.id == id).first()
    if not stop:
        raise WaylineError(code="STOP_NOT_FOUND", message=f"Stop {id} not found.", status_code=404)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(stop, field, value)
    db.commit()
    db.refresh(stop)
    return stop

@router.delete("/{id}", dependencies=[Depends(require_role(["admin"]))])
def delete_stop(id: str, db: Session = Depends(get_db)):
    stop = db.query(Stop).filter(Stop.id == id).first()
    if not stop:
        raise WaylineError(code="STOP_NOT_FOUND", message=f"Stop {id} not found.", status_code=404)
    db.delete(stop)
    db.commit()
    return {"status": "deleted", "id": id}

