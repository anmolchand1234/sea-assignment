# Changelog

All notable changes to Wayline will be documented in this file.

## [Unreleased]

## [0.1.0] - 2026-10-28
### Milestone 0: Scaffolding, Design Primitives & Health Checks
- Established FastAPI backend structure with request ID correlation middleware, standard error envelopes, and `/health` & `/ready` endpoints.
- Configured React 18 + Vite + TypeScript (strict) frontend with Tailwind CSS and full `design/tokens.css` color token system.
- Implemented core transit UI primitives: `RouteChip`, `DepartureRow`, `LiveDot`, `DelayBadge`, `OccupancyLabel`, `ConnectionStatus`, `DataTable`, `Drawer`, `EmptyState`, and `InlineError`.
- Created interactive `/design` showcase route demonstrating all primitives in light and dark modes.
- Added `docker-compose.yml`, `Makefile`, and environment config templates.
