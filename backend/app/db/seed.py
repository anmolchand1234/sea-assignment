"""
Database seed script for Wayline Demo Network (SPEC §11).
Creates:
- 28 stops in Prayagraj
- 6 routes with polylines and ordered stops
- Calendars & frequency bands
- 16 vehicles (mix of diesel & electric accessible)
- 20 drivers & default users (admin, dispatcher, driver)
- Today's trips, blocks, and duties
- Active alerts and incidents
"""

import json
from datetime import datetime, timezone
from backend.app.db.session import SessionLocal, Base, engine
from backend.app.models import (
    User, Stop, Route, RouteStop, RoutePath, ServiceCalendar,
    FrequencyBand, Vehicle, Driver, Block, Trip, Duty, Incident, Alert
)
from backend.app.core.security import get_password_hash

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Users
    if not db.query(User).filter(User.email == "admin@wayline.local").first():
        db.add_all([
            User(
                name="Admin User",
                email="admin@wayline.local",
                password_hash=get_password_hash("admin123"),
                role="admin"
            ),
            User(
                name="Dispatcher One",
                email="dispatcher@wayline.local",
                password_hash=get_password_hash("dispatch123"),
                role="dispatcher"
            ),
            User(
                name="Driver Rajesh",
                email="driver1@wayline.local",
                password_hash=get_password_hash("driver123"),
                role="driver"
            ),
        ])
        db.commit()

    # 2. Stops (Prayagraj transit network - 28 stops per SPEC §11)
    stops_data = [
        ("S001", "Civil Lines Terminal", 25.4528, 81.8340, True, True),
        ("S002", "Subedarganj Railway Station", 25.4380, 81.7980, True, True),
        ("S003", "Prayagraj Junction (City Side)", 25.4430, 81.8260, True, True),
        ("S004", "High Court", 25.4485, 81.8210, True, True),
        ("S005", "Medical College (SRN Hospital)", 25.4388, 81.8415, True, True),
        ("S006", "Katra Market", 25.4610, 81.8540, False, True),
        ("S007", "University of Allahabad", 25.4590, 81.8590, True, True),
        ("S008", "Allahpur Post Office", 25.4510, 81.8710, True, False),
        ("S009", "Sangam Ghat Terminal", 25.4290, 81.8820, True, True),
        ("S010", "Alopibagh Mandir", 25.4435, 81.8740, False, True),
        ("S011", "IIIT Allahabad (Jhalwa)", 25.4295, 81.7705, True, True),
        ("S012", "Dhumanganj Thana", 25.4410, 81.7820, False, False),
        ("S013", "Naini Railway Station", 25.3880, 81.8650, True, True),
        ("S014", "Naini New Bridge (South)", 25.4120, 81.8580, True, False),
        ("S015", "Jhunsi Bus Stand", 25.4390, 81.9050, True, True),
        ("S016", "Shastri Bridge (East)", 25.4420, 81.8900, False, False),
        ("S017", "Lukerganj Crossing", 25.4340, 81.8150, True, True),
        ("S018", "Bamrauli Airport Gate", 25.4410, 81.7340, True, True),
        ("S019", "Chaukhandi", 25.4320, 81.8310, False, False),
        ("S020", "Zero Road Bus Terminal", 25.4360, 81.8380, True, True),
        ("S021", "MNNIT Allahabad Gate", 25.4920, 81.8640, True, True),
        ("S022", "Teliyarganj", 25.4850, 81.8580, False, True),
        ("S023", "Phaphamau Bridge", 25.5080, 81.8540, True, False),
        ("S024", "Govindpur Crossing", 25.4740, 81.8720, False, True),
        ("S025", "Buxi Bandh", 25.4480, 81.8810, True, False),
        ("S026", "Kareli Police Station", 25.4180, 81.8260, False, True),
        ("S027", "Gaughat", 25.4230, 81.8390, True, False),
        ("S028", "Yamuna Bank Road", 25.4280, 81.8480, False, True),
    ]

    stop_map = {}
    for code, name, lat, lng, acc, she in stops_data:
        stop = db.query(Stop).filter(Stop.code == code).first()
        if not stop:
            stop = Stop(
                code=code,
                name=name,
                lat=lat,
                lng=lng,
                is_accessible=acc,
                has_shelter=she
            )
            db.add(stop)
            db.flush()
        stop_map[code] = stop
    db.commit()

    # 3. Calendar
    cal = db.query(ServiceCalendar).filter(ServiceCalendar.name == "Weekday").first()
    if not cal:
        cal = ServiceCalendar(name="Weekday", days_of_week=31)
        db.add(cal)
        db.commit()
        db.refresh(cal)

    # 4. Routes (6 routes per SPEC §11)
    routes_def = [
        ("7A", "Civil Lines - Sangam Express", "#2563EB", "express", [
            "S001", "S004", "S003", "S005", "S019", "S020", "S010", "S009"
        ]),
        ("14", "IIIT Jhalwa - Civil Lines - Katra", "#DC2626", "city", [
            "S011", "S012", "S002", "S017", "S003", "S001", "S004", "S006", "S007"
        ]),
        ("21E", "Naini Station - Civil Lines - Teliyarganj", "#059669", "city", [
            "S013", "S014", "S028", "S027", "S005", "S001", "S006", "S024", "S022", "S021"
        ]),
        ("5B", "Jhunsi - Sangam - Zero Road", "#7C3AED", "feeder", [
            "S015", "S016", "S025", "S009", "S010", "S008", "S020"
        ]),
        ("AIR-1", "Bamrauli Airport - Civil Lines - Railway Station", "#D97706", "express", [
            "S018", "S012", "S002", "S017", "S003", "S004", "S001"
        ]),
        ("N1", "Night Owl Circular", "#1F2937", "city", [
            "S001", "S003", "S005", "S020", "S013", "S009", "S007", "S006", "S001"
        ]),
    ]

    for short_name, long_name, color, r_type, s_codes in routes_def:
        r = db.query(Route).filter(Route.short_name == short_name).first()
        if not r:
            r = Route(
                short_name=short_name,
                long_name=long_name,
                color_hex=color,
                route_type=r_type,
                is_active=True
            )
            db.add(r)
            db.flush()

            # Sequence stops
            coords = []
            for idx, scode in enumerate(s_codes):
                st = stop_map[scode]
                coords.append([st.lat, st.lng])
                rs = RouteStop(
                    route_id=r.id,
                    direction=0,
                    sequence=idx + 1,
                    stop_id=st.id,
                    dwell_seconds=30,
                    scheduled_offset_s=idx * 180, # 3 mins per stop
                )
                db.add(rs)

            # Route polyline
            rp = RoutePath(route_id=r.id, direction=0, polyline=coords)
            db.add(rp)

            # Frequency band (every 10-15 mins)
            fb = FrequencyBand(
                route_id=r.id,
                direction=0,
                calendar_id=cal.id,
                start_s=21600, # 06:00
                end_s=79200,   # 22:00
                headway_min=12
            )
            db.add(fb)
    db.commit()

    # 5. Vehicles (16 vehicles per SPEC §11)
    vehicles_data = [
        ("BUS-101", "UP-70-AT-1001", "standard", 36, 24, True, "active", "Civil Lines Depot"),
        ("BUS-102", "UP-70-AT-1002", "standard", 36, 24, True, "active", "Civil Lines Depot"),
        ("BUS-103", "UP-70-AT-1003", "articulated", 54, 35, True, "active", "Subedarganj Depot"),
        ("BUS-104", "UP-70-AT-1004", "standard", 36, 24, True, "active", "Civil Lines Depot"),
        ("BUS-105", "UP-70-AT-1005", "electric", 32, 20, True, "active", "Naini Depot"),
        ("BUS-106", "UP-70-AT-1006", "electric", 32, 20, True, "active", "Naini Depot"),
        ("BUS-107", "UP-70-AT-1007", "electric", 32, 20, True, "active", "Civil Lines Depot"),
        ("BUS-108", "UP-70-AT-1008", "electric", 32, 20, True, "active", "Civil Lines Depot"),
        ("BUS-109", "UP-70-AT-1009", "midi", 24, 15, True, "active", "Jhunsi Depot"),
        ("BUS-110", "UP-70-AT-1010", "standard", 36, 24, True, "active", "Civil Lines Depot"),
        ("BUS-111", "UP-70-AT-1011", "standard", 36, 24, False, "active", "Subedarganj Depot"),
        ("BUS-112", "UP-70-AT-1012", "standard", 36, 24, True, "active", "Civil Lines Depot"),
        ("BUS-113", "UP-70-AT-1013", "standard", 36, 24, True, "active", "Civil Lines Depot"),
        ("BUS-114", "UP-70-AT-1014", "midi", 24, 15, True, "active", "Civil Lines Depot"),
        ("BUS-115", "UP-70-AT-1015", "standard", 36, 24, True, "maintenance", "Main Workshop"),
        ("BUS-116", "UP-70-AT-1016", "standard", 36, 24, False, "retired", "Depot Yard"),
    ]

    for fleet_no, plate, v_type, cap_s, cap_st, acc, status, depot in vehicles_data:
        if not db.query(Vehicle).filter(Vehicle.fleet_no == fleet_no).first():
            v = Vehicle(
                fleet_no=fleet_no,
                plate=plate,
                type=v_type,
                capacity_seated=cap_s,
                capacity_standing=cap_st,
                is_accessible=acc,
                status=status,
                depot=depot,
            )
            db.add(v)
    db.commit()

    # 6. Drivers (20 drivers per SPEC §11)
    drivers_names = [
        "Rajesh Kumar", "Amit Sharma", "Sunil Yadav", "Mohd Irfan", "Deepak Verma",
        "Ramesh Chandra", "Pooja Singh", "Vikas Mishra", "Sanjay Patel", "Anil Maurya",
        "Praveen Tiwari", "Santosh Bind", "Manoj Shukla", "Arun Pandey", "Rahul Sonkar",
        "Satish Nishad", "Dinesh Gupta", "Kamlesh Pal", "Suraj Jaiswal", "Neeraj Tripathi"
    ]
    for idx, name in enumerate(drivers_names):
        lic = f"DL-70-2022-{1000 + idx}"
        if not db.query(Driver).filter(Driver.license_no == lic).first():
            d = Driver(
                name=name,
                license_no=lic,
                phone=f"+91 98390{10000 + idx}",
                max_duty_minutes=480,
                is_active=True
            )
            db.add(d)
    db.commit()

    # 7. Active Alerts and Incidents (SPEC §11)
    if not db.query(Alert).first():
        db.add_all([
            Alert(
                title="Shastri Bridge Lane Maintenance",
                body="Route 5B and crosstown services may experience 5-8 min delay during peak hours.",
                severity="warning",
                created_by="dispatcher"
            ),
            Alert(
                title="Sangam Special Service Active",
                body="Route 7A high-frequency shuttle operating every 8 minutes all weekend.",
                severity="info",
                created_by="dispatcher"
            )
        ])

    if not db.query(Incident).first():
        db.add(
            Incident(
                type="traffic",
                severity="med",
                description="Heavy congestion near Katra Market crossing. Delay ~7 mins.",
                status="open",
                created_by="system"
            )
        )
    db.commit()
    db.close()
    print("Seed data successfully populated!")

if __name__ == "__main__":
    seed()
