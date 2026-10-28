"""
Unit and property-based tests for Wayline scheduling algorithms.
Validates SPEC §6 and §12 backend requirements.
"""

import pytest
import random
from backend.app.services.scheduling import (
    check_assignment,
    trip_generator,
    vehicle_blocker,
    duty_builder,
    eta_calculator,
    replacement_ranking,
    journey_planner,
    TripData,
    VehicleData,
    DriverData,
    FrequencyBandData,
    CONFLICT_VEHICLE_OVERLAP,
    CONFLICT_DRIVER_OVERLAP,
    CONFLICT_LAYOVER_TOO_SHORT,
    CONFLICT_TERMINAL_MISMATCH,
    CONFLICT_VEHICLE_UNAVAILABLE,
    CONFLICT_DUTY_TOO_LONG,
    CONFLICT_BREAK_MISSING,
    CONFLICT_NOT_ACCESSIBLE,
)

def test_check_assignment_no_conflicts():
    trip = TripData("T1", "R1", 0, 36000, 39600, "STOP_A", "STOP_B")
    vehicle = VehicleData("V1", "BUS-101", status="active")
    driver = DriverData("D1", "Rajesh", is_active=True)

    conflicts = check_assignment(trip, vehicle, driver, [], [])
    assert len(conflicts) == 0

def test_check_assignment_vehicle_overlap():
    trip1 = TripData("T1", "R1", 0, 36000, 39600, "STOP_A", "STOP_B")
    overlap_trip = TripData("T2", "R1", 0, 38000, 41000, "STOP_A", "STOP_B")
    vehicle = VehicleData("V1", "BUS-101", status="active")

    conflicts = check_assignment(overlap_trip, vehicle=vehicle, existing_vehicle_trips=[trip1])
    assert any(c.code == CONFLICT_VEHICLE_OVERLAP for c in conflicts)

def test_check_assignment_layover_too_short():
    trip1 = TripData("T1", "R1", 0, 36000, 39600, "STOP_A", "STOP_B")
    # Gap is only 60 seconds, less than MIN_LAYOVER_S = 300
    tight_trip = TripData("T2", "R1", 1, 39660, 43200, "STOP_B", "STOP_A")
    vehicle = VehicleData("V1", "BUS-101", status="active")

    conflicts = check_assignment(tight_trip, vehicle=vehicle, existing_vehicle_trips=[trip1])
    assert any(c.code == CONFLICT_LAYOVER_TOO_SHORT for c in conflicts)

def test_check_assignment_terminal_mismatch():
    trip1 = TripData("T1", "R1", 0, 36000, 39600, "STOP_A", "STOP_B")
    # Starts at STOP_C instead of STOP_B
    mismatch_trip = TripData("T2", "R2", 0, 40500, 44000, "STOP_C", "STOP_D")
    vehicle = VehicleData("V1", "BUS-101", status="active")

    conflicts = check_assignment(mismatch_trip, vehicle=vehicle, existing_vehicle_trips=[trip1])
    assert any(c.code == CONFLICT_TERMINAL_MISMATCH for c in conflicts)

def test_check_assignment_vehicle_unavailable():
    trip = TripData("T1", "R1", 0, 36000, 39600, "STOP_A", "STOP_B")
    broken_vehicle = VehicleData("V1", "BUS-101", status="breakdown")

    conflicts = check_assignment(trip, vehicle=broken_vehicle)
    assert any(c.code == CONFLICT_VEHICLE_UNAVAILABLE for c in conflicts)

def test_check_assignment_not_accessible():
    trip = TripData("T1", "R1", 0, 36000, 39600, "STOP_A", "STOP_B", is_accessible_required=True)
    inaccessible_vehicle = VehicleData("V1", "BUS-101", is_accessible=False)

    conflicts = check_assignment(trip, vehicle=inaccessible_vehicle)
    assert any(c.code == CONFLICT_NOT_ACCESSIBLE for c in conflicts)

def test_check_assignment_driver_duty_too_long():
    # 9 hours total duration exceeds 8 hours (480 min)
    trip1 = TripData("T1", "R1", 0, 21600, 36000, "STOP_A", "STOP_B") # 4 hours
    trip2 = TripData("T2", "R1", 1, 38000, 56000, "STOP_B", "STOP_A") # 5 hours
    driver = DriverData("D1", "Ramesh", max_duty_minutes=480)

    conflicts = check_assignment(trip2, driver=driver, existing_driver_trips=[trip1])
    assert any(c.code == CONFLICT_DUTY_TOO_LONG for c in conflicts)

def test_trip_generator():
    bands = [
        FrequencyBandData(route_id="R1", direction=0, start_s=21600, end_s=25200, headway_min=15)
    ]
    trips = trip_generator(bands, route_duration_s=1800, start_stop_id="S1", end_stop_id="S2")
    # From 21600 to 25200 with 15 min (900 s) headway -> 4 trips (0, 15, 30, 45 min)
    assert len(trips) == 4
    assert trips[0].start_s == 21600
    assert trips[1].start_s == 22500

def test_vehicle_blocker_best_fit():
    trips = [
        TripData("T1", "R1", 0, 21600, 23400, "S1", "S2"),
        TripData("T2", "R1", 1, 24000, 25800, "S2", "S1"),
        TripData("T3", "R1", 0, 26400, 28200, "S1", "S2"),
    ]
    vehicles = [VehicleData("V1", "BUS-101"), VehicleData("V2", "BUS-102")]

    blocks, unassigned, stats = vehicle_blocker(trips, vehicles)
    # Consecutive matching trips should chain into 1 vehicle block
    assert len(blocks) == 1
    assert len(blocks[0].trips) == 3
    assert len(unassigned) == 0
    assert stats["vehicles_used"] == 1

def test_eta_calculator_live_and_scheduled():
    # Live vehicle 2500m away at 30 km/h: (2500 / (30000/3600)) = 300s = 5 minutes
    mins_live, label_live = eta_calculator(
        is_live=True,
        scheduled_stop_offset_s=600,
        trip_start_s=36000,
        current_time_s=36100,
        vehicle_speed_kmph=30.0,
        remaining_distance_m=2500.0,
    )
    assert mins_live == 5
    assert label_live == "live"

    # Scheduled bus: offset 900s from trip_start 36000 = 36900. Current time 36300 -> diff 600s = 10 min
    mins_sched, label_sched = eta_calculator(
        is_live=False,
        scheduled_stop_offset_s=900,
        trip_start_s=36000,
        current_time_s=36300,
    )
    assert mins_sched == 10
    assert label_sched == "scheduled"

def test_replacement_ranking():
    broken = VehicleData("V1", "BUS-BROKEN", current_lat=25.4358, current_lng=81.8463, is_accessible=True)
    c1 = VehicleData("V2", "BUS-FAR", current_lat=25.5000, current_lng=81.9000, is_accessible=True)
    c2 = VehicleData("V3", "BUS-NEAR", current_lat=25.4380, current_lng=81.8480, is_accessible=True)
    c3 = VehicleData("V4", "BUS-INACCESSIBLE", current_lat=25.4370, current_lng=81.8470, is_accessible=False)

    ranked = replacement_ranking(broken, [c1, c2, c3], 36000, [])
    # BUS-NEAR should be first; BUS-INACCESSIBLE should be excluded
    assert len(ranked) >= 2
    assert ranked[0][0].fleet_no == "BUS-NEAR"
    assert not any(r[0].fleet_no == "BUS-INACCESSIBLE" for r in ranked)

def test_journey_planner_direct_and_transfer():
    routes = [
        {"id": "R1", "short_name": "7A", "stops": ["S1", "S2", "S3", "S4"]},
        {"id": "R2", "short_name": "14", "stops": ["S3", "S5", "S6"]},
    ]
    # Direct from S1 to S4
    direct_plans = journey_planner(routes, "S1", "S4")
    assert len(direct_plans) > 0
    assert direct_plans[0].transfers == 0
    assert direct_plans[0].legs[0].route_short_name == "7A"

    # Transfer from S1 to S6 via S3
    transfer_plans = journey_planner(routes, "S1", "S6")
    assert len(transfer_plans) > 0
    assert transfer_plans[0].transfers == 1
    assert transfer_plans[0].legs[0].to_stop_id == "S3"
    assert transfer_plans[0].legs[2].to_stop_id == "S6"

def test_property_blocking_never_violates_check_assignment():
    """
    Property test: Vehicle blocker must NEVER produce an assignment that
    check_assignment would reject. (SPEC §9 & §12)
    """
    random.seed(42)
    terminals = ["DEPOT", "CIVIL_LINES", "RAILWAY_STATION", "CAMPUS"]
    trips: list[TripData] = []
    
    # Generate random sequence of trips
    cur_time = 21600
    for i in range(15):
        t_start = cur_time + random.randint(1, 10) * 60
        duration = random.randint(20, 45) * 60
        t_end = t_start + duration
        s_from = terminals[i % len(terminals)]
        s_to = terminals[(i + 1) % len(terminals)]
        trips.append(TripData(f"T-{i}", "R1", 0, t_start, t_end, s_from, s_to))
        cur_time = t_start + 600

    vehicles = [VehicleData(f"V-{v}", f"BUS-{v}") for v in range(5)]
    blocks, _, _ = vehicle_blocker(trips, vehicles)

    # Validate that every block's trips pass check_assignment
    for block in blocks:
        veh = next(v for v in vehicles if v.id == block.vehicle_id)
        for i, trip in enumerate(block.trips):
            other_trips = [t for t in block.trips if t.id != trip.id]
            conflicts = check_assignment(trip, vehicle=veh, existing_vehicle_trips=other_trips)
            assert len(conflicts) == 0, f"Blocking produced invalid assignment: {conflicts}"

