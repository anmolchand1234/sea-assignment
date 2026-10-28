from pydantic import BaseModel, Field
from typing import Optional, List, Any

# Stop Schemas
class StopBase(BaseModel):
    code: str
    name: str
    lat: float
    lng: float
    is_accessible: bool = True
    has_shelter: bool = True
    landmark_note: Optional[str] = None

class StopCreate(StopBase):
    pass

class StopUpdate(BaseModel):
    name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_accessible: Optional[bool] = None
    has_shelter: Optional[bool] = None
    landmark_note: Optional[str] = None

class StopResponse(StopBase):
    id: str

    class Config:
        from_attributes = True

# Route Schemas
class RouteStopItem(BaseModel):
    stop_id: str
    direction: int = 0
    sequence: int
    dwell_seconds: int = 30
    distance_from_prev_m: float = 0.0
    scheduled_offset_s: int = 0

class RouteBase(BaseModel):
    short_name: str
    long_name: str
    color_hex: str = "#2563EB"
    is_active: bool = True
    route_type: str = "city"

class RouteCreate(RouteBase):
    stops: Optional[List[RouteStopItem]] = None
    polyline: Optional[List[List[float]]] = None

class RouteResponse(RouteBase):
    id: str

    class Config:
        from_attributes = True

# Vehicle Schemas
class VehicleBase(BaseModel):
    fleet_no: str
    plate: str
    type: str = "standard"
    capacity_seated: int = 36
    capacity_standing: int = 24
    is_accessible: bool = True
    status: str = "active"
    depot: str = "Main Depot"

class VehicleCreate(VehicleBase):
    pass

class VehicleUpdate(BaseModel):
    status: Optional[str] = None
    depot: Optional[str] = None
    is_accessible: Optional[bool] = None

class VehicleResponse(VehicleBase):
    id: str

    class Config:
        from_attributes = True

# Driver Schemas
class DriverBase(BaseModel):
    name: str
    license_no: str
    phone: str
    max_duty_minutes: int = 480
    is_active: bool = True

class DriverCreate(DriverBase):
    user_id: Optional[str] = None

class DriverResponse(DriverBase):
    id: str
    user_id: Optional[str] = None

    class Config:
        from_attributes = True

# Incident & Alert Schemas
class IncidentCreate(BaseModel):
    type: str  # breakdown, accident, traffic, road_closure, driver_absent, other
    severity: str = "med"
    vehicle_id: Optional[str] = None
    trip_id: Optional[str] = None
    route_id: Optional[str] = None
    stop_id: Optional[str] = None
    description: str

class IncidentResponse(BaseModel):
    id: str
    type: str
    severity: str
    vehicle_id: Optional[str] = None
    trip_id: Optional[str] = None
    route_id: Optional[str] = None
    stop_id: Optional[str] = None
    description: str
    status: str
    created_at: Any
    resolved_at: Optional[Any] = None

    class Config:
        from_attributes = True

class AlertCreate(BaseModel):
    route_id: Optional[str] = None
    stop_id: Optional[str] = None
    title: str
    body: str
    severity: str = "warning"

class AlertResponse(BaseModel):
    id: str
    route_id: Optional[str] = None
    stop_id: Optional[str] = None
    title: str
    body: str
    severity: str
    starts_at: Any
    ends_at: Optional[Any] = None

    class Config:
        from_attributes = True

