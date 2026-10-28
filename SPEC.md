# SPEC — Public Transport Fleet Scheduling & Passenger Information System

**Team:** T9 · **Working name:** Wayline · **Version:** 1.0
**Stack:** Python (FastAPI) backend · React (Vite + TypeScript) frontend

---

## 1. Purpose

A single system that does two jobs for a city bus network:

1. **Operations side:** plan schedules, assign vehicles and drivers without conflicts, and manage disruptions live.
2. **Passenger side:** tell people where their bus is, when it arrives, and what is disrupted.

Both sides share one data model and one live feed. If a dispatcher marks a bus as broken down, the passenger board changes within seconds.

### 1.1 Users

| Role | Auth | What they need |
|---|---|---|
| Passenger | None (public) | Next buses at my stop, where is my bus, is anything disrupted |
| Dispatcher | Login | Build schedules, assign buses and drivers, react to delays |
| Driver | Login | See today's duty, start/end trips, report problems |
| Admin | Login | Manage stops, routes, vehicles, drivers, users; see reports |

### 1.2 Out of scope (v1)

Ticketing and payments, real GPS hardware integration (we simulate it), multi-city tenancy, native mobile apps, ML-based prediction.

---

## 2. Tech Stack

### Backend
- Python 3.11+, **FastAPI**, Pydantic v2
- **SQLAlchemy 2.0** + **Alembic** migrations
- **PostgreSQL** (production/docker), SQLite allowed for quick local dev
- JWT auth (access + refresh), password hashing with argon2 or bcrypt
- **WebSockets** (FastAPI native) for live vehicle positions and alerts
- Background simulator as an asyncio task (no Celery/Redis needed in v1)
- **pytest**, httpx test client, ruff + mypy
- `uv` or `pip` + `requirements.txt` (pick one, document it)

### Frontend
- React 18, **Vite**, **TypeScript** (strict)
- React Router, **TanStack Query** (server state), Zustand (small UI state)
- **Tailwind CSS** with a custom token layer (see §9), no component library that imposes its look
- **Leaflet** + OpenStreetMap tiles for maps
- Radix primitives for accessible behaviour (dialogs, popovers, tabs), styled by us
- **Vitest** + React Testing Library; Playwright for 3 critical e2e flows
- Icons: lucide-react, used sparingly (see §9.6)

### Dev/Infra
- `docker-compose.yml` with `db`, `api`, `web`
- `.env.example` for both apps
- A `Makefile` (or `justfile`) with `dev`, `test`, `seed`, `lint`

---

## 3. Repository Layout

```
wayline/
├─ SPEC.md
├─ ANTIGRAVITY_PROMPT.md
├─ README.md
├─ docker-compose.yml
├─ Makefile
├─ backend/
│  ├─ pyproject.toml
│  ├─ alembic/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ core/            # config, security, deps, errors
│  │  ├─ db/              # session, base, seed
│  │  ├─ models/          # SQLAlchemy models
│  │  ├─ schemas/         # Pydantic models
│  │  ├─ api/v1/          # routers: auth, stops, routes, vehicles, drivers, trips,
│  │  │                   #   schedule, assignments, incidents, alerts, public, reports
│  │  ├─ services/        # business logic (scheduler, eta, incidents, reports)
│  │  ├─ realtime/        # ws manager, simulator
│  │  └─ tests/
├─ frontend/
│  ├─ package.json
│  ├─ index.html
│  ├─ src/
│  │  ├─ app/             # router, providers, layouts
│  │  ├─ design/          # tokens.css, typography, primitives
│  │  ├─ features/
│  │  │  ├─ passenger/    # home, stop board, route view, planner, alerts
│  │  │  ├─ dispatch/     # live map, schedule builder, gantt, incidents
│  │  │  ├─ driver/       # duty view
│  │  │  └─ admin/        # CRUD screens, reports
│  │  ├─ lib/             # api client, ws client, time utils
│  │  └─ tests/
└─ docs/
   ├─ api.md
   └─ scheduling-algorithm.md
```

Rule: routers stay thin. Business logic lives in `services/`. No logic in React components that belongs in a hook or util.

---

## 4. Domain Model

All times stored in UTC in the DB, displayed in `Asia/Kolkata` by default (configurable). Service times (timetables) are stored as "seconds after midnight, local service day" so late-night trips past 24:00 work.

### 4.1 Entities

**User** — id, name, email, password_hash, role (`admin|dispatcher|driver`), is_active, created_at

**Stop** — id, code (short, e.g. `S014`), name, lat, lng, is_accessible (bool), has_shelter (bool), landmark_note

**Route** — id, short_name (`7A`), long_name, color_hex, is_active, route_type (`city|express|feeder`)

**RouteStop** — route_id, direction (`0|1`), sequence, stop_id, dwell_seconds, distance_from_prev_m, scheduled_offset_s (from trip start)

**RoutePath** — route_id, direction, polyline (list of [lat,lng]) used for map drawing and simulator movement

**ServiceCalendar** — id, name (`Weekday`, `Saturday`, `Sunday/Holiday`), days_of_week bitmask, plus **CalendarException** (date, calendar_id or none, reason)

**FrequencyBand** — route_id, direction, calendar_id, start_s, end_s, headway_min. Source of truth for "how often".

**Vehicle** — id, fleet_no, plate, type (`midi|standard|articulated|electric`), capacity_seated, capacity_standing, is_accessible, status (`active|maintenance|breakdown|retired`), depot

**MaintenanceWindow** — vehicle_id, start_at, end_at, reason

**Driver** — id, user_id (nullable), name, license_no, phone, max_duty_minutes (default 480), is_active

**Trip** — id, route_id, direction, service_date, calendar_id, start_s, end_s, status (`scheduled|in_progress|completed|cancelled`), block_id (nullable)

**Block** — id, service_date, vehicle_id (nullable), name. A block is a chain of trips run by one vehicle in a day.

**Duty** — id, service_date, driver_id, start_s, end_s, break_start_s, break_end_s. A duty covers one or more blocks (or parts of blocks).

**DutyBlock** — duty_id, block_id, from_trip_id, to_trip_id

**VehiclePosition** — vehicle_id, trip_id, lat, lng, speed_kmph, heading, occupancy (`empty|seats|standing|full`), recorded_at. Keep latest in memory, persist every Nth tick for history.

**TripStopEvent** — trip_id, stop_id, scheduled_s, actual_s (nullable), delay_s. Basis for on-time reports.

**Incident** — id, type (`breakdown|accident|traffic|road_closure|driver_absent|other`), severity (`low|med|high`), vehicle_id?, trip_id?, route_id?, stop_id?, description, status (`open|acknowledged|resolved`), created_by, created_at, resolved_at

**Alert** — id, route_id?, stop_id?, title, body, severity (`info|warning|severe`), starts_at, ends_at, created_by. Public-facing.

### 4.2 Key constraints (enforced in service layer and DB where possible)

- A vehicle cannot be in two overlapping blocks on the same day.
- A driver cannot be in two overlapping duties.
- Consecutive trips in a block must have `layover >= MIN_LAYOVER_S` (default 300 s), and the next trip's start terminal must equal the previous trip's end terminal.
- Vehicle in `maintenance` or `breakdown` cannot be assigned during the affected window.
- Accessible-only trips (flag on route or trip) need `is_accessible` vehicles.
- Duty length ≤ `max_duty_minutes`; a break of ≥ 30 min is required within the first 4.5 hours of continuous driving.

---

## 5. Functional Requirements

Each requirement has an ID so we can trace it in tests and in the lab report.

### 5.1 Passenger (public, no login)

| ID | Requirement | Acceptance criteria |
|---|---|---|
| P-1 | Search stops and routes by name or code | Results appear as the user types, tolerate typos, first result within 300 ms on seed data |
| P-2 | **Stop board**: upcoming arrivals at a stop | Shows next 8 arrivals; each row has route chip, destination, minutes away, and a "live" or "scheduled" marker; refreshes automatically |
| P-3 | **Route view**: map of route with live buses and stop list | Buses move smoothly; tapping a stop opens its board; direction toggle |
| P-4 | **Trip planner** (A → B) | Finds direct routes first, then single-transfer options; shows total time, walk/wait/ride breakdown, next 3 departures |
| P-5 | **Service alerts** | Alerts show on affected routes and stops; a global banner for severe alerts |
| P-6 | **Saved places** | User pins stops/routes locally (no account); pinned items appear on Home with next arrival |
| P-7 | Timetable view | Full-day timetable per route/direction/day-type, with the current time highlighted |
| P-8 | Accessibility filter | Toggle to show only wheelchair-accessible stops/buses |
| P-9 | Crowding hint | Each live bus shows occupancy as a plain label (not a colored blob only) |
| P-10 | Works offline-ish | Last-fetched timetables and saved places load when the network drops, with a visible "offline" note |

### 5.2 Dispatcher

| ID | Requirement | Acceptance criteria |
|---|---|---|
| D-1 | **Live ops map** | All active vehicles on map with route color, delay badge, and status; filter by route/status; click vehicle for a side panel |
| D-2 | **Fleet board** | Table of every vehicle: status, current trip, driver, delay, next maintenance; sortable and filterable |
| D-3 | **Schedule generation** | Pick service date + calendar; system generates trips from FrequencyBands; preview before commit |
| D-4 | **Auto-assign vehicles (blocking)** | One click builds blocks and assigns vehicles; shows unassigned trips and why |
| D-5 | **Auto-assign drivers (duties)** | Builds legal duties around the blocks; shows rule violations |
| D-6 | **Manual override** | Drag a trip (or block) to another vehicle on the Gantt; instant conflict check with a clear reason when rejected |
| D-7 | **Gantt timeline** | Rows are vehicles (or drivers), bars are trips, colored by route; zoom to 1 h / 4 h / full day; now-line |
| D-8 | **Incident handling** | Create/acknowledge/resolve incidents; marking a vehicle `breakdown` suggests replacement vehicles and drivers and affected trips |
| D-9 | **One-click reassign** | Accept a suggested replacement; affected trips move, driver notified in the driver view |
| D-10 | **Broadcast alert** | Compose a public alert tied to route/stop with start/end time; appears in passenger app live |
| D-11 | **Audit trail** | Every assignment change is logged with who, when, before/after |

### 5.3 Driver

| ID | Requirement | Acceptance criteria |
|---|---|---|
| R-1 | Today's duty | Shows duty start/end, break, list of trips in order with vehicle and start time |
| R-2 | Start / end trip | Large buttons; start is only enabled near scheduled time and when previous trip is complete |
| R-3 | Report issue | Pick from presets (breakdown, traffic, accident, passenger issue), optional note; creates an Incident |
| R-4 | Delay status | Shows current delay vs schedule in plain words ("4 min late") |
| R-5 | Notices | Reassignments and dispatcher messages appear as a short feed |

### 5.4 Admin

| ID | Requirement | Acceptance criteria |
|---|---|---|
| A-1 | CRUD for stops, routes (with ordered stops per direction), vehicles, drivers, users, calendars, frequency bands | Form validation, inline errors, soft delete where history exists |
| A-2 | Route editor with map | Add stops by clicking the map or picking existing ones; reorder by drag; auto-draw polyline between stops (straight segments acceptable in v1) |
| A-3 | Reports | On-time performance by route/day/hour, vehicle utilisation, incident counts, driver hours; export CSV |
| A-4 | Role management | Admin can create dispatcher/driver accounts and deactivate users |

### 5.5 System

| ID | Requirement |
|---|---|
| S-1 | Live positions are pushed over WebSocket; clients fall back to polling every 10 s if the socket drops |
| S-2 | A simulator moves vehicles along route polylines at realistic speeds with random delays and occasional events, so the demo is alive without hardware |
| S-3 | Seed script creates a complete demo network (see §11) |
| S-4 | All list endpoints support pagination, sorting, and filtering |
| S-5 | Consistent error format (see §7.1) |
| S-6 | OpenAPI docs available at `/docs` |

---

## 6. Core Algorithms

Write these as pure, well-tested functions in `services/`. Document in `docs/scheduling-algorithm.md`.

### 6.1 Trip generation
For each route, direction, and calendar: for each `FrequencyBand`, emit trips at `start_s, start_s + headway, …` while `< end_s`. Trip duration = last `scheduled_offset_s` of the pattern. Output sorted by start time.

### 6.2 Vehicle blocking (interval chaining)
Goal: cover all trips with the fewest vehicles while respecting layover and terminal continuity.

1. Sort trips by start time.
2. Maintain a pool of open blocks keyed by (end terminal, end time).
3. For each trip, pick the open block whose last trip ends at the trip's start terminal, with `trip.start − block.end >= MIN_LAYOVER_S`, choosing the **smallest idle gap** (best fit).
4. If none fits and a vehicle is free (not in maintenance, accessible if needed), open a new block.
5. If no vehicle is available, mark the trip **unassigned** with a reason code (`NO_VEHICLE`, `NO_ACCESSIBLE_VEHICLE`, `MAINTENANCE_CONFLICT`).

Return `{blocks, unassigned, stats: {vehicles_used, avg_idle_min}}`.

### 6.3 Driver duty building
1. For each block, split into candidate duty segments of at most `max_duty_minutes`, cutting at a layover that is ≥ 30 min where possible to place the break.
2. Assign drivers greedily by least total hours so far that day, skipping drivers who are inactive or already overlapping.
3. Validate each duty: max length, break rule, no overlap. Emit warnings for soft rule breaks, errors for hard ones.

### 6.4 Conflict detection
A pure function `check_assignment(proposed, existing) -> list[Conflict]` returning typed conflicts (`VEHICLE_OVERLAP`, `DRIVER_OVERLAP`, `LAYOVER_TOO_SHORT`, `TERMINAL_MISMATCH`, `VEHICLE_UNAVAILABLE`, `DUTY_TOO_LONG`, `BREAK_MISSING`, `NOT_ACCESSIBLE`). Used by both auto-assign and manual drag-drop so they cannot disagree.

### 6.5 ETA
For a stop on a trip:
- If the vehicle is live: project remaining distance along the route path at the average speed of the last 3 minutes (clamped 8–40 km/h) plus remaining dwell times.
- Else: scheduled time plus the trip's current known delay.
- Label output `live` or `scheduled`.
- Never show negative minutes; show "due" under 1 min.

### 6.6 Breakdown replacement suggestion
When a vehicle goes to `breakdown`: find active vehicles with no overlapping block in the remaining window, matching or exceeding accessibility; rank by proximity to the failed vehicle's last position, then by capacity. Return the top 3 with the list of affected trips.

### 6.7 Journey planner (v1)
Build an in-memory graph at startup: nodes = stops, edges = consecutive stops on a route direction, with transfer nodes for stops within 250 m. Search direct first; then one transfer via BFS limited to depth 2. Score by (ride time + transfer wait + walk time). Cache the graph; rebuild when routes change.

---

## 7. API Design

Base path `/api/v1`. JSON. Auth via `Authorization: Bearer <token>`.

### 7.1 Conventions
- Pagination: `?page=1&page_size=25`, response `{items, total, page, page_size}`
- Errors: `{ "error": { "code": "VEHICLE_OVERLAP", "message": "Bus 112 is already on Block B4 from 09:10 to 10:40", "details": {...} } }`
- Timestamps ISO-8601 with timezone. Service times as `"HH:MM"` strings in responses plus raw seconds where needed.
- Every mutating endpoint is role-guarded and idempotent where reasonable.

### 7.2 Endpoints

**Auth**
- `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`

**Public (no auth)**
- `GET /public/search?q=`
- `GET /public/stops/{id}`
- `GET /public/stops/{id}/arrivals?limit=8`
- `GET /public/routes`, `GET /public/routes/{id}` (stops, path, directions)
- `GET /public/routes/{id}/timetable?date=&direction=`
- `GET /public/routes/{id}/vehicles` (live snapshot)
- `GET /public/plan?from=&to=&depart_at=&accessible=`
- `GET /public/alerts?route_id=&stop_id=`
- `GET /public/nearby-stops?lat=&lng=&radius=`

**Admin / Dispatcher resources** (standard CRUD, role-guarded)
- `/stops`, `/routes`, `/routes/{id}/stops`, `/routes/{id}/frequency`, `/calendars`, `/vehicles`, `/drivers`, `/users`

**Scheduling**
- `POST /schedule/generate` `{date, calendar_id, dry_run}` → trips preview or committed
- `POST /schedule/auto-assign-vehicles` `{date, dry_run}`
- `POST /schedule/auto-assign-drivers` `{date, dry_run}`
- `GET  /schedule/gantt?date=&group_by=vehicle|driver`
- `POST /assignments/check` `{trip_ids, vehicle_id?, driver_id?}` → conflicts
- `PUT  /assignments/trips/{trip_id}` `{vehicle_id, driver_id}`
- `GET  /assignments/audit?date=`

**Operations**
- `GET  /ops/fleet` (live board data)
- `POST /incidents`, `GET /incidents`, `PATCH /incidents/{id}`
- `GET  /incidents/{id}/replacement-suggestions`
- `POST /incidents/{id}/apply-replacement`
- `POST /alerts`, `PATCH /alerts/{id}`, `DELETE /alerts/{id}`

**Driver**
- `GET  /driver/duty/today`
- `POST /driver/trips/{id}/start`, `POST /driver/trips/{id}/end`
- `POST /driver/report-issue`

**Reports**
- `GET /reports/on-time?from=&to=&route_id=`
- `GET /reports/utilisation?date=`
- `GET /reports/incidents?from=&to=`
- `GET /reports/driver-hours?from=&to=`
- Each supports `&format=csv`

### 7.3 WebSockets
- `WS /ws/live` — public. Client sends `{subscribe: {routes:[…], stops:[…]}}`. Server sends:
  - `{type:"positions", data:[{vehicle_id, route_id, lat, lng, heading, occupancy, delay_s, ts}]}` every 2 s
  - `{type:"alert", data:{…}}` when alerts change
  - `{type:"arrivals", stop_id, data:[…]}` when a subscribed stop's board changes materially
- `WS /ws/ops` — authenticated (token in query or first message). Adds incidents, assignment changes, and vehicle status.

---

## 8. Frontend: Screens and Behaviour

### 8.1 Information architecture

```
/                       Passenger home
/stop/:id               Stop board
/route/:id              Route view (map + live)
/plan                   Trip planner
/alerts                 Service alerts
/timetable/:routeId     Timetable

/ops                    Dispatcher shell (auth)
  /ops/live             Live map + fleet board
  /ops/schedule         Generate, assign, Gantt
  /ops/incidents        Incident queue
  /ops/alerts           Broadcast composer
  /ops/reports          Reports

/driver                 Driver duty (auth, mobile-first)

/admin                  Admin shell (auth)
  /admin/network        Stops, routes, route editor
  /admin/fleet          Vehicles, maintenance
  /admin/people         Drivers, users
  /admin/calendars      Calendars, frequency bands
```

### 8.2 Passenger app (mobile-first, one-handed)

**Home**
- Top: a single search field, large, always reachable. Placeholder: "Stop, route, or place".
- Below: **Saved** (pinned stops with next two arrivals each, inline) and **Nearby** (if location is granted; else a quiet prompt, no modal).
- A slim alert strip only when a severe alert exists.
- No hero image, no marketing copy.

**Stop board**
- Header: stop name, code, accessibility and shelter icons with text labels.
- The board is a departure-board layout: rows of `[route chip] [destination] [minutes]`. Minutes are large and use tabular numerals. Live rows show a small pulsing dot; scheduled rows show a hollow dot. Tap a row to see that bus on the map.
- A pin button saves the stop.

**Route view**
- Map occupies the upper 55% on mobile, with a draggable bottom sheet listing stops in order with time-to-arrival per stop for the nearest approaching bus. On desktop, map right, list left.
- Buses are drawn as small rotated markers with the route number; tapping shows delay, occupancy label, next stop.

**Planner**
- Two fields (From, To) with swap button, "Leave now" with a time option.
- Result cards are compact timelines: walk — wait — ride (route chip) — transfer — ride. Show total minutes prominently.

**Alerts**
- A plain list grouped by severity, newest first, each with affected routes as chips.

### 8.3 Dispatcher console (desktop-first, dense)

- Left rail navigation (icons + labels, collapsible). Top bar with date picker, clock, connection status indicator (live / reconnecting).
- **Live**: split view. Map left (60%), fleet board right with tabs: Vehicles · Incidents. Selecting a row focuses the map and vice versa.
- **Schedule**: a stepper along the top: `Generate → Vehicles → Drivers → Review`. Each step shows a preview, stats (vehicles used, unassigned trips, rule warnings), and a Commit button. Below, the Gantt.
- **Gantt**: sticky left column, time axis with 15-min gridlines, now-line, bars show route short name and start time; conflicts render with a hatched pattern plus an icon. Drag to reassign with a live ghost bar and a validity tint (green outline = ok, red outline + reason = rejected).
- **Incidents**: a queue with severity, age, status. Selecting one opens a right drawer with affected trips and replacement suggestions as a ranked list with a primary "Apply" action.
- **Keyboard**: `/` focus search, `g l` live, `g s` schedule, `g i` incidents, `?` shortcut sheet, `Esc` close drawers.
- Tables: sticky header, resizable columns not required, row density toggle (comfortable / compact).

### 8.4 Driver view (phone, big touch targets)

- Single column. Top card: "Next trip" with route, start time, and vehicle. One primary button: **Start trip** / **End trip**. Below: remaining trips for the day and the break window.
- "Report issue" is a persistent secondary button leading to a 2-tap flow.
- Large text, high contrast, no map required.

### 8.5 Admin

- Standard list + detail forms, with the **route editor** as the signature screen: map canvas, ordered stop list with drag handles, per-stop dwell time, and a live summary (total length, estimated run time).

### 8.6 States every screen must handle
Loading (skeletons matching the real layout, not spinners), empty (a useful sentence and the next action), error (what happened and a retry), offline (visible, non-blocking), and permission denied.

---

## 9. Design System and Visual Direction

**Intent:** it should feel like well-made transit signage and printed timetables — functional, warm, a little industrial — not like a SaaS template. Think municipal wayfinding, not startup landing page.

### 9.1 Principles
1. **Information first.** The time, the route, the delay. Everything else is quiet.
2. **Signage logic.** Route chips behave like the colored bus-front boards. Big numerals, strong contrast, left-aligned text.
3. **One accent, used with intent.** Colour carries meaning (route identity, delay state), never decoration.
4. **Density where experts work, air where the public works.** Ops console is compact; passenger app is spacious and thumb-friendly.

### 9.2 Colour tokens

Define as CSS variables in `design/tokens.css`; Tailwind reads from them.

```
/* Light (passenger default) */
--paper:        #F5F2EA;   /* page background, warm off-white */
--surface:      #FBF9F4;   /* cards, sheets */
--ink:          #1C1B19;   /* primary text */
--ink-soft:     #5E5B54;   /* secondary text */
--rule:         #DDD8CB;   /* hairlines, borders */
--signal:       #E8A200;   /* primary accent: sign amber */
--signal-ink:   #2B2000;   /* text on amber */
--go:           #1E7A55;   /* on time, success */
--late:         #C4452B;   /* delay, error */
--caution:      #B8741A;   /* minor delay, warning */
--info:         #2F5F8A;   /* neutral info */

/* Dark (ops console default) */
--paper:        #131412;
--surface:      #1B1C19;
--ink:          #ECE9E1;
--ink-soft:     #A19D92;
--rule:         #2D2E29;
/* accents keep hue, adjust lightness for AA on dark */
```

Route colours are data (from `Route.color_hex`) and must be checked for contrast; auto-pick black or white text on the chip.

No purple-to-blue gradients. No glassmorphism. No neon glows. Maps use a muted/desaturated tile style so route colours pop (apply a CSS filter or use a quiet tile source).

### 9.3 Typography
- **Display / headings:** *Bricolage Grotesque* or *Familjen Grotesk* (self-host via `@fontsource`, not a CDN call)
- **Body / UI:** *Instrument Sans* or *Public Sans*
- **Numerals / times / codes:** *IBM Plex Mono* or *JetBrains Mono* with `font-variant-numeric: tabular-nums`
- Do **not** use Inter, Roboto, or system-ui as the visible brand face.
- Scale (px): 12 / 14 / 16 / 20 / 28 / 40 / 64 (the 64 is only for "minutes away" on the stop board).
- Line height 1.4 for body, 1.1 for large numerals. Sentence case everywhere, no ALL CAPS headings (small caps-style labels at 12px with letter-spacing are fine).

### 9.4 Layout, shape, spacing
- 4 px base grid; spacing steps 4, 8, 12, 16, 24, 32, 48.
- Corner radius: **4 px** for inputs/buttons/chips, **8 px** for sheets and drawers. Not pill-everything, not 24 px blobs.
- Separation by **hairline rules and whitespace**, not by stacking shadowed cards. Max one soft shadow level, used only for floating layers (drawers, popovers, bottom sheet).
- Don't build screens out of "icon in a circle + title + paragraph" tiles. Don't open with a row of four KPI cards. If a number matters, put it in context (a chart, a table row, a sentence).
- Left-aligned content. Avoid centred hero stacks.

### 9.5 Motion
- Purposeful only: vehicle markers glide between positions (CSS transition 1.8 s linear), minute counters tick with a short vertical slide, drawers slide 180 ms ease-out.
- Respect `prefers-reduced-motion` (turn off the glide and tick, keep state changes instant).
- No bouncing, no confetti, no skeleton shimmer longer than needed.

### 9.6 Iconography and imagery
- Icons: lucide at 16/20 px, 1.5 stroke, always paired with a text label for anything non-obvious. No emoji in the UI.
- No stock photos, no AI-style illustrations. If a graphic is needed, use simple geometric route-line motifs (straight segments with 45° bends, like a metro diagram) drawn in SVG.

### 9.7 Copy tone
Plain and specific. "Bus 7A is 4 min late near Civil Lines" not "Oops! Something might be delayed." Errors say what broke and what to do next. No exclamation marks, no "Welcome back!", no "Seamless".

### 9.8 Accessibility
- WCAG 2.2 AA contrast, visible focus rings (2 px, `--signal`), full keyboard operation of the ops console, ARIA live region for stop board updates (polite), never colour alone for status (always paired with text or icon), minimum 44 px touch targets on passenger and driver views, `lang` attribute set, semantic landmarks.

### 9.9 Component inventory (build these once, reuse)
`RouteChip`, `DepartureRow`, `StopBoard`, `LiveDot`, `DelayBadge`, `OccupancyLabel`, `VehicleMarker`, `BottomSheet`, `Drawer`, `DataTable`, `GanttTimeline`, `ConflictTag`, `Stepper`, `FormField`, `SegmentedControl`, `EmptyState`, `InlineError`, `ConnectionStatus`, `CommandSearch`.

---

## 10. Non-Functional Requirements

| Area | Target |
|---|---|
| Performance | Stop arrivals API p95 < 200 ms on seed data; passenger home first paint < 1.5 s on a mid-range phone over 4G; Gantt stays smooth with 60 vehicles × 12 h |
| Realtime | Position updates visible within 3 s of generation |
| Security | Hashed passwords, JWT expiry (15 min access, 7 day refresh), role checks on every ops/admin/driver endpoint, rate limiting on login and public search, CORS locked to configured origins, input validation on all payloads |
| Reliability | Graceful WS reconnect with exponential backoff; API returns stale-but-labelled data rather than failing hard |
| Testability | Core algorithms ≥ 90% line coverage; every conflict type has a unit test |
| Observability | Structured JSON logs, request IDs, `/health` and `/ready` endpoints |
| Maintainability | Type hints everywhere (mypy clean), TS strict, ruff/eslint/prettier clean, no dead code |
| Portability | `docker compose up` brings up everything with seeded data |

---

## 11. Seed Data (demo network)

Create a believable mid-size network so every screen has something to show. Use a Prayagraj-flavoured city with approximate coordinates (demo accuracy is fine; this is not a navigation product).

- **28 stops**, e.g. Civil Lines, Subedarganj, Naini, Jhunsi, Katra, Sangam, Allahpur, Lukerganj, IIIT Allahabad, Railway Station, Bus Stand, Medical College, High Court, and others. 70% accessible, 50% with shelters.
- **6 routes**: two trunk routes (frequent), two cross-town, one express, one feeder. Each has both directions, 10–16 stops, a polyline, a colour.
- **Calendars:** Weekday, Saturday, Sunday/Holiday, with frequency bands (peak 8–10 min, midday 15 min, evening 12 min, late 25 min).
- **16 vehicles** (mix of types, 4 accessible electric), 1 in maintenance, 1 retired.
- **20 drivers**, plus users: `admin@wayline.local`, `dispatcher@wayline.local`, `driver1@wayline.local` (documented in README with demo passwords).
- A generated schedule for **today and tomorrow** with blocks and duties already assigned, leaving 2–3 deliberate unassigned trips so the dispatcher flow has something to fix.
- 2 active alerts and 1 open incident.
- 30 days of historical `TripStopEvent` rows for the reports.

The simulator starts with the API and drives all in-progress trips of today.

---

## 12. Testing Strategy

**Backend**
- Unit: trip generation, blocking, duty building, conflict detection (one test per conflict type), ETA, replacement ranking, journey planner.
- API: auth and role guards, pagination, error format, public endpoints without auth.
- Integration: schedule generate → auto-assign → commit → gantt returns consistent data.

**Frontend**
- Component tests for `DepartureRow`, `RouteChip` (contrast logic), `GanttTimeline` conflict rendering.
- Hook tests for the WS client (reconnect, fallback to polling).
- **Playwright e2e (3 flows):**
  1. Passenger: search stop → view board → open route map → pin stop → reload and see it on Home.
  2. Dispatcher: generate schedule → auto-assign → drag a trip into a conflict → see rejection reason → fix.
  3. Dispatcher + Passenger: mark vehicle as breakdown → apply replacement → passenger board updates.

---

## 13. Milestones

| M | Scope | Done when |
|---|---|---|
| M0 | Scaffolding, docker, CI lint/test, design tokens, base components | `docker compose up` shows an empty styled shell and a green health check |
| M1 | Data model, migrations, seed, admin CRUD, auth | Admin can log in and manage the network |
| M2 | Public API + passenger app (home, stop board, route view, search, timetable, alerts) with simulator and WS | A passenger can watch a bus approach a stop live |
| M3 | Scheduling engine + dispatcher schedule screen + Gantt + conflict checks | Generate → assign → drag-and-drop with correct rejections |
| M4 | Incidents, replacement flow, broadcast alerts, driver view | Breakdown flows end-to-end into the passenger app |
| M5 | Planner, reports, saved places/offline, polish, accessibility pass, e2e tests | Full acceptance table in §14 passes |

---

## 14. Definition of Done (acceptance checklist)

- [ ] Every requirement ID in §5 is implemented or explicitly listed as deferred in `README.md`.
- [ ] `docker compose up` works from a clean clone, seeds data, and both apps load.
- [ ] Backend tests pass; coverage ≥ 90% on `services/` scheduling code. `ruff` and `mypy` clean.
- [ ] Frontend `tsc --noEmit`, lint, and unit tests pass. 3 Playwright flows pass.
- [ ] Verified visually at **390 px**, **768 px**, and **1440 px**, in light and dark where applicable. Screenshots saved to `docs/screenshots/`.
- [ ] No screen shows an unstyled loading flash, an unhandled error, or a blank empty state.
- [ ] Lighthouse accessibility ≥ 95 on passenger home and stop board.
- [ ] Design review against §9: no purple gradients, no icon-in-circle tile grids, no emoji, no Inter/Roboto, no KPI-card-row dashboards, copy follows §9.7.
- [ ] `docs/api.md` and `docs/scheduling-algorithm.md` written and accurate.
- [ ] README includes setup, demo credentials, architecture sketch, and known limitations.

---

## 15. Open Decisions (resolve in M0, record in README)

1. SQLite vs Postgres as the default for local dev (spec prefers Postgres via docker).
2. Tile source for Leaflet (OSM default; note usage policy and use a muted filter).
3. Whether drivers use a separate login page or the shared one (default: shared, role-based redirect).
