import subprocess
import os
import sys
from threading import Thread
import time
from fastapi import APIRouter
from PyQt6.QtGui import QAction
from utils.logger import logger, setup_logger  # Assuming logger is configured in utils/logger.py
from setproctitle import setproctitle

# Set up the logger
setup_logger()  # Initialize logger with the desired configuration

# Bind the logger to the "audio" context
logger = logger.bind(name="Tray")

# Track the process globally
mic_server_process = None
monitor_mic_server_thread = None

mic_server_status_router = APIRouter()

@mic_server_status_router.get("/mic-server-status")
async def get_mic_server_status():
    """API route to check mic server status."""
    if mic_server_process and mic_server_process.poll() is None:
        logger.info("Mic server is running.")
        return {"status": "running"}
    else:
        logger.info("Mic server is stopped or not running.")
        return {"status": "stopped"}

def monitor_mic_server(mic_server_action, icons):
    """Starts a background thread to monitor the mic server process."""
    global monitor_mic_server_thread  # Declare global here
    if monitor_mic_server_thread is None:
        logger.debug("Starting mic server monitoring thread.")
        monitor_mic_server_thread = threading.Thread(target=monitor_mic_process, args=(mic_server_action, icons))
        monitor_mic_server_thread.daemon = True
        monitor_mic_server_thread.start()

def monitor_mic_process(mic_server_process, icons):
    """Periodically check the mic server's state."""
    while True:
        if mic_server_process and mic_server_process.poll() is None:
            logger.info("Mic server is running.")
            mic_server_action.setText(f"{icons['quit']} Stop Audio Server")
        else:
            logger.info("Mic server is stopped or not running.")
            mic_server_action.setText(f"{icons['audio']} Start Audio Server")
        time.sleep(2)  # Adjust sleep time if needed

def start_mic_server():
    global mic_server_process
    """Start the mic server using subprocess."""
    if mic_server_process is None:
        try:
            logger.debug("Attempting to start the mic server process.")
            # Start the mic server process
            mic_server_process = subprocess.Popen(
                [os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'python3.10'),
                 os.path.join(os.path.dirname(__file__), '..', 'servers', 'mic_server.py')],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            logger.info("Mic server started.")
        except Exception as e:
            logger.error(f"Error starting mic server: {e}")
            mic_server_process = None

def stop_mic_server(mic_server_action, icons):
    global mic_server_process
    """Stop the mic server if running."""
    if mic_server_process:
        try:
            logger.debug("Attempting to stop the mic server process.")
            mic_server_process.terminate()  # Gracefully stop the server
            mic_server_process.wait(timeout=5)  # Wait for it to stop
            logger.info("Mic server stopped.")
            mic_server_action.setText(f"{icons['audio']} Start Mic Server")  # Update tray action text

        except subprocess.TimeoutExpired:
            logger.warning("Mic server didn't stop in time, force killing.")
            mic_server_process.kill()  # Force kill if timeout occurs
            mic_server_process.wait()  # Ensure it terminates
            logger.debug("Mic server killed successfully.")
            mic_server_action.setText(f"{icons['audio']} Start Mic Server")  # Update tray action text

        except Exception as e:
            logger.error(f"Error stopping mic server: {e}")

        finally:
            mic_server_process = None  # Clear the process reference
    else:
        logger.warning("Mic server is not running.")

def toggle_mic_server(mic_server_action, icons):
    """Toggle between 'Start Audio Server' and 'Stop Audio Server'."""
    if mic_server_action.text() == f"{icons['audio']} Start Audio Server":
        logger.debug("Starting the mic server...")
        start_mic_server()
        mic_server_action.setText(f"{icons['quit']} Stop Audio Server")
    else:
        logger.debug("Stopping the mic server...")
        stop_mic_server(mic_server_action, icons)
        mic_server_action.setText(f"{icons['audio']} Start Audio Server")
