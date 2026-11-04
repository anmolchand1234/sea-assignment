from fastapi import APIRouter
from backend.app.api.v1.endpoints import auth, stops, routes, vehicles, drivers

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(stops.router)
api_router.include_router(routes.router)
api_router.include_router(vehicles.router)
api_router.include_router(drivers.router)
