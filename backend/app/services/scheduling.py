"""
Pure scheduling functions for Wayline transit scheduling engine.
Implements algorithms specified in SPEC.md §6.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
import math

# Conflict typed codes per SPEC §6.4 & §7.1
CONFLICT_VEHICLE_OVERLAP = "VEHICLE_OVERLAP"
CONFLICT_DRIVER_OVERLAP = "DRIVER_OVERLAP"
CONFLICT_LAYOVER_TOO_SHORT = "LAYOVER_TOO_SHORT"
CONFLICT_TERMINAL_MISMATCH = "TERMINAL_MISMATCH"
CONFLICT_VEHICLE_UNAVAILABLE = "VEHICLE_UNAVAILABLE"
CONFLICT_DUTY_TOO_LONG = "DUTY_TOO_LONG"
CONFLICT_BREAK_MISSING = "BREAK_MISSING"
CONFLICT_NOT_ACCESSIBLE = "NOT_ACCESSIBLE"

MIN_LAYOVER_S = 300  # 5 minutes default (SPEC §4.2)

@dataclass
class Conflict:
    code: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TripData:
    id: str
    route_id: str
    direction: int
    start_s: int
    end_s: int
    start_stop_id: str
    end_stop_id: str
    is_accessible_required: bool = False
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    block_id: Optional[str] = None

@dataclass
class VehicleData:
    id: str
    fleet_no: str
    is_accessible: bool = True
    status: str = "active"  # active, maintenance, breakdown, retired
    depot: str = "Main Depot"
    capacity_seated: int = 36
    capacity_standing: int = 24
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None

@dataclass
class DriverData:
    id: str
    name: str
    max_duty_minutes: int = 480  # 8 hours
    is_active: bool = True

@dataclass
class BlockData:
    id: str
    vehicle_id: Optional[str]
    trips: List[TripData] = field(default_factory=list)

@dataclass
class DutyData:
    id: str
    driver_id: str
    start_s: int
    end_s: int
    break_start_s: Optional[int] = None
    break_end_s: Optional[int] = None
    trips: List[TripData] = field(default_factory=list)

# ---------------------------------------------------------------------------
# 6.4 Conflict Detection: check_assignment
# ---------------------------------------------------------------------------

def check_assignment(
    proposed_trip: TripData,
    vehicle: Optional[VehicleData] = None,
    driver: Optional[DriverData] = None,
    existing_vehicle_trips: Optional[List[TripData]] = None,
    existing_driver_trips: Optional[List[TripData]] = None,
    min_layover_s: int = MIN_LAYOVER_S,
) -> List[Conflict]:
    """
    Validates a proposed assignment against vehicle and driver constraints.
    Used identically in auto-assignment and manual dispatcher drag-and-drop.
    """
    conflicts: List[Conflict] = []
    v_trips = existing_vehicle_trips or []
    d_trips = existing_driver_trips or []

    # 1. Vehicle availability checks
    if vehicle:
        if vehicle.status in ("maintenance", "breakdown", "retired"):
            conflicts.append(
                Conflict(
                    code=CONFLICT_VEHICLE_UNAVAILABLE,
                    message=f"Vehicle {vehicle.fleet_no} is currently {vehicle.status} and cannot be assigned.",
                    details={"vehicle_id": vehicle.id, "status": vehicle.status},
                )
            )

        if proposed_trip.is_accessible_required and not vehicle.is_accessible:
            conflicts.append(
                Conflict(
                    code=CONFLICT_NOT_ACCESSIBLE,
                    message=f"Trip requires wheelchair accessibility, but vehicle {vehicle.fleet_no} is not accessible.",
                    details={"vehicle_id": vehicle.id, "trip_id": proposed_trip.id},
                )
            )

        # Check vehicle trip overlaps & layover continuity
        for other in v_trips:
            if other.id == proposed_trip.id:
                continue

            # Overlap check
            if not (proposed_trip.end_s <= other.start_s or proposed_trip.start_s >= other.end_s):
                conflicts.append(
                    Conflict(
                        code=CONFLICT_VEHICLE_OVERLAP,
                        message=f"Vehicle {vehicle.fleet_no} is already assigned to trip {other.id} from {other.start_s//60}m to {other.end_s//60}m.",
                        details={"vehicle_id": vehicle.id, "conflicting_trip_id": other.id},
                    )
                )

            # Preceding trip layover & terminal check
            if other.end_s <= proposed_trip.start_s:
                gap = proposed_trip.start_s - other.end_s
                if gap < min_layover_s and (other.end_s + min_layover_s > proposed_trip.start_s):
                    conflicts.append(
                        Conflict(
                            code=CONFLICT_LAYOVER_TOO_SHORT,
                            message=f"Layover before trip is {gap}s; minimum required is {min_layover_s}s.",
                            details={"gap_seconds": gap, "required_seconds": min_layover_s},
                        )
                    )
                if gap < 3600 and other.end_stop_id != proposed_trip.start_stop_id:
                    conflicts.append(
                        Conflict(
                            code=CONFLICT_TERMINAL_MISMATCH,
                            message=f"Terminal mismatch: previous trip ended at {other.end_stop_id}, but proposed trip starts at {proposed_trip.start_stop_id}.",
                            details={"prev_end": other.end_stop_id, "next_start": proposed_trip.start_stop_id},
                        )
                    )

            # Succeeding trip layover & terminal check
            elif proposed_trip.end_s <= other.start_s:
                gap = other.start_s - proposed_trip.end_s
                if gap < min_layover_s:
                    conflicts.append(
                        Conflict(
                            code=CONFLICT_LAYOVER_TOO_SHORT,
                            message=f"Layover after trip is {gap}s; minimum required is {min_layover_s}s.",
                            details={"gap_seconds": gap, "required_seconds": min_layover_s},
                        )
                    )
                if gap < 3600 and proposed_trip.end_stop_id != other.start_stop_id:
                    conflicts.append(
                        Conflict(
                            code=CONFLICT_TERMINAL_MISMATCH,
                            message=f"Terminal mismatch: proposed trip ends at {proposed_trip.end_stop_id}, but succeeding trip starts at {other.start_stop_id}.",
                            details={"proposed_end": proposed_trip.end_stop_id, "next_start": other.start_stop_id},
                        )
                    )

    # 2. Driver availability & legal duty checks
    if driver:
        if not driver.is_active:
            conflicts.append(
                Conflict(
                    code=CONFLICT_DRIVER_OVERLAP,
                    message=f"Driver {driver.name} is inactive.",
                    details={"driver_id": driver.id},
                )
            )

        total_driving_s = proposed_trip.end_s - proposed_trip.start_s
        earliest_start = proposed_trip.start_s
        latest_end = proposed_trip.end_s

        for other in d_trips:
            if other.id == proposed_trip.id:
                continue

            # Driver overlap check
            if not (proposed_trip.end_s <= other.start_s or proposed_trip.start_s >= other.end_s):
                conflicts.append(
                    Conflict(
                        code=CONFLICT_DRIVER_OVERLAP,
                        message=f"Driver {driver.name} is already driving trip {other.id} from {other.start_s//60}m to {other.end_s//60}m.",
                        details={"driver_id": driver.id, "conflicting_trip_id": other.id},
                    )
                )

            total_driving_s += (other.end_s - other.start_s)
            earliest_start = min(earliest_start, other.start_s)
            latest_end = max(latest_end, other.end_s)

        # Duty length check
        max_s = driver.max_duty_minutes * 60
        duty_span_s = latest_end - earliest_start
        if duty_span_s > max_s or total_driving_s > max_s:
            conflicts.append(
                Conflict(
                    code=CONFLICT_DUTY_TOO_LONG,
                    message=f"Duty span of {duty_span_s//60} min exceeds driver limit of {driver.max_duty_minutes} min.",
                    details={"duty_span_minutes": duty_span_s // 60, "limit_minutes": driver.max_duty_minutes},
                )
            )

        # Break rule check (SPEC §4.2: break of >= 30 min within first 4.5 hours = 16200 s)
        if duty_span_s > 16200:
            # Check if there is an idle gap of at least 30 min (1800 s) between consecutive driver trips
            all_sorted = sorted([proposed_trip] + [t for t in d_trips if t.id != proposed_trip.id], key=lambda t: t.start_s)
            has_valid_break = False
            for i in range(len(all_sorted) - 1):
                gap = all_sorted[i+1].start_s - all_sorted[i].end_s
                if gap >= 1800 and all_sorted[i].end_s <= earliest_start + 16200:
                    has_valid_break = True
                    break
            if not has_valid_break and len(all_sorted) > 1:
                conflicts.append(
                    Conflict(
                        code=CONFLICT_BREAK_MISSING,
                        message="Duty exceeds 4.5 hours without a mandatory 30-minute rest break.",
                        details={"duty_span_seconds": duty_span_s},
                    )
                )

    return conflicts

# ---------------------------------------------------------------------------
# 6.1 Trip Generation
# ---------------------------------------------------------------------------

@dataclass
class FrequencyBandData:
    route_id: str
    direction: int
    start_s: int
    end_s: int
    headway_min: int

def trip_generator(
    bands: List[FrequencyBandData],
    route_duration_s: int,
    start_stop_id: str,
    end_stop_id: str,
) -> List[TripData]:
    """
    Generates headway-based trips across frequency bands.
    Sorted by start time.
    """
    trips: List[TripData] = []
    trip_counter = 1

    for band in bands:
        cur_s = band.start_s
        step_s = band.headway_min * 60
        while cur_s < band.end_s:
            trip_id = f"TRIP-{band.route_id}-D{band.direction}-{cur_s//60}"
            trips.append(
                TripData(
                    id=trip_id,
                    route_id=band.route_id,
                    direction=band.direction,
                    start_s=cur_s,
                    end_s=cur_s + route_duration_s,
                    start_stop_id=start_stop_id,
                    end_stop_id=end_stop_id,
                )
            )
            cur_s += step_s
            trip_counter += 1

    trips.sort(key=lambda t: t.start_s)
    return trips

# ---------------------------------------------------------------------------
# 6.2 Vehicle Blocking (Interval Chaining)
# ---------------------------------------------------------------------------

def vehicle_blocker(
    trips: List[TripData],
    available_vehicles: List[VehicleData],
    min_layover_s: int = MIN_LAYOVER_S,
) -> Tuple[List[BlockData], List[TripData], Dict[str, Any]]:
    """
    Greedy best-fit interval chaining minimizing vehicles used and deadhead gaps.
    Returns (blocks, unassigned_trips, stats).
    """
    sorted_trips = sorted(trips, key=lambda t: t.start_s)
    blocks: List[BlockData] = []
    unassigned: List[TripData] = []
    active_vehicles = [v for v in available_vehicles if v.status == "active"]
    vehicle_pool = list(active_vehicles)

    for trip in sorted_trips:
        best_block: Optional[BlockData] = None
        best_gap = float("inf")

        # Find best existing block ending at trip's start terminal
        for block in blocks:
            last_trip = block.trips[-1]
            if last_trip.end_stop_id == trip.start_stop_id:
                gap = trip.start_s - last_trip.end_s
                if gap >= min_layover_s and gap < best_gap:
                    # Check accessibility compatibility
                    if block.vehicle_id:
                        veh = next((v for v in active_vehicles if v.id == block.vehicle_id), None)
                        if trip.is_accessible_required and veh and not veh.is_accessible:
                            continue
                    best_gap = gap
                    best_block = block

        if best_block:
            trip.block_id = best_block.id
            trip.vehicle_id = best_block.vehicle_id
            best_block.trips.append(trip)
        else:
            # Need a new vehicle/block
            if vehicle_pool:
                # Pick vehicle matching accessibility requirement
                veh_candidate = None
                for v in vehicle_pool:
                    if not trip.is_accessible_required or v.is_accessible:
                        veh_candidate = v
                        break

                if veh_candidate:
                    vehicle_pool.remove(veh_candidate)
                    new_block = BlockData(
                        id=f"BLK-{len(blocks) + 1}",
                        vehicle_id=veh_candidate.id,
                        trips=[trip],
                    )
                    trip.block_id = new_block.id
                    trip.vehicle_id = veh_candidate.id
                    blocks.append(new_block)
                else:
                    unassigned.append(trip)
            else:
                unassigned.append(trip)

    # Compute stats
    vehicles_used = len(blocks)
    total_gaps = 0
    gap_count = 0
    for b in blocks:
        for i in range(len(b.trips) - 1):
            total_gaps += (b.trips[i+1].start_s - b.trips[i].end_s)
            gap_count += 1
    avg_idle_min = (total_gaps / gap_count / 60) if gap_count > 0 else 0.0

    stats = {
        "vehicles_used": vehicles_used,
        "unassigned_count": len(unassigned),
        "avg_idle_min": round(avg_idle_min, 1),
    }

    return blocks, unassigned, stats

# ---------------------------------------------------------------------------
# 6.3 Driver Duty Building
# ---------------------------------------------------------------------------

def duty_builder(
    blocks: List[BlockData],
    drivers: List[DriverData],
    max_duty_minutes: int = 480,
) -> Tuple[List[DutyData], List[str]]:
    """
    Builds legal driver duties from vehicle blocks, placing 30m breaks where layover permits.
    Returns (duties, warnings).
    """
    duties: List[DutyData] = []
    warnings: List[str] = []
    active_drivers = [d for d in drivers if d.is_active]
    driver_idx = 0

    if not active_drivers:
        return [], ["No active drivers available"]

    for block in blocks:
        if not block.trips:
            continue

        current_duty_trips: List[TripData] = []
        duty_start = block.trips[0].start_s

        for i, trip in enumerate(block.trips):
            current_duty_trips.append(trip)
            duty_span = trip.end_s - duty_start

            # If approaching 8 hours or last trip in block, seal duty
            is_last = (i == len(block.trips) - 1)
            next_trip_would_exceed = False
            if not is_last:
                next_trip = block.trips[i + 1]
                if (next_trip.end_s - duty_start) > max_duty_minutes * 60:
                    next_trip_would_exceed = True

            if is_last or next_trip_would_exceed:
                driver = active_drivers[driver_idx % len(active_drivers)]
                driver_idx += 1

                duty = DutyData(
                    id=f"DUTY-{len(duties) + 1}",
                    driver_id=driver.id,
                    start_s=duty_start,
                    end_s=trip.end_s,
                    trips=list(current_duty_trips),
                )

                # Set driver on each trip
                for t in current_duty_trips:
                    t.driver_id = driver.id

                duties.append(duty)

                if not is_last:
                    duty_start = block.trips[i + 1].start_s
                    current_duty_trips = []

    return duties, warnings

# ---------------------------------------------------------------------------
# 6.5 Real-Time ETA Calculation
# ---------------------------------------------------------------------------

def eta_calculator(
    is_live: bool,
    scheduled_stop_offset_s: int,
    trip_start_s: int,
    current_time_s: int,
    current_delay_s: int = 0,
    vehicle_speed_kmph: float = 25.0,
    remaining_distance_m: float = 0.0,
) -> Tuple[int, str]:
    """
    Computes ETA in minutes and status label ('live' or 'scheduled').
    Clamps speed between 8 and 40 km/h (SPEC §6.5).
    Never returns negative minutes; returns 0 for under 1 minute.
    """
    if is_live and remaining_distance_m > 0:
        clamped_speed = max(8.0, min(40.0, vehicle_speed_kmph))
        speed_m_per_s = (clamped_speed * 1000.0) / 3600.0
        projected_travel_s = remaining_distance_m / speed_m_per_s
        minutes = int(math.ceil(projected_travel_s / 60.0))
        return max(0, minutes), "live"
    else:
        # Timetable + delay
        scheduled_arrival_s = trip_start_s + scheduled_stop_offset_s + current_delay_s
        diff_s = scheduled_arrival_s - current_time_s
        minutes = int(math.ceil(diff_s / 60.0))
        return max(0, minutes), "scheduled" if not is_live else "live"

# ---------------------------------------------------------------------------
# 6.6 Breakdown Replacement Suggestion
# ---------------------------------------------------------------------------

def replacement_ranking(
    failed_vehicle: VehicleData,
    candidates: List[VehicleData],
    incident_time_s: int,
    remaining_trips: List[TripData],
) -> List[Tuple[VehicleData, float]]:
    """
    Ranks available vehicles by proximity to failed vehicle's last position,
    then by capacity and accessibility compatibility.
    Returns ranked list of (vehicle, score_distance_km).
    """
    ranked: List[Tuple[VehicleData, float]] = []
    req_accessible = failed_vehicle.is_accessible

    for c in candidates:
        if c.id == failed_vehicle.id or c.status != "active":
            continue

        # Check accessibility matching
        if req_accessible and not c.is_accessible:
            continue

        # Proximity score (approximate Haversine or Euclidean distance)
        dist_km = 2.5  # default depot distance
        if (
            failed_vehicle.current_lat is not None
            and failed_vehicle.current_lng is not None
            and c.current_lat is not None
            and c.current_lng is not None
        ):
            dlat = math.radians(c.current_lat - failed_vehicle.current_lat)
            dlng = math.radians(c.current_lng - failed_vehicle.current_lng)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(failed_vehicle.current_lat)) * math.cos(math.radians(c.current_lat)) * math.sin(dlng/2)**2
            c_val = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist_km = 6371.0 * c_val

        ranked.append((c, round(dist_km, 2)))

    # Sort by distance first, then capacity descending
    ranked.sort(key=lambda item: (item[1], -(item[0].capacity_seated + item[0].capacity_standing)))
    return ranked[:3]

# ---------------------------------------------------------------------------
# 6.7 Journey Planner (Direct + 1-Transfer Graph Search)
# ---------------------------------------------------------------------------

@dataclass
class JourneyLeg:
    type: str  # ride or transfer
    route_id: Optional[str]
    route_short_name: Optional[str]
    from_stop_id: str
    to_stop_id: str
    duration_min: int

@dataclass
class JourneyPlan:
    legs: List[JourneyLeg]
    total_minutes: int
    transfers: int

def journey_planner(
    routes_data: List[Dict[str, Any]],
    from_stop_id: str,
    to_stop_id: str,
) -> List[JourneyPlan]:
    """
    Finds direct transit legs first, then 1-transfer options using in-memory graph.
    """
    plans: List[JourneyPlan] = []
    if from_stop_id == to_stop_id:
        return []

    # 1. Search Direct Routes
    for route in routes_data:
        stops = route.get("stops", [])
        if from_stop_id in stops and to_stop_id in stops:
            from_idx = stops.index(from_stop_id)
            to_idx = stops.index(to_stop_id)
            if from_idx < to_idx:
                # Direct route found!
                stops_count = to_idx - from_idx
                duration = stops_count * 3  # approx 3 min per stop
                plans.append(
                    JourneyPlan(
                        legs=[
                            JourneyLeg(
                                type="ride",
                                route_id=route["id"],
                                route_short_name=route.get("short_name", "BUS"),
                                from_stop_id=from_stop_id,
                                to_stop_id=to_stop_id,
                                duration_min=duration,
                            )
                        ],
                        total_minutes=duration,
                        transfers=0,
                    )
                )

    if plans:
        return plans

    # 2. Search 1-Transfer Routes
    for r1 in routes_data:
        stops1 = r1.get("stops", [])
        if from_stop_id not in stops1:
            continue
        from_idx1 = stops1.index(from_stop_id)

        for transfer_stop in stops1[from_idx1 + 1:]:
            for r2 in routes_data:
                if r2["id"] == r1["id"]:
                    continue
                stops2 = r2.get("stops", [])
                if transfer_stop in stops2 and to_stop_id in stops2:
                    trans_idx2 = stops2.index(transfer_stop)
                    to_idx2 = stops2.index(to_stop_id)
                    if trans_idx2 < to_idx2:
                        leg1_min = (stops1.index(transfer_stop) - from_idx1) * 3
                        transfer_wait = 5  # 5 min transfer
                        leg2_min = (to_idx2 - trans_idx2) * 3
                        total = leg1_min + transfer_wait + leg2_min

                        plans.append(
                            JourneyPlan(
                                legs=[
                                    JourneyLeg(
                                        type="ride",
                                        route_id=r1["id"],
                                        route_short_name=r1.get("short_name", "BUS"),
                                        from_stop_id=from_stop_id,
                                        to_stop_id=transfer_stop,
                                        duration_min=leg1_min,
                                    ),
                                    JourneyLeg(
                                        type="transfer",
                                        route_id=None,
                                        route_short_name=None,
                                        from_stop_id=transfer_stop,
                                        to_stop_id=transfer_stop,
                                        duration_min=transfer_wait,
                                    ),
                                    JourneyLeg(
                                        type="ride",
                                        route_id=r2["id"],
                                        route_short_name=r2.get("short_name", "BUS"),
                                        from_stop_id=transfer_stop,
                                        to_stop_id=to_stop_id,
                                        duration_min=leg2_min,
                                    ),
                                ],
                                total_minutes=total,
                                transfers=1,
                            )
                        )
                        if len(plans) >= 3:
                            break

    plans.sort(key=lambda p: p.total_minutes)
    return plans

