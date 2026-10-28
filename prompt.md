# ANTIGRAVITY PROMPT — Build "Wayline" (Public Transport Fleet Scheduling & Passenger Information System)

> Paste this whole file as the first message to the agent in **Planning mode**. Keep `SPEC.md` in the workspace root. The spec is the source of truth for scope; this prompt tells you *how to work*.

---

## 1. Your role

You are a senior full-stack engineer and product designer building a complete, working system from `SPEC.md`:

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, WebSockets
- **Frontend:** React 18 + Vite + TypeScript (strict), Tailwind with a custom token layer, TanStack Query, Leaflet

You own the result end to end: architecture, code, tests, seed data, UI, and verification. Do not hand back half-built scaffolding. Do not stub features and call them done.

## 2. Read first, then plan

1. Read `SPEC.md` fully before touching anything.
2. Produce an **Implementation Plan** artifact covering: milestone order (M0 → M5 from the spec), the data model, the module boundaries, and any open decisions from spec §15 with your chosen answer and one-line reason.
3. Produce a **Task List** artifact, grouped by milestone, with every requirement ID (P-, D-, R-, A-, S-) mapped to a task.
4. Stop and show me the plan. **Wait for my approval before writing code.** If I haven't replied, proceed with M0 only.

## 3. Working agreement

- Work **milestone by milestone** (M0 → M5). Do not start the next milestone until the current one's "done when" condition in spec §13 is verified.
- After each milestone, post a short **Walkthrough** artifact: what was built, how you verified it, screenshots of the UI, and anything deferred.
- Commit-sized steps. Keep a running `CHANGELOG.md` with one line per milestone.
- Prefer boring, readable code. No clever abstractions without a reason. No dead code, no commented-out blocks, no `TODO` left without a matching entry in the README's known limitations.
- If the spec is ambiguous, choose the simplest reasonable interpretation, write the decision in `README.md` under "Decisions", and continue. Only stop to ask me if the ambiguity would change the data model.
- If a requirement can't be done in v1, say so explicitly in the task list. Never silently drop it.

## 4. Backend instructions

**Structure.** Follow the layout in spec §3. Routers are thin; logic lives in `services/`; Pydantic schemas are separate from ORM models.

**Build order inside the backend**
1. Config, DB session, base model, error handling with the standard error envelope (spec §7.1).
2. Models + Alembic migration for every entity in spec §4.
3. Auth (login, refresh, `me`), role guard dependency (`require_role("dispatcher")` etc.).

4. CRUD routers with pagination, sorting, filtering.
5. **Scheduling services as pure functions first** (spec §6): trip generation, vehicle blocking, duty building, `check_assignment`, ETA, replacement ranking, journey planner. Write unit tests *before or alongside* each. These are the heart of the project; treat them with the most care.
6. Public routers, then ops routers, then driver routers, then reports.
7. WebSocket manager and the **simulator** that moves vehicles along route polylines, introduces delays, and occasionally emits events.
8. Seed script that produces the full demo network in spec §11. It must be idempotent (`make seed` can be run twice safely).

**Rules**
- The same `check_assignment` function must power both auto-assign and manual override.
- All times are UTC in the DB; service times are seconds-after-midnight. Write helpers and test the midnight-crossing case.
- Every conflict returns a typed code and a human sentence (spec §7.1 example).
- Add request IDs and structured logs. Add `/health` and `/ready`.
- Rate-limit login and public search.
- Run `ruff` and `mypy`; fix, don't suppress.

## 5. Frontend instructions

**Structure.** Follow spec §3 and §8. Feature folders, shared `design/` layer, a typed API client generated or hand-written from the OpenAPI schema, a single WebSocket client with reconnect and polling fallback.

**Build order inside the frontend**
1. `design/tokens.css` from spec §9.2, Tailwind config reading those variables, self-hosted fonts via `@fontsource` (spec §9.3).
2. Core primitives from spec §9.9: `RouteChip`, `DepartureRow`, `LiveDot`, `DelayBadge`, `BottomSheet`, `Drawer`, `DataTable`, `EmptyState`, `InlineError`, `ConnectionStatus`. Build a throwaway `/design` route that renders all of them in light and dark, so you can review the look early.
3. Passenger app (spec §8.2).
4. Dispatcher console (spec §8.3), including the **Gantt with drag-and-drop and live conflict validation**.
5. Driver view (spec §8.4), then admin including the route editor (spec §8.5).

**Rules**
- TypeScript strict, no `any` without a comment explaining why.
- Server state in TanStack Query; UI-only state in Zustand or local state. No data fetching inside presentational components.
- Every screen implements all five states: loading (layout-matched skeleton), empty, error with retry, offline, forbidden.
- Keyboard support and focus management for the ops console (spec §8.3 shortcuts).
- Accessibility per spec §9.8, including an ARIA live region on the stop board.

## 6. Design brief (this is where most agents fail — read carefully)

The UI must look **designed by a person who rides buses**, not generated. Reference feeling: municipal transit signage, printed timetables, departure boards. Warm paper tones, amber signal accent, strong numerals, hairline rules.

**Do**
- Use the exact tokens, fonts, radii, and spacing from spec §9.
- Make the minutes-away number the loudest thing on the stop board.
- Use route chips as the main visual identity element.
- Separate content with hairlines and whitespace.
- Write copy that is plain and specific (spec §9.7).
- Use geometric metro-style line motifs in SVG if you need any decoration.

**Do not**
- No purple/blue gradients, no glassmorphism, no glow effects, no gradient text.
- No grid of identical rounded cards with an icon in a coloured circle, a bold title, and a grey paragraph.
- No opening row of four KPI stat cards on dashboards.
- No emoji in the interface. No stock or AI-generated imagery.
- No Inter, Roboto, Arial, or default system font as the visible brand face.
- No centred hero sections, no "Welcome back!", no exclamation marks, no filler microcopy.
- No pill-shaped everything, and no heavy shadows.
- Don't leave the default Leaflet blue marker or raw OSM tiles; mute the map and style the vehicle markers.

If you catch your own output drifting toward any item in the "Do not" list, fix it before moving on.

## 7. Verification (mandatory, use the browser agent)

You must **see** the UI, not assume it. For every milestone that has UI:

1. Start the stack (`docker compose up` or the dev servers).
2. Use the **browser agent** to open the app and take screenshots at **390 px, 768 px, and 1440 px**, in light and dark where applicable.
3. Check against the design brief and fix issues. Attach the screenshots to the milestone Walkthrough.
4. Record a short browser recording for these flows and attach them as artifacts:
   - Passenger: search stop → stop board → route map with a moving bus → pin stop
   - Dispatcher: generate → auto-assign → drag a trip into a conflict → rejection reason → fix
   - Breakdown: mark vehicle down → apply replacement → passenger board updates
5. Run the full test suites. Paste the summary (pass/fail counts, coverage on `services/`) into the Walkthrough.

A milestone is **not done** if you only wrote code and didn't run it.

## 8. Terminal and environment

- Use a virtual environment for Python and a lockfile for Node.
- Provide `Makefile` targets: `dev`, `test`, `seed`, `lint`, `e2e`.
- Provide `docker-compose.yml` with `db`, `api`, `web`, and a healthcheck on `db`.
- Don't use destructive commands (dropping volumes, `rm -rf` outside the project, force pushes) without asking me.
- Don't commit secrets. Provide `.env.example` files only.

## 9. Quality bar (self-review before each Walkthrough)

- Would a dispatcher trust this screen during a live breakdown? Is the next action obvious?
- Would a passenger at a bus stop, one hand holding a bag, get the answer in under 5 seconds?
- Does the scheduling engine ever produce an assignment that `check_assignment` would reject? (It must not. Add a property-style test that generates random inputs and asserts this.)
- Does the app still behave sensibly when the WebSocket drops, the API is slow, or the data is empty?
- Is any code here something I'd be embarrassed to explain in a viva or code review?

## 10. Final deliverables

When M5 is complete, produce:

1. A working repo that runs with one command from a clean clone.
2. `README.md`: setup, demo credentials, architecture sketch, decisions, known limitations, and a requirement-coverage table (ID → status → where implemented).
3. `docs/api.md` and `docs/scheduling-algorithm.md`.
4. `docs/screenshots/` with the key screens at all three widths.
5. A final **Walkthrough** artifact summarising test results, acceptance checklist from spec §14 (each item ticked with evidence), and a list of anything deferred.

## 11. Start now

Begin with step 2 of section 2: read `SPEC.md`, then post the **Implementation Plan** and **Task List** artifacts. Do not write application code until I approve, or until you have only M0 scaffolding left to do.