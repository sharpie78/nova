import subprocess
import psutil
from fastapi import APIRouter
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Tray")

# Define the router for system status-related routes
server_status_router = APIRouter()

def service_status_check():
    """Checks the status of the novatray systemd service."""
    try:
        logger.debug("Checking status of novatray systemd service...")
        result = subprocess.run(
            ["systemctl", "--user", "status", "novatray.service"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        output = result.stdout
        active = "Active: active (running)" in output or "Active: activating" in output
        enabled = "Loaded: loaded" in output and "enabled;" in output

        logger.debug(f"Systemd service status checked: Active = {active}, Enabled = {enabled}")
        return {"active": active, "enabled": enabled}

    except Exception as e:
        logger.error(f"Error checking novatray service status: {e}")
        return {"active": False, "enabled": False}

# Route to check the systemd service status for novatray
@server_status_router.get("/tray-status")
async def get_novatray_service_status():
    logger.debug("HIT /tray-status route")
    status = service_status_check()
    logger.debug(f"Tray status: {status}")
    return status
