import os
import sys
import shutil
import subprocess
from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtCore import QTimer
from tray.tray_api import stop_api_server
from tray.tray_mic import stop_mic_server
from tray.tray_ui import close_webUI
from utils.logger import logger, setup_logger

setup_logger()
logger = logger.bind(name="Tray")

# Path to the systemd user directory
systemd_user_dir = os.path.expanduser("~/.config/systemd/user")

def delete_pycache_files():
    """Recursively delete all __pycache__ directories within the Nova directory."""
    # Get the path where the script is running from (tray_management.py)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Navigate up to the 'nova' directory from 'tray_management.py'
    nova_dir = os.path.abspath(os.path.join(script_dir, "../.."))  # Going up 2 levels to /mnt/nova

    logger.info(f"Deleting __pycache__ files in: {nova_dir}")

    # Walk through all subdirectories under 'nova_dir'
    for dirpath, dirnames, filenames in os.walk(nova_dir, topdown=False):
        if '__pycache__' in dirnames:
            pycache_dir = os.path.join(dirpath, '__pycache__')  # Construct full path to __pycache__
            shutil.rmtree(pycache_dir)  # Delete the __pycache__ directory and its contents

def on_tray_icon_activated(self, reason):
    cursor_pos = QtGui.QCursor.pos()
    offset = QtCore.QPoint(-125, -275)  # Same offset for both menus
    new_pos = cursor_pos + offset

    if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Context:
        self.right_click_menu.popup(new_pos)  # Show right-click menu at new position
    elif reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
        self.left_click_menu.popup(new_pos)  # Show left-click menu at new position

def quit_tray(app, api_server_action, mic_server_action, launch_ui_action, icons):
    """Quit the tray application."""
    stop_api_server(api_server_action, icons)  # Pass the necessary arguments
    logger.info("Quitting API server...")
    stop_mic_server(mic_server_action, icons)
    logger.info("Quitting mic server...")
    close_webUI(launch_ui_action, api_server_action, icons)
    delete_pycache_files()
    logger.info("Deleted pycache files...")
    app.quit()  # Quit the application

def restart_nova(app, api_server_action, enable_nova_action, restart_nova_action, mic_server_action, launch_ui_action, icons):
    """Restart the tray application using systemd."""
    logger.info("Stopping servers...")
    stop_api_server(api_server_action, icons)
    stop_mic_server(mic_server_action, icons)

    logger.info("Restarting Nova...")

    # First reload and restart the service
    subprocess.run(["systemctl", "--user", "daemon-reload"])  # Reload the systemd configuration
    subprocess.run(["systemctl", "--user", "restart", "novatray.service"])  # Restart the service

    # Now stop the Python tray instance (quit it after restarting the service)
    quit_tray(app, mic_server_action, api_server_action, launch_ui_action, icons)  # Pass arguments to quit_tray()

    logger.info("Nova restarted successfully.")

def toggle_nova(enable_nova_action, restart_nova_action, icons, app, api_server_action, launch_ui_action, mic_server_action):
    """Toggle between 'Enable Nova' and 'Disable Nova' (systemctl enable/disable, stop when disabling)."""
    # Check if the directory exists, and create it if not
    if not os.path.exists(systemd_user_dir):
        os.makedirs(systemd_user_dir)
        logger.info(f"Created missing directory: {systemd_user_dir}")

    try:
        # Check if the service is enabled
        result = subprocess.run(
            ["systemctl", "--user", "is-enabled", "novatray.service"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        subprocess.run(["cp", os.path.join(os.path.dirname(__file__), '..', '..', 'setup', 'novatray.service'),
                        os.path.join(systemd_user_dir, 'novatray.service')
                        ])

        if result.stdout.strip() == "enabled":
            # Service is enabled, so disable and stop it
            logger.info("Disabling and stopping Nova...")
            subprocess.run(["systemctl", "--user", "disable", "novatray.service"])  # Stop the service
            subprocess.run(["systemctl", "--user", "stop", "novatray.service"])  # Disable the service
            enable_nova_action.setText(f"{icons['nova']} Integrate Nova")
            restart_nova_action.setVisible(False)  # Hide restart action

        else:
            # Service is disabled, so enable it
            logger.info("Enabling Nova...")
            subprocess.run(["systemctl", "--user", "enable", "novatray.service"])  # Enable the service
            subprocess.run(["systemctl", "--user", "start", "novatray.service"])  # Start the service
            enable_nova_action.setText(f"{icons['quit']} Disable Nova")
            restart_nova_action.setVisible(True)  # Show restart action

            restart_nova(app, api_server_action, enable_nova_action, mic_server_action, restart_nova_action, launch_ui_action, icons)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking or controlling the service: {e}")
