#!/mnt/nova/backend/venv/bin/python3.10

import os
import sys
sys.path.append(os.path.abspath('/mnt/nova/backend'))
import requests  # if not already imported
import subprocess
from PyQt6 import QtWidgets, QtGui, QtCore
from setproctitle import setproctitle

from tray.tray_management import on_tray_icon_activated, quit_tray, toggle_nova, restart_nova
#from tray.tray_tts import *
from tray.tray_mic import *
from tray.tray_api import *
from tray.tray_voice import toggle_voice
from tray.tray_ui import *
from tray.tray_status import service_status_check



setproctitle("nova_tray")

class NovaTrayManager(QtWidgets.QSystemTrayIcon):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.api_server_proc = None  # Tracks the API server process
        self.setToolTip("Nova Tray Manager")

        # Tray Icon (Using QIcon for tray)
        self.icons = {
            "tray": QtGui.QIcon('assets/icons/novafavicon.png'),  # Custom tray icon (image file)
            "quit": "❌",  # Quit icon (using cross mark emoji)
            "api": "🌐",  # API server icon (using globe emoji)
            "audio": "🎵",  # Audio server icon (using musical note emoji)
            "restart": "🔄",  # Restart icon (using refresh emoji)
            "enable": "✅",  # Enable icon (using check mark emoji)
            "disable": "❌",  # Disable icon (using cross mark emoji)
            "stop_all": "⏹️",  # Stop All Servers icon (using stop button emoji)
            "start_all": "▶️",  # Play All Servers icon (using play button emoji)
            "ui": "💻",  # UI icon (using laptop emoji)
            "voice": "🎤",  # Voice icon (using microphone emoji)
            "nova": "🌟"  # Enable Nova icon (using star emoji)
        }

        self.setIcon(self.icons["tray"])  # Set tray icon using QIcon (image file)
        self.setVisible(True)

        # Shared menu style function
        def apply_menu_style(menu):
            menu.setStyleSheet("""
                QMenu {
                    font-size: 16pt;
                    padding: 8px 8px;  /* Padding (top/bottom, left/right) */
                }
                QMenu::item {
                    text-align: left;  /* Ensure text is aligned to the left */
                    height: 40px;  /* Set a fixed height for the items */
                    padding-left: 10px;  /* Add padding to ensure the text doesn't touch the left edge */
                }
                QMenu::item:selected {
                    background-color: #5A5A5A; /* Highlight selected item */
                }
                QMenu::separator {
                    height: 3px;  /* Increase height for thicker separator */
                    background-color: #B0B0B0;  /* Grey color for separator */
                    margin: 8px 0;  /* Margin around separator for spacing */
                }
            """)

        # Create both left-click and right-click menus
        self.left_click_menu = QtWidgets.QMenu()
        apply_menu_style(self.left_click_menu)  # Apply shared style
        self.left_click_menu.setFixedSize(250, 400)
        self.left_click_menu.move(-125, -525)

        self.right_click_menu = QtWidgets.QMenu()
        apply_menu_style(self.right_click_menu)  # Apply shared style
        self.right_click_menu.setFixedSize(250, 400)
        self.right_click_menu.move(-125, -525)

        # Common actions

        self.launch_ui_action = QtGui.QAction(f"{self.icons['ui']} Launch UI")
        self.launch_ui_action.triggered.connect(lambda: toggle_ui(self.launch_ui_action, self.icons, self.api_server_action))

        self.left_click_menu.addSeparator()
        self.right_click_menu.addSeparator()

        self.enable_voice_action = QtGui.QAction(f"{self.icons['voice']} Enable Voice")
        self.enable_voice_action.triggered.connect(lambda: toggle_voice(self.enable_voice_action, self.icons))

        self.left_click_menu.addSeparator()
        self.right_click_menu.addSeparator()

        self.enable_nova_action = QtGui.QAction(f"{self.icons['nova']} Integrate Nova")
        self.restart_nova_action = QtGui.QAction(f"{self.icons['restart']} Restart service")
        self.restart_nova_action.triggered.connect(lambda: restart_nova(self.app, self.api_server_action, self.enable_nova_action, self.restart_nova_action, self.mic_server_action, self.launch_ui_action, self.icons)) # self.tts_server_action))
        self.restart_nova_action.setVisible(False)
        try:
            resp = requests.get("http://127.0.0.1:56969/tray-status", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("enabled"):
                    self.enable_nova_action.setText(f"{self.icons['disable']} Disable Nova")
                    self.restart_nova_action.setVisible(True)
        except Exception as e:
            print(f"Failed to check tray status: {e}")
            status = service_status_check()
            if status["enabled"]:
                self.enable_nova_action.setText(f"{self.icons['disable']} Disable Nova")
                self.restart_nova_action.setVisible(True)

        self.enable_nova_action.triggered.connect(lambda: toggle_nova(self.enable_nova_action, self.restart_nova_action, self.icons, self.app, self.api_server_action, self.launch_ui_action, self.mic_server_action)) # , self.tts_server_action))

        self.left_click_menu.addSeparator()
        self.right_click_menu.addSeparator()

        self.api_server_action = QtGui.QAction(f"{self.icons['api']} Start API Server")
        self.api_server_action.triggered.connect(lambda: toggle_api_server(self.api_server_action, self.icons))

        self.mic_server_action = QtGui.QAction(f"{self.icons['audio']} Start Mic Server")
        self.mic_server_action.triggered.connect(lambda: toggle_mic_server(self.mic_server_action, self.icons))

        #self.tts_server_action = QtGui.QAction(f"{self.icons['audio']} Start TTS Server")
        #self.tts_server_action.triggered.connect(lambda: toggle_tts_server(self.tts_server_action, self.icons))

        self.left_click_menu.addSeparator()
        self.right_click_menu.addSeparator()

        self.stop_service_action = QtGui.QAction(f"{self.icons['quit']} Quit Nova")
        self.stop_service_action.triggered.connect(lambda: quit_tray(self.app, self.api_server_action, self.mic_server_action, self.launch_ui_action, self.icons))


        # Add actions to both menus
        for action in [self.launch_ui_action,
                       self.left_click_menu.addSeparator(),
                       self.right_click_menu.addSeparator(),
                       self.enable_voice_action,
                       self.left_click_menu.addSeparator(),
                       self.right_click_menu.addSeparator(),
                       self.enable_nova_action,
                       self.restart_nova_action,
                       self.left_click_menu.addSeparator(),
                       self.right_click_menu.addSeparator(),
                       self.api_server_action,
                       self.mic_server_action,
                       self.left_click_menu.addSeparator(),
                       self.right_click_menu.addSeparator(),
                       self.stop_service_action]: # self.tts_server_action,
            self.left_click_menu.addAction(action)
            self.right_click_menu.addAction(action)

        # Add separators where needed
        self.left_click_menu.addSeparator()
        self.right_click_menu.addSeparator()

        if is_api_server_up():
            self.api_server_action.setText(f"{self.icons['quit']} Stop API Server")
        else:
            self.api_server_action.setText(f"{self.icons['api']} Start API Server")

        if mic_server_process and mic_server_process.poll() is None:
            self.mic_server_action.setText(f"{self.icons['quit']} Stop Audio Server")
        else:
            self.mic_server_action.setText(f"{self.icons['audio']} Start Audio Server")

        # Set WebUI action text based on window state
        result = subprocess.run(['wmctrl', '-l', '-x'], capture_output=True, text=True)
        if result.returncode == 0 and 'nova-webui' in result.stdout:
            self.launch_ui_action.setText(f"{self.icons['quit']} Close UI")
        else:
            self.launch_ui_action.setText(f"{self.icons['ui']} Launch UI")

        # Start monitoring the WebUI window
        monitor_webUI(self.api_server_action, self.icons, self.launch_ui_action)


        #if tts_server_process and tts_server_process.poll() is None:
            #self.tts_server_action.setText(f"{self.icons['quit']} Stop TTS Server")
        #else:
            #self.tts_server_action.setText(f"{self.icons['audio']} Start TTS Server")

        # Handle tray icon click actions (left-click)
        self.activated.connect(lambda reason: on_tray_icon_activated(self, reason))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    tray = NovaTrayManager(app)
    sys.exit(app.exec())
