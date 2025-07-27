import os
import sys
import time
import subprocess
import threading
import requests
from websocket import create_connection, WebSocketException
from fastapi import APIRouter
import logging
from utils.logger import logger, setup_logger
from servers.api_server import app
from tray.tray_servers import is_api_server_up

# Initialize log sinks
setup_logger()

# Bind separate loggers for routing to specific files
logger = logger.bind(name="Tray")

# Global variable to track the API server process
api_server_proc = None
monitor_api_server_thread = None


def monitor_api_server(api_server_action, icons):
    """Starts a background thread to monitor the API server process."""
    global monitor_api_server_thread  # Declare global here
    if monitor_api_server_thread is None:
        monitor_api_server_thread = threading.Thread(target=monitor_api_process, args=(api_server_action, icons))
        monitor_api_server_thread.daemon = True
        monitor_api_server_thread.start()
        logger.info("Started monitoring the API server process.")


def monitor_api_process(api_server_action, icons):
    """Monitors the status of the API server process in a background thread."""
    while True:
        if api_server_proc and api_server_proc.poll() is None:
            # API server is still running
            logger.debug("API server is running.")
            api_server_action.setText(f"{icons['quit']} Stop API Server")
        else:
            # API server is not running
            logger.debug("API server is not running.")
            api_server_action.setText(f"{icons['api']} Start API Server")

        # Refresh the tray menu to reflect the updated action text
        api_server_action.setContextMenu(api_server_action.right_click_menu)

        # Sleep for a bit before checking again (adjust the sleep time as needed)
        time.sleep(2)

def start_api_server(api_server_action, icons):
    """Starts the API server using Uvicorn."""
    global api_server_proc
    try:
        # Start the Uvicorn server
        api_server_proc = subprocess.Popen([
        "/mnt/nova/backend/venv/bin/uvicorn",  # Path to Uvicorn
        "servers.api_server:app",  # This should be the FastAPI app to run
        "--host", "127.0.0.1",
        "--port", "56969",
        "--timeout-graceful-shutdown", "5"  # Set the graceful shutdown timeout to 5 seconds
    ])

        # Give the server time to start
        time.sleep(2)

        # Ping the server to check if it's running
        if is_api_server_up():

            logger.debug("API server started successfully.")
            api_server_action.setText(f"{icons['quit']} Stop API Server")  # Update tray action text
        else:
            logger.critical("Failed to start API server: Server did not respond")
            api_server_action.setText(f"{icons['api']} Start API Server")  # Update tray action text

    except Exception as e:
        logger.critical(f"An error occurred while starting the API server: {e}")


def stop_api_server(api_server_action, icons):
    """Stops the API server if it's running."""
    global api_server_proc  # Ensure the global variable is used
    if api_server_proc:
        try:
            logger.debug("Stopping the API Server...")
            api_server_proc.terminate()  # Gracefully terminate the process

            # Wait for the process to terminate within a reasonable time (10 seconds)
            api_server_proc.wait(timeout=10)  # Increase timeout if necessary
            logger.debug("API Server stopped successfully.")
            api_server_action.setText(f"{icons['api']} Start API Server")  # Update tray action text

        except subprocess.TimeoutExpired:
            # If the process doesn't stop within the timeout, force kill it
            logger.warning("API Server did not stop in time, force killing...")
            api_server_proc.kill()  # Force kill the process
            api_server_proc.wait()  # Ensure it terminates
            logger.debug("API Server killed successfully.")
            api_server_action.setText(f"{icons['api']} Start API Server")  # Update tray action text

        except Exception as e:
            logger.critical(f"Error stopping the API server: {e}")
        finally:
            api_server_proc = None  # Clear the process reference
    else:
        logger.warning("API server is not running.")



def toggle_api_server(api_server_action, icons):
    """Toggles the state of the API server (start/stop)."""
    if api_server_action.text() == f"{icons['api']} Start API Server":
        logger.debug("Starting the API server...")
        start_api_server(api_server_action, icons)
    else:
        logger.debug("Stopping the API server...")
        stop_api_server(api_server_action, icons)


