# editor_bridge_router.py
import asyncio, json, uuid
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi import Body, Query

EditorBridgeRouter = APIRouter(tags=["editor-bridge"])

# Active WebSocket clients keyed by client_id
clients: Dict[str, WebSocket] = {}
# Pending snapshot futures keyed by request id
awaiters: Dict[str, asyncio.Future] = {}

def _pick_client_id(requested: Optional[str]) -> str:
    """
    Resolve a usable client_id.
    - Treat None / "null" / "undefined" / "" as missing.
    - If exactly one client is connected, auto-select it.
    - If zero → 404.
    - If multiple → 409 with list so caller can choose.
    """
    req = (requested or "").strip()
    if req and req.lower() not in {"null", "none", "undefined"}:
        return req

    ids = list(clients.keys())
    if not ids:
        raise HTTPException(status_code=404, detail="No editor clients connected")
    if len(ids) == 1:
        return ids[0]
    raise HTTPException(status_code=409, detail={"error": "multiple_clients", "clients": ids})

@EditorBridgeRouter.websocket("/ws")
async def editor_ws(websocket: WebSocket, client_id: str = Query(...)):
    await websocket.accept()
    clients[client_id] = websocket
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            # Route snapshot replies back to the awaiting HTTP caller
            if msg.get("type") == "snapshot":
                req_id = msg.get("id")
                fut = awaiters.pop(req_id, None)
                if fut and not fut.done():
                    fut.set_result(msg)
    except WebSocketDisconnect:
        pass
    finally:
        clients.pop(client_id, None)

@EditorBridgeRouter.post("/agent/inject")
async def agent_inject(
    client_id: Optional[str] = Body(None),
    content: str = Body(""),
    mode: str = Body("insert"),         # insert | replace | append
    position: str = Body("cursor"),     # cursor | start | end
):
    cid = _pick_client_id(client_id)
    ws = clients.get(cid)
    if not ws:
        raise HTTPException(404, detail="Editor client not connected")
    msg = {"type": "inject", "content": content, "mode": mode, "position": position}
    try:
        await ws.send_text(json.dumps(msg))
    except RuntimeError:
        raise HTTPException(410, detail="Editor socket closed")
    return {"ok": True, "client_id": cid}

@EditorBridgeRouter.get("/agent/snapshot")
async def agent_snapshot(
    client_id: Optional[str] = Query(None),
    selection: bool = Query(False),
    timeout: float = Query(3.0, ge=0.5, le=30.0),
):
    cid = _pick_client_id(client_id)
    ws = clients.get(cid)
    if not ws:
        raise HTTPException(404, detail="Editor client not connected")
    req_id = str(uuid.uuid4())
    fut: asyncio.Future = asyncio.get_event_loop().create_future()
    awaiters[req_id] = fut
    try:
        await ws.send_text(json.dumps({"type": "snapshot_request", "id": req_id, "selection": selection}))
    except RuntimeError:
        awaiters.pop(req_id, None)
        raise HTTPException(410, detail="Editor socket closed")
    try:
        msg = await asyncio.wait_for(fut, timeout)
    except asyncio.TimeoutError:
        awaiters.pop(req_id, None)
        raise HTTPException(504, detail="Editor snapshot timeout")

    return {
        "client_id": cid,
        "path": msg.get("path"),
        "content": msg.get("content"),
        "selection": msg.get("selection"),
    }

@EditorBridgeRouter.get("/clients")
def list_clients():
    return {"clients": list(clients.keys())}
