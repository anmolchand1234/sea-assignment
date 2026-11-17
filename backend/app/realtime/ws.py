import asyncio
import json
import logging
from typing import Dict, Set, List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("wayline.realtime")

class WebSocketManager:
    def __init__(self):
        # Public connections: set of websockets
        self.public_connections: Set[WebSocket] = set()
        # Ops connections: set of websockets
        self.ops_connections: Set[WebSocket] = set()
        # Subscriptions per public client: ws -> { "routes": set(), "stops": set() }
        self.subscriptions: Dict[WebSocket, Dict[str, Set[str]]] = {}

    async def connect_public(self, websocket: WebSocket):
        await websocket.accept()
        self.public_connections.add(websocket)
        self.subscriptions[websocket] = {"routes": set(), "stops": set()}

    def disconnect_public(self, websocket: WebSocket):
        self.public_connections.discard(websocket)
        self.subscriptions.pop(websocket, None)

    async def connect_ops(self, websocket: WebSocket):
        await websocket.accept()
        self.ops_connections.add(websocket)

    def disconnect_ops(self, websocket: WebSocket):
        self.ops_connections.discard(websocket)

    def handle_public_message(self, websocket: WebSocket, message: dict):
        # Client sends: { "subscribe": { "routes": [...], "stops": [...] } }
        sub = message.get("subscribe", {})
        if websocket in self.subscriptions:
            if "routes" in sub:
                self.subscriptions[websocket]["routes"] = set(sub["routes"])
            if "stops" in sub:
                self.subscriptions[websocket]["stops"] = set(sub["stops"])

    async def broadcast_public(self, message: dict):
        dead_sockets = []
        payload = json.dumps(message)
        for ws in self.public_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.disconnect_public(ws)

    async def broadcast_ops(self, message: dict):
        dead_sockets = []
        payload = json.dumps(message)
        for ws in self.ops_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            self.disconnect_ops(ws)

ws_manager = WebSocketManager()
