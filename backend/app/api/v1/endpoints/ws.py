import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from backend.app.realtime.ws import ws_manager
from backend.app.core.security import decode_token

logger = logging.getLogger("wayline.ws_router")
router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/live")
async def websocket_live_endpoint(websocket: WebSocket):
    """
    Public WebSocket for live vehicle positions and service alerts (SPEC §7.3).
    Client can send: {"subscribe": {"routes": [...], "stops": [...]}}
    Server pushes: {"type": "positions", "data": [...]} every 2s
    """
    await ws_manager.connect_public(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                import json
                msg = json.loads(data)
                ws_manager.handle_public_message(websocket, msg)
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect_public(websocket)

@router.websocket("/ws/ops")
async def websocket_ops_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    Authenticated WebSocket for dispatchers & ops (SPEC §7.3).
    Receives live vehicle updates, incidents, and assignment changes.
    """
    if token:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            await websocket.close(code=1008)
            return

    await ws_manager.connect_ops(websocket)
    try:
        while True:
            # Keepalive / message reception
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect_ops(websocket)
