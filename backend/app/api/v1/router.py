from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    auth, stops, routes, vehicles, drivers, public, ops, scheduling, driver_portal, reports
)

api_router = APIRouter()
api_router.include_router(public.router)
api_router.include_router(auth.router)
api_router.include_router(stops.router)
api_router.include_router(routes.router)
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
api_router.include_router(ops.router)
api_router.include_router(scheduling.router)
api_router.include_router(driver_portal.router)
api_router.include_router(reports.router)
