import subprocess
import os
import sys
import time
import threading
import requests
import signal
from websocket import create_connection, WebSocketException
from fastapi import APIRouter
from tray.tray_api import start_api_server
from tray.tray_servers import is_api_server_up
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Tray")

webUI_pid = None
web_ui_open = False  # Track WebUI state (open/closed)

def monitor_webUI(api_server_action, icons, launch_ui_action):
    """Monitors the Web UI process in a background thread."""
    if not hasattr(monitor_webUI, "monitor_thread") or monitor_webUI.monitor_thread is None:
        logger.debug("Starting WebUI monitoring thread.")
        monitor_webUI.monitor_thread = threading.Thread(
            target=_monitor_webUI_process,
            args=(api_server_action, icons, launch_ui_action)
        )
        monitor_webUI.monitor_thread.daemon = True
        monitor_webUI.monitor_thread.start()

def _monitor_webUI_process(api_server_action, icons, launch_ui_action):
    """Monitors the status of the Web UI process in a background thread."""
    global webUI_pid, web_ui_open
    logger.debug("Checking WebUI process status.")
    while True:
        result = subprocess.run(['wmctrl', '-l', '-x'], capture_output=True, text=True)
        if result.returncode == 0:
            current_state = False
            for line in result.stdout.splitlines():
                if 'nova-ui' in line:
                    current_state = True
                    break

            if current_state != web_ui_open:  # Log only if the state changes
                if current_state:
                    logger.debug("WebUI is currently open.")
                    launch_ui_action.setText(f"{icons['quit']} Close UI")
                else:
                    logger.debug("WebUI is not open.")
                    launch_ui_action.setText(f"{icons['ui']} Launch UI")
                web_ui_open = current_state
        else:
            logger.error("Failed to fetch window list.")
        time.sleep(1)  # Adjust sleep time if necessary

def open_webUI(api_server_action, launch_ui_action, icons):
    """Open the Web UI using Tauri."""
    global webUI_pid
    try:
        logger.debug("Attempting to open WebUI...")
        if not is_api_server_up():
            logger.debug("API server is not running. Starting the server.")
            start_api_server(api_server_action, icons)
        else:
            logger.debug("API server is already running.")

        process = subprocess.Popen(["npx", "tauri", "dev"], cwd="/mnt/nova/nova-UI")
        webUI_pid = process.pid

        with open("/tmp/webUI_pid.txt", "w") as file:
            file.write(str(webUI_pid))

        logger.debug(f"Nova Web UI launched with PID {webUI_pid}")

    except Exception as e:
        logger.critical(f"Failed to launch Nova-WebUI: {e}")

def close_webUI(launch_ui_action, api_server_action, icons):
    """Close the Web UI by terminating the Tauri process."""
    global webUI_pid
    try:
        logger.debug("Attempting to close UI...")
        result = subprocess.run(['wmctrl', '-l', '-x'], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'nova-ui' in line:
                    window_id = line.split()[0]
                    subprocess.run(['wmctrl', '-i', '-c', window_id])
                    if webUI_pid:
                        os.kill(webUI_pid, signal.SIGTERM)
                    webUI_pid = None
                    logger.debug(f"Closed WebUI with window ID {window_id} and PID {webUI_pid}")
                    break
            else:
                logger.debug("No UI window found with title 'nova-ui'.")
        else:
            logger.error("Failed to fetch window list.")
    except Exception as e:
        logger.error(f"Error closing WebUI window: {e}")

def toggle_ui(launch_ui_action, icons, api_server_action):
    try:
        logger.debug("Toggling WebUI state...")
        result = subprocess.run(['wmctrl', '-l', '-x'], capture_output=True, text=True)
        web_ui_open = False
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if 'nova-ui' in line:
                    web_ui_open = True
                    break

        if web_ui_open:
            logger.debug("WebUI is currently running. Closing it now.")
            close_webUI(launch_ui_action, api_server_action, icons)
            launch_ui_action.setText(f"{icons['ui']} Launch UI")
        else:
            logger.debug("WebUI is not currently open. Opening it now.")
            open_webUI(api_server_action, launch_ui_action, icons)
            launch_ui_action.setText(f"{icons['quit']} Close UI")

    except Exception as e:
        logger.error(f"Error toggling WebUI: {e}")
