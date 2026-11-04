# Wayline System Entity-Relationship (ER) Diagram

This document models the complete relational domain schema for **Wayline** (Public Transport Fleet Scheduling & Passenger Information System), based on `SPEC.md §4` and implemented via SQLAlchemy 2.0.

---

## 1. High-Level Entity Relationship Diagram

```mermaid
erDiagram
    USER ||--o| DRIVER : "assigned as"
    ROUTE ||--|{ ROUTE_STOP : "contains ordered"
    STOP ||--|{ ROUTE_STOP : "referenced by"
    ROUTE ||--|{ ROUTE_PATH : "mapped by"
    ROUTE ||--|{ FREQUENCY_BAND : "governed by"
    SERVICE_CALENDAR ||--|{ FREQUENCY_BAND : "defines active window for"
    SERVICE_CALENDAR ||--|{ TRIP : "schedules"
    ROUTE ||--|{ TRIP : "generates"
    BLOCK ||--|{ TRIP : "chains"
    VEHICLE ||--o{ BLOCK : "assigned to"
    VEHICLE ||--o{ VEHICLE_POSITION : "transmits"
    TRIP ||--o{ VEHICLE_POSITION : "associated with"
    TRIP ||--|{ TRIP_STOP_EVENT : "tracks schedule for"
    STOP ||--|{ TRIP_STOP_EVENT : "checkpoint at"
    DRIVER ||--|{ DUTY : "works"
    DUTY ||--|{ DUTY_BLOCK : "covers"
    BLOCK ||--|{ DUTY_BLOCK : "apportioned to"
    VEHICLE ||--o{ INCIDENT : "involved in"
    TRIP ||--o{ INCIDENT : "affected by"
    ROUTE ||--o{ INCIDENT : "disrupted on"
    ROUTE ||--o{ ALERT : "broadcasts on"
    STOP ||--o{ ALERT : "displayed at"

    USER {
        string id PK
        string name
        string email UK
        string password_hash
        string role "admin | dispatcher | driver | passenger"
        boolean is_active
        datetime created_at
    }

    DRIVER {
        string id PK
        string user_id FK
        string name
        string license_no UK
        string phone
        int max_duty_minutes
        boolean is_active
    }

    STOP {
        string id PK
        string code UK "e.g. S014"
        string name
        float lat
        float lng
        boolean is_accessible
        boolean has_shelter
        string landmark_note
    }

    ROUTE {
        string id PK
        string short_name UK "e.g. 7A"
        string long_name
        string color_hex
        boolean is_active
        string route_type "city | express | feeder"
    }

    ROUTE_STOP {
        string id PK
        string route_id FK
        int direction "0 | 1"
        int sequence
        string stop_id FK
        int dwell_seconds
        float distance_from_prev_m
        int scheduled_offset_s
    }

    ROUTE_PATH {
        string id PK
        string route_id FK
        int direction
        json polyline "[[lat, lng], ...]"
    }

    SERVICE_CALENDAR {
        string id PK
        string name "Weekday | Saturday | Sunday/Holiday"
        int days_of_week "Bitmask"
    }

    FREQUENCY_BAND {
        string id PK
        string route_id FK
        int direction
        string calendar_id FK
        int start_s "Seconds after midnight"
        int end_s
        int headway_min
    }

    VEHICLE {
        string id PK
        string fleet_no UK "e.g. BUS-101"
        string plate
        string type "midi | standard | articulated | electric"
        int capacity_seated
        int capacity_standing
        boolean is_accessible
        string status "active | maintenance | breakdown | retired"
        string depot
    }

    BLOCK {
        string id PK
        string service_date "YYYY-MM-DD"
        string vehicle_id FK
        string name "e.g. BLK-1"
    }

    TRIP {
        string id PK
        string route_id FK
        int direction
        string service_date "YYYY-MM-DD"
        string calendar_id FK
        int start_s
        int end_s
        string status "scheduled | in_progress | completed | cancelled"
        string block_id FK
    }

    DUTY {
        string id PK
        string service_date "YYYY-MM-DD"
        string driver_id FK
        int start_s
        int end_s
        int break_start_s
        int break_end_s
    }

    DUTY_BLOCK {
        string id PK
        string duty_id FK
        string block_id FK
        string from_trip_id FK
        string to_trip_id FK
    }

    VEHICLE_POSITION {
        string id PK
        string vehicle_id FK
        string trip_id FK
        float lat
        float lng
        float speed_kmph
        float heading
        string occupancy "empty | seats | standing | full"
        int delay_s
        datetime recorded_at
    }

    TRIP_STOP_EVENT {
        string id PK
        string trip_id FK
        string stop_id FK
        int scheduled_s
        int actual_s
        int delay_s
    }

    INCIDENT {
        string id PK
        string type "breakdown | accident | traffic | road_closure | other"
        string severity "low | med | high"
        string vehicle_id FK
        string trip_id FK
        string route_id FK
        string stop_id FK
        text description
        string status "open | acknowledged | resolved"
        string created_by
        datetime created_at
        datetime resolved_at
    }

    ALERT {
        string id PK
        string route_id FK
        string stop_id FK
        string title
        text body
        string severity "info | warning | severe"
        datetime starts_at
        datetime ends_at
        string created_by
    }
```

---

## 2. Key Domain Groups

### A. Network Topology
- **`Stop`**: Physical pickup/dropoff points with GPS coordinates, shelter availability, and accessibility features.
- **`Route`**: Transit line definitions with branding color hex and mode classifications.
- **`RouteStop`**: Ordered junction table determining travel sequences, dwell periods, and timetable offsets per direction.
- **`RoutePath`**: Serialized polyline path for map rendering and simulator interpolation.

### B. Timetable & Scheduling
- **`ServiceCalendar`**: Service schedules per day category (Weekdays, Saturdays, Holidays).
- **`FrequencyBand`**: Base headway rules defining trip emission rates throughout operational time bands.
- **`Trip`**: Concrete scheduled runs between start and end terminals.
- **`Block`**: Consecutive chains of trips covered by a single assigned vehicle.
- **`Duty` & `DutyBlock`**: Legal shift packaging assigned to individual drivers conforming to max duty hours and mandatory break rules.

### C. Fleet & Real-Time Telemetry
- **`Vehicle`**: Bus inventory, capacities, depot allocations, and maintenance/breakdown states.
- **`Driver`**: Licensed transit operators with duty constraints.
- **`VehiclePosition`**: Real-time telemetry point updates (speed, coordinates, heading, delay, occupancy).
- **`TripStopEvent`**: Historical and live arrival tracking powering on-time performance analytics.

### D. Operations & Passenger Information
- **`Incident`**: Breakdowns, accidents, or disruptions with automated replacement candidate ranking.
- **`Alert`**: Public-facing advisories visible directly on stop boards and route banners.
