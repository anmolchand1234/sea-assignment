import asyncio
import math
import random
import time
import logging
from datetime import datetime, timezone
from backend.app.realtime.ws import ws_manager
from backend.app.db.session import SessionLocal
from backend.app.models import Route, RoutePath, RouteStop, Stop, Vehicle, VehiclePosition

logger = logging.getLogger("wayline.simulator")

class TelemetrySimulator:
    def __init__(self):
        self.running = False
        self.task: asyncio.Task | None = None
        # State for active simulated vehicles: { vehicle_id: { route_id, polyline, progress_index, heading, speed, delay_s, occupancy } }
        self.simulated_vehicles = {}

    def init_routes(self):
        db = SessionLocal()
        try:
            routes = db.query(Route).filter(Route.is_active == True).all()
            vehicles = db.query(Vehicle).filter(Vehicle.status == "active").all()
            
            for i, v in enumerate(vehicles):
                if not routes:
                    break
                route = routes[i % len(routes)]
                path = db.query(RoutePath).filter(RoutePath.route_id == route.id).first()
                if path and path.polyline and len(path.polyline) >= 2:
                    self.simulated_vehicles[v.id] = {
                        "vehicle_id": v.id,
                        "fleet_no": v.fleet_no,
                        "route_id": route.id,
                        "route_code": route.short_name,
                        "color_hex": route.color_hex,
                        "polyline": path.polyline,
                        "progress": float(i * 3 % len(path.polyline)),
                        "speed_kmph": random.uniform(22.0, 36.0),
                        "heading": 45.0,
                        "delay_s": random.choice([0, 60, 120, 180]),
                        "occupancy": random.choice(["seats", "seats", "standing", "empty"]),
                    }
        finally:
            db.close()

    async def run(self):
        self.running = True
        self.init_routes()
        logger.info("Telemetry simulator started for %d vehicles", len(self.simulated_vehicles))

        while self.running:
            try:
                positions = []
                now_ts = int(time.time())

                for v_id, v in list(self.simulated_vehicles.items()):
                    poly = v["polyline"]
                    if not poly:
                        continue
                    
                    # Advance progress along polyline
                    v["progress"] = (v["progress"] + 0.15) % len(poly)
                    idx = int(v["progress"])
                    next_idx = (idx + 1) % len(poly)
                    frac = v["progress"] - idx

                    p1 = poly[idx]
                    p2 = poly[next_idx]

                    # Interpolate coordinate
                    lat = p1[0] + (p2[0] - p1[0]) * frac
                    lng = p1[1] + (p2[1] - p1[1]) * frac

                    # Compute heading
                    dlat = p2[0] - p1[0]
                    dlng = p2[1] - p1[1]
                    heading = (math.degrees(math.atan2(dlng, dlat)) + 360) % 360
                    v["heading"] = round(heading, 1)

                    # Random slight delay variation
                    if random.random() < 0.05:
                        v["delay_s"] = max(0, v["delay_s"] + random.choice([-30, 30, 60]))

                    positions.append({
                        "vehicle_id": v_id,
                        "fleet_no": v["fleet_no"],
                        "route_id": v["route_id"],
                        "route_code": v["route_code"],
                        "color_hex": v["color_hex"],
                        "lat": round(lat, 5),
                        "lng": round(lng, 5),
                        "heading": v["heading"],
                        "speed_kmph": round(v["speed_kmph"], 1),
                        "occupancy": v["occupancy"],
                        "delay_s": v["delay_s"],
                        "ts": now_ts,
                    })

                # Broadcast to connected WebSockets every 2 seconds (SPEC §7.3)
                if positions:
                    await ws_manager.broadcast_public({
                        "type": "positions",
                        "data": positions
                    })
                    await ws_manager.broadcast_ops({
                        "type": "positions",
                        "data": positions
                    })

                await asyncio.sleep(2.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Simulator loop error: %s", e)
                await asyncio.sleep(2.0)

    def start(self):
        if not self.running:
            self.task = asyncio.create_task(self.run())

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

simulator = TelemetrySimulator()
