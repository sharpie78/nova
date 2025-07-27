from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import psutil
import subprocess
from typing import List, Dict, Any
import asyncio
import re
import json
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Servers-Routes")

# Data model for system status
class SensorPacket(BaseModel):
    cpu_usage: float
    cpu_temp: float | None
    ram_used_gb: float
    ram_total_gb: float
    gpus: List[Dict[str, Any]]  # temperature, utilization, mem_used, mem_total

# Utility to gather GPU stats
def get_gpu_stats() -> List[Dict[str, Any]]:
    """Return list of GPU stats using `nvidia-smi` (empty list if unavailable)."""
    try:
        logger.debug("Attempting to fetch GPU stats using nvidia-smi.")
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=temperature.gpu,utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.warning("nvidia-smi command failed or not found. Returning empty GPU stats.")
        return []

    gpus: List[Dict[str, Any]] = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        temp, util, mem_used, mem_total = [x.strip() for x in line.split(',')]
        gpus.append({
            "temperature": int(temp),
            "utilization": int(util),
            "mem_used": int(mem_used),
            "mem_total": int(mem_total),
        })
    logger.debug(f"GPU stats: {gpus}")
    return gpus

# Function to gather system status data
def gather_sensor_packet() -> SensorPacket:
    logger.debug("Gathering system status data...")
    ram = psutil.virtual_memory()
    cpu_usage = psutil.cpu_percent(interval=0.1)

    # CPU temp (Linux example, may vary)
    cpu_temp_val: float | None = None
    try:
        temps = psutil.sensors_temperatures()
        if "k10temp" in temps:
            for entry in temps["k10temp"]:
                if entry.label == "Tctl":
                    cpu_temp_val = float(entry.current)
                    break
    except Exception as e:
        logger.error(f"Error retrieving CPU temperature: {e}")

    # Correct RAM rounding
    ram_used_gb = round(ram.used / (1024 ** 3), 2)  # Convert bytes to GB and round
    ram_total_gb = round(ram.total / (1024 ** 3), 2)  # Convert bytes to GB and round

    # Construct the packet with rounded RAM values
    packet = SensorPacket(
        cpu_usage=cpu_usage,
        cpu_temp=cpu_temp_val,
        ram_used_gb=ram_used_gb,  # Using rounded values here
        ram_total_gb=ram_total_gb,  # Using rounded values here
        gpus=get_gpu_stats(),
    )

    logger.debug(f"System status packet: {packet}")
    return packet

# Function to get System info
def get_system_info():
    logger.debug("Gathering system information using neofetch...")
    result = subprocess.run("neofetch | sed 's/\\x1b\\[[0-9;]*m//g' | grep -E 'OS:|Kernel:|Uptime:|Shell:|Resolution:|DE:|CPU:|GPU:|Memory:'",
                            shell=True, capture_output=True, text=True)

    # Remove only the [43C cursor move escape sequence
    cleaned_output = re.sub(r'\x1b\[43C', '', result.stdout)

    # Split the result by lines and process each line
    output_lines = cleaned_output.splitlines()

    system_info = {}

    # Initialize list for GPUs
    gpus = []

    # Process each line and format the system info
    for line in output_lines:
        if "OS" in line:
            system_info["OS"] = line.split(":", 1)[1].strip()
        elif "Kernel" in line:
            system_info["Kernel"] = line.split(":", 1)[1].strip()
        elif "Uptime" in line:
            system_info["Uptime"] = line.split(":", 1)[1].strip()
        elif "Shell" in line:
            system_info["Shell"] = line.split(":", 1)[1].strip()
        elif "Resolution" in line:
            system_info["Monitors"] = line.split(":", 1)[1].strip()
        elif "DE" in line:
            system_info["DE"] = line.split(":", 1)[1].strip()
        elif "CPU" in line:
            system_info["CPU"] = line.split(":", 1)[1].strip()
        elif "GPU" in line:
            # Only add the GPU name to the list without "GPU:" prepending
            gpus.append(line.split("GPU:")[1].strip() if "GPU:" in line else line.split(":")[1].strip())
        elif "Memory" in line:
            match = re.search(r'/ (\d+)(MiB)', line)
            if match:
                total_mib = int(match.group(1))  # Extract the total MiB value
                total_gib = total_mib / 1024  # Convert to GiB
                system_info["Memory"] = f"{total_gib:.2f} GiB"

    # If multiple GPUs are found, include them as a list in the system info
    if gpus:
        system_info["GPU"] = "<br>".join(gpus)  # Join GPUs with <br> for line breaks

    logger.debug(f"System info: {json.dumps(system_info)}")
    return system_info  # Return the formatted system info as a JSON object


# Define the router for system status-related routes
SystemStatusRouter = APIRouter()

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
        logger.info("WebSocket disconnected")

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
        logger.info("WebSocket disconnected")
