import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="passenger")  # admin, dispatcher, driver
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    driver_profile = relationship("Driver", back_populates="user", uselist=False)

class Stop(Base):
    __tablename__ = "stops"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(20), unique=True, index=True, nullable=False)  # S014
    name = Column(String(150), index=True, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    is_accessible = Column(Boolean, default=True, nullable=False)
    has_shelter = Column(Boolean, default=True, nullable=False)
    landmark_note = Column(String(255), nullable=True)

    route_stops = relationship("RouteStop", back_populates="stop")

class Route(Base):
    __tablename__ = "routes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    short_name = Column(String(20), unique=True, index=True, nullable=False)  # 7A
    long_name = Column(String(255), nullable=False)
    color_hex = Column(String(10), nullable=False, default="#2563EB")
    is_active = Column(Boolean, default=True, nullable=False)
    route_type = Column(String(20), default="city", nullable=False)  # city, express, feeder

    route_stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan")
    paths = relationship("RoutePath", back_populates="route", cascade="all, delete-orphan")
    frequency_bands = relationship("FrequencyBand", back_populates="route", cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="route")

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), index=True, nullable=False)
    direction = Column(Integer, default=0, nullable=False)  # 0 or 1
    sequence = Column(Integer, nullable=False)  # 1, 2, 3...
    stop_id = Column(String(36), ForeignKey("stops.id"), index=True, nullable=False)
    dwell_seconds = Column(Integer, default=30, nullable=False)
    distance_from_prev_m = Column(Float, default=0.0, nullable=False)
    scheduled_offset_s = Column(Integer, default=0, nullable=False)  # seconds from start of trip

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")

class RoutePath(Base):
    __tablename__ = "route_paths"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), index=True, nullable=False)
    direction = Column(Integer, default=0, nullable=False)
    polyline = Column(JSON, nullable=False)  # list of [lat, lng] coordinates

    route = relationship("Route", back_populates="paths")

class ServiceCalendar(Base):
    __tablename__ = "service_calendars"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(50), nullable=False)  # Weekday, Saturday, Sunday/Holiday
    days_of_week = Column(Integer, default=127, nullable=False)  # bitmask (e.g. 1-5 for Mon-Fri)

    frequency_bands = relationship("FrequencyBand", back_populates="calendar")
    trips = relationship("Trip", back_populates="calendar")

class FrequencyBand(Base):
    __tablename__ = "frequency_bands"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id", ondelete="CASCADE"), index=True, nullable=False)
    direction = Column(Integer, default=0, nullable=False)
    calendar_id = Column(String(36), ForeignKey("service_calendars.id"), index=True, nullable=False)
    start_s = Column(Integer, nullable=False)  # seconds after midnight (e.g. 21600 for 06:00)
    end_s = Column(Integer, nullable=False)    # e.g. 36000 for 10:00
    headway_min = Column(Integer, nullable=False)  # headway in minutes

    route = relationship("Route", back_populates="frequency_bands")
    calendar = relationship("ServiceCalendar", back_populates="frequency_bands")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    fleet_no = Column(String(50), unique=True, index=True, nullable=False)
    plate = Column(String(50), nullable=False)
    type = Column(String(50), default="standard", nullable=False)  # midi, standard, articulated, electric
    capacity_seated = Column(Integer, default=36, nullable=False)
    capacity_standing = Column(Integer, default=24, nullable=False)
    is_accessible = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, maintenance, breakdown, retired
    depot = Column(String(100), default="Main Depot", nullable=False)

    blocks = relationship("Block", back_populates="vehicle")
    positions = relationship("VehiclePosition", back_populates="vehicle")

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    license_no = Column(String(50), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    max_duty_minutes = Column(Integer, default=480, nullable=False)  # 8 hours default
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="driver_profile")
    duties = relationship("Duty", back_populates="driver")

class Block(Base):
    __tablename__ = "blocks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    service_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=True, index=True)
    name = Column(String(50), nullable=False)

    vehicle = relationship("Vehicle", back_populates="blocks")
    trips = relationship("Trip", back_populates="block")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id"), index=True, nullable=False)
    direction = Column(Integer, default=0, nullable=False)
    service_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    calendar_id = Column(String(36), ForeignKey("service_calendars.id"), nullable=False)
    start_s = Column(Integer, nullable=False)  # seconds after midnight
    end_s = Column(Integer, nullable=False)
    status = Column(String(20), default="scheduled", nullable=False)  # scheduled, in_progress, completed, cancelled
    block_id = Column(String(36), ForeignKey("blocks.id"), nullable=True, index=True)

    route = relationship("Route", back_populates="trips")
    calendar = relationship("ServiceCalendar", back_populates="trips")
    block = relationship("Block", back_populates="trips")
    stop_events = relationship("TripStopEvent", back_populates="trip")

class Duty(Base):
    __tablename__ = "duties"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    service_date = Column(String(10), index=True, nullable=False)  # YYYY-MM-DD
    driver_id = Column(String(36), ForeignKey("drivers.id"), nullable=False, index=True)
    start_s = Column(Integer, nullable=False)
    end_s = Column(Integer, nullable=False)
    break_start_s = Column(Integer, nullable=True)
    break_end_s = Column(Integer, nullable=True)

    driver = relationship("Driver", back_populates="duties")
    duty_blocks = relationship("DutyBlock", back_populates="duty", cascade="all, delete-orphan")

class DutyBlock(Base):
    __tablename__ = "duty_blocks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    duty_id = Column(String(36), ForeignKey("duties.id"), nullable=False, index=True)
    block_id = Column(String(36), ForeignKey("blocks.id"), nullable=False, index=True)
    from_trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True)
    to_trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True)

    duty = relationship("Duty", back_populates="duty_blocks")

class VehiclePosition(Base):
    __tablename__ = "vehicle_positions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True, index=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    speed_kmph = Column(Float, default=25.0, nullable=False)
    heading = Column(Float, default=0.0, nullable=False)
    occupancy = Column(String(20), default="seats", nullable=False)  # empty, seats, standing, full
    delay_s = Column(Integer, default=0, nullable=False)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    vehicle = relationship("Vehicle", back_populates="positions")

class TripStopEvent(Base):
    __tablename__ = "trip_stop_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=False, index=True)
    stop_id = Column(String(36), ForeignKey("stops.id"), nullable=False, index=True)
    scheduled_s = Column(Integer, nullable=False)
    actual_s = Column(Integer, nullable=True)
    delay_s = Column(Integer, default=0, nullable=False)

    trip = relationship("Trip", back_populates="stop_events")

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(50), nullable=False)  # breakdown, accident, traffic, road_closure, driver_absent, other
    severity = Column(String(20), default="med", nullable=False)  # low, med, high
    vehicle_id = Column(String(36), ForeignKey("vehicles.id"), nullable=True, index=True)
    trip_id = Column(String(36), ForeignKey("trips.id"), nullable=True)
    route_id = Column(String(36), ForeignKey("routes.id"), nullable=True)
    stop_id = Column(String(36), ForeignKey("stops.id"), nullable=True)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="open", nullable=False)  # open, acknowledged, resolved
    created_by = Column(String(100), default="system", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    route_id = Column(String(36), ForeignKey("routes.id"), nullable=True, index=True)
    stop_id = Column(String(36), ForeignKey("stops.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    severity = Column(String(20), default="warning", nullable=False)  # info, warning, severe
    starts_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ends_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), default="dispatcher", nullable=False)

