from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models import Route, RouteStop, RoutePath, Stop
from backend.app.schemas.entities import RouteCreate, RouteResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.core.deps import require_role
from backend.app.core.errors import WaylineError

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.get("", response_model=PaginatedResponse[RouteResponse])
def list_routes(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    query = db.query(Route)
    if active_only:
        query = query.filter(Route.is_active == True)
    total = query.count()
    items = query.order_by(Route.short_name).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

@router.get("/{id}")
def get_route_details(id: str, db: Session = Depends(get_db)):
    route = db.query(Route).filter((Route.id == id) | (Route.short_name == id)).first()
    if not route:
        raise WaylineError(code="ROUTE_NOT_FOUND", message=f"Route {id} not found.", status_code=404)

    # Fetch stops per direction
    stops_dir0 = (
        db.query(RouteStop, Stop)
        .join(Stop, RouteStop.stop_id == Stop.id)
        .filter(RouteStop.route_id == route.id, RouteStop.direction == 0)
        .order_by(RouteStop.sequence)
        .all()
    )
    stops_dir1 = (
        db.query(RouteStop, Stop)
        .join(Stop, RouteStop.stop_id == Stop.id)
        .filter(RouteStop.route_id == route.id, RouteStop.direction == 1)
        .order_by(RouteStop.sequence)
        .all()
    )

    path = db.query(RoutePath).filter(RoutePath.route_id == route.id).first()

    return {
        "id": route.id,
        "short_name": route.short_name,
        "long_name": route.long_name,
        "color_hex": route.color_hex,
        "route_type": route.route_type,
        "polyline": path.polyline if path else [],
        "direction_0_stops": [
            {
                "stop_id": s.id,
                "code": s.code,
                "name": s.name,
                "lat": s.lat,
                "lng": s.lng,
                "sequence": rs.sequence,
                "dwell_seconds": rs.dwell_seconds,
                "offset_s": rs.scheduled_offset_s,
            }
            for rs, s in stops_dir0
        ],
        "direction_1_stops": [
            {
                "stop_id": s.id,
                "code": s.code,
                "name": s.name,
                "lat": s.lat,
                "lng": s.lng,
                "sequence": rs.sequence,
                "dwell_seconds": rs.dwell_seconds,
                "offset_s": rs.scheduled_offset_s,
            }
            for rs, s in stops_dir1
        ],
    }

@router.post("", response_model=RouteResponse, dependencies=[Depends(require_role(["admin"]))])
def create_route(payload: RouteCreate, db: Session = Depends(get_db)):
    existing = db.query(Route).filter(Route.short_name == payload.short_name).first()
    if existing:
        raise WaylineError(code="ROUTE_EXISTS", message=f"Route with code {payload.short_name} already exists.")
    
    route = Route(
        short_name=payload.short_name,
        long_name=payload.long_name,
        color_hex=payload.color_hex,
        is_active=payload.is_active,
        route_type=payload.route_type,
    )
    db.add(route)
    db.flush()

    if payload.polyline:
        path = RoutePath(route_id=route.id, direction=0, polyline=payload.polyline)
        db.add(path)

    if payload.stops:
        for item in payload.stops:
            rs = RouteStop(
                route_id=route.id,
                direction=item.direction,
                sequence=item.sequence,
                stop_id=item.stop_id,
                dwell_seconds=item.dwell_seconds,
                distance_from_prev_m=item.distance_from_prev_m,
                scheduled_offset_s=item.scheduled_offset_s,
            )
            db.add(rs)

    db.commit()
    db.refresh(route)
    return route

