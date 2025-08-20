import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any

from tray.tray_status import *
from tray.tray_mic import is_mic_server_up
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Servers-Routes")

# Define the router for system status-related routes
SystemStatusRouter = APIRouter()

# Route to check the systemd service status for novatray
@SystemStatusRouter.get("/tray-status")
async def get_novatray_service_status():
    logger.debug("HIT /tray-status route")
    status = service_status_check()
    logger.debug(f"Tray status: {status}")
    return status


# API route to serve system status as WebSocket
@SystemStatusRouter.websocket("/ws/system-status")
async def websocket_status(ws: WebSocket):
    await ws.accept()
    try:
        logger.debug("WebSocket connection established for system status.")
        while True:
            packet = gather_sensor_packet()
            await ws.send_text(packet.json())
            await asyncio.sleep(1)  # 1Hz update interval
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected")

# WebSocket route to send system info
@SystemStatusRouter.websocket("/ws/system-info")
async def websocket_system_info(ws: WebSocket):
    await ws.accept()
    try:
        logger.debug("WebSocket connection established for system info.")
        while True:
            info = get_system_info()
            await ws.send_text(json.dumps(info))  # Send the formatted JSON data
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected")

@SystemStatusRouter.get("/mic-server-status")
async def get_mic_server_status():
    if is_mic_server_up():
        logger.debug("Mic server is running.")
        return {"status": "running"}
    else:
        logger.debug("Mic server is stopped.")
        return {"status": "stopped"}

